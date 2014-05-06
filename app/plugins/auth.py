# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import os
import hashlib

from google.appengine.api import blobstore

from app import ndb, settings, memcache, util
from app.srv import event, blob
from app.srv.setup import Configuration
from app.lib.attribute_manipulator import set_attr, get_attr
from app.lib import oauth2


def new_session(entity):
  from app.srv.auth import Session
  session_ids = [session.session_id for session in entity.sessions]
  while True:
    session_id = hashlib.md5(util.random_chars(30)).hexdigest()
    if session_id not in session_ids:
      break
  session = Session(session_id=session_id)
  entity.sessions.append(session)
  return session

def has_identity(entity, identity_id):
  for identity in entity.identities:
    if identity.identity == identity_id:
      return identity
  return False


class OAuth2Error(Exception):
  
  def __init__(self, error):
    self.message = {'oauth2_error': error}


class UserLoginPrepare(event.Plugin):
  
  def run(self, context):
    from app.srv.auth import User
    context.entities['0'] = User.current_user()
    context.user = User.current_user()


class UserLoginOAuth(event.Plugin):
  
  def run(self, context):
    from app.srv.auth import User
    login_method = context.input.get('login_method')
    error = context.input.get('error')
    code = context.input.get('code')
    oauth2_cfg = settings.LOGIN_METHODS[login_method]['oauth2']
    client = oauth2.Client(**oauth2_cfg)
    context.output['authorization_url'] = client.get_authorization_code_uri()
    urls = {}
    for urls_login_method, cfg in settings.LOGIN_METHODS.items():
      urls_oauth2_cfg = cfg['oauth2']
      urls_client = oauth2.Client(**urls_oauth2_cfg)
      urls[urls_oauth2_cfg['type']] = urls_client.get_authorization_code_uri()
    context.output['authorization_urls'] = urls
    if error:
      raise OAuth2Error('rejected_account_access')
    if code:
      client.get_token(code)
      if not client.access_token:
        raise OAuth2Error('failed_access_token')
      userinfo = oauth2_cfg['userinfo']
      info = client.resource_request(url=userinfo)
      if info and 'email' in info:
        identity = oauth2_cfg['type']
        context.identity_id = '%s-%s' % (info['id'], identity)
        context.email = info['email']
        user = User.query(User.identities.identity == context.identity_id).get()
        if not user:
          user = User.query(User.emails == context.email).get()
        if user:
          context.entities['0'] = user
          context.user = user


class UserLoginUpdate(event.Plugin):
  
  def run(self, context):
    if hasattr(context, 'identity_id'):
      from app.srv.auth import User, Identity
      entity = context.entities['0']
      if entity._is_guest:
        entity = User()
        entity.emails.append(context.email)
        entity.identities.append(Identity(identity=context.identity_id, email=context.email, primary=True))
        entity.state = 'active'
        session = new_session(entity)
        entity.put()
      else:
        if context.email not in entity.emails:
          entity.emails.append(context.email)
        used_identity = has_identity(entity, context.identity_id)
        if not used_identity:
          entity.append(Identity(identity=context.identity_id, email=context.email, primary=False))
        else:
          used_identity.associated = True
          if used_identity.email != context.email:
            used_identity.email = context.email
        session = new_session(entity)
        entity.put()
      User.set_current_user(entity, session)
      context.entities['0'] = entity
      context.user = entity
      context.session = session
      context.log_entities.append((entity, {'ip_address' : context.ip_address}))


class UserLoginOutput(event.Plugin):
  
  def run(self, context):
    context.output['entity'] = context.entities['0']
    if not context.entities['0']._is_guest:
      context.output['authorization_code'] = '%s|%s' % (context.entities['0'].key.urlsafe(), context.session.session_id)


class UserIPAddress(event.Plugin):
  
  def run(self, context):
    context.ip_address = os.environ['REMOTE_ADDR']


class UserLogoutOutput(event.Plugin):
  
  def run(self, context):
    context.entities['0'].set_current_user(None, None)
    context.output['entity'] = context.entities['0'].current_user()


class UserReadDomains(event.Plugin):
  
  def run(self, context):
    context.domains = []
    context.domain_users = []
    if context.user.domains:
      
      @ndb.tasklet
      def async(domain):
        if domain:
          # Rule engine cannot run in tasklets because the context.rule.entity gets in wrong places for some reason... which
          # also causes rule engine to not work properly with _action_permissions, this i could not debug because it is impossible to determine what is going on in iterator
          domain_user_key = ndb.Key('8', context.user.key_id_str, namespace=domain.key_namespace)
          domain_user = yield domain_user_key.get_async()
        raise ndb.Return(domain_user)
      
      @ndb.tasklet
      def helper(domains):
        domain_users = yield map(async, domains)
        raise ndb.Return(domain_users)
      
      context.domains = ndb.get_multi(context.user.domains)
      context.domain_users = helper(context.domains).get_result()


class UserUpdate(event.Plugin):
  
  def run(self, context):
    primary_email = context.input.get('primary_email')
    disassociate = context.input.get('disassociate')
    for identity in context.values['0'].identities:
      if disassociate:
        if identity.identity in disassociate:
          identity.associated = False
      if primary_email:
        identity.primary = False
        if identity.email == primary_email:
          identity.primary = True
          identity.associated = True


class UserSudo(event.Plugin):
  
  def run(self, context):
    if context.entities['0']._field_permissions['state']['writable'] and context.values['0'].state == 'suspended':
      context.values['0'].sessions = []


class DomainCreate(event.Plugin):
  
  def run(self, context):
    config_input = context.input.copy()
    domain_logo = config_input.get('domain_logo')
    blob.Manager.used_blobs(domain_logo.image)
    config_input['domain_primary_contact'] = context.user.key
    config = Configuration(parent=context.user.key, configuration_input=config_input, setup='setup_domain', state='active')
    config.put()
    context.entities[config.get_kind()] = config
    
class DomainRead(event.Plugin):
  
  def run(self, context):
    # @todo Async operations effectively require two separate plugins
    # that will be separated by intermediate plugins, in order to prove to be useful!
    # This separation for async ops has to be decided yet!
    # Right now async is eliminated!
    #primary_contact = context.entities['6'].primary_contact.get_async()
    #primary_contact = primary_contact.get_result()
    primary_contact = context.entities['6'].primary_contact.get()
    context.entities['6']._primary_contact_email = primary_contact._primary_email


class DomainPrepare(event.Plugin):
  
  def run(self, context):
    context.output['upload_url'] = blobstore.create_upload_url(context.input.get('upload_url'), gs_bucket_name=settings.COMPANY_LOGO_BUCKET)


class DomainSearch(event.Plugin):
  
  def run(self, context):
    @ndb.tasklet
    def async(entity):
      user = yield entity.primary_contact.get_async()
      entity._primary_contact_email = user._primary_email
      raise ndb.Return(entity)
    
    @ndb.tasklet
    def mapper(entities):
      entities = yield map(async, entities)
      raise ndb.Return(entities)
    
    context.entities = mapper(context.entities).get_result()
