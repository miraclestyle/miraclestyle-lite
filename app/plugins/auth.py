# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import os
import hashlib

from app import ndb, util
from app.tools import oauth2


def primary_contact_validator(prop, value):
  domain_user = value.get()
  role_ids = [role.id() for role in domain_user.roles]
  if 'admin' in role_ids:
    return value
  else:
    raise ndb.PropertyError('invalid_domain_user')


def new_session(model, entity):
  Session = model
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


class UserLoginOAuth(ndb.BaseModel):
  
  login_methods = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    context._user = context.model.current_user()
    context.user = context.model.current_user()
    kwargs = {'user': context.user, 'action': context.action}
    rule_prepare(context._user, True, False, **kwargs)
    rule_exec(context._user, context.action)
    login_method = context.input.get('login_method')
    error = context.input.get('error')
    code = context.input.get('code')
    oauth2_cfg = self.login_methods[login_method]['oauth2']
    client = oauth2.Client(**oauth2_cfg)
    context.output['authorization_url'] = client.get_authorization_code_uri()
    urls = {}
    for urls_login_method, cfg in self.login_methods.items():
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
        context._identity_id = '%s-%s' % (info['id'], identity)
        context._email = info['email']
        user = context.model.query(User.identities.identity == context._identity_id).get()
        if not user:
          user = context.model.query(User.emails == context._email).get()
        if user:
          context._user = user
          context.user = user


class UserLoginUpdate(ndb.BaseModel):
  
  def run(self, context):
    if context._identity_id != None:
      User = context.models['0']
      Identity = context.models['64']
      Session = context.models['70']
      entity = context._user
      if entity._is_guest:
        entity = User()
        entity.emails.append(context._email)
        entity.identities.append(Identity(identity=context._identity_id, email=context._email, primary=True))
        entity.state = 'active'
        session = new_session(Session, entity)
        entity._use_rule_engine = False
        entity.write({'agent': entity.key, 'action': context.action.key, 'ip_address': entity.ip_address})
      else:
        if context._email not in entity.emails:
          entity.emails.append(context._email)
        used_identity = has_identity(entity, context._identity_id)
        if not used_identity:
          entity.append(Identity(identity=context._identity_id, email=context._email, primary=False))
        else:
          used_identity.associated = True
          if used_identity.email != context._email:
            used_identity.email = context._email
        session = new_session(Session, entity)
        entity.write({'agent': entity.key, 'action': context.action.key, 'ip_address': entity.ip_address})
      User.set_current_user(entity, session)
      context._user = entity
      context.user = entity
      context._session = session


class UserLoginOutput(ndb.BaseModel):
  
  def run(self, context):
    context.output['entity'] = context.entities['0']
    if not context.entities['0']._is_guest:
      context.output['authorization_code'] = '%s|%s' % (context.entities['0'].key.urlsafe(), context.tmp['session'].session_id)


class UserLogoutOutput(ndb.BaseModel):
  
  def run(self, context):
    context.entities['0'].set_current_user(None, None)
    context.output['entity'] = context.entities['0'].current_user()


# @todo To be removed, once we figure out how to virtualize properties.
class UserReadDomains(ndb.BaseModel):
  
  def run(self, context):
    context.tmp['domains'] = []
    context.tmp['domain_users'] = []
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
      
      context.tmp['domains'] = ndb.get_multi(context.user.domains)
      context.tmp['domain_users'] = helper(context.tmp['domains']).get_result()


class UserUpdate(ndb.BaseModel):
  
  def run(self, context):
    primary_email = context.input.get('primary_email')
    disassociate = context.input.get('disassociate')
    for identity in context.entities['0'].identities:
      if disassociate:
        if identity.identity in disassociate:
          identity.associated = False
      if primary_email:
        identity.primary = False
        if identity.email == primary_email:
          identity.primary = True
          identity.associated = True


class DomainCreate(ndb.BaseModel):
  
  def run(self, context):
    config_input = context.input.copy()
    Configuration = context.models['57']
    config = Configuration(parent=context.user.key, configuration_input=config_input, setup='setup_domain', state='active')
    config.put()
    context.entities[config.get_kind()] = config
