# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib

from app import orm
from app.tools import oauth2
from app.tools.base import *
from app.util import *


def primary_contact_validator(prop, value):
  domain_user = value.get()
  role_ids = [role.id() for role in domain_user.roles]
  if 'admin' in role_ids:
    return value
  else:
    raise orm.PropertyError('invalid_domain_user')


def new_session(model, entity):
  Session = model
  session_ids = [session.session_id for session in entity.sessions.value]
  while True:
    session_id = hashlib.md5(random_chars(30)).hexdigest()
    if session_id not in session_ids:
      break
  session = Session(session_id=session_id)
  entity.sessions.value.append(session)
  return session


def has_identity(entity, identity_id):
  for identity in entity.identities.value:
    if identity.identity == identity_id:
      return identity
  return False


class OAuth2Error(Exception):
  
  def __init__(self, error):
    self.message = {'oauth2_error': error}


class UserLoginInit(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    login_methods = self.cfg.get('methods', {})
    context._user = context.model.current_user()
    context.user = context.model.current_user()
    kwargs = {'user': context.user, 'action': context.action}
    rule_prepare(context._user, True, False, **kwargs)
    rule_exec(context._user, context.action)
    login_method = context.input.get('login_method')
    error = context.input.get('error')
    code = context.input.get('code')
    oauth2_cfg = login_methods[login_method]['oauth2']
    client = oauth2.Client(**oauth2_cfg)
    context.output['authorization_url'] = client.get_authorization_code_uri()
    urls = {}
    for urls_login_method, cfg in login_methods.items():
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
        user = context.model.query(context.model.identities.identity == context._identity_id).get()
        if not user:
          user = context.model.query(context.model.emails == context._email).get()
        if user:
          context._user = user
          context.user = user
    kwargs = {'user': context.user, 'action': context.action}
    rule_prepare(context._user, True, False, **kwargs)
    rule_exec(context._user, context.action)


class UserLoginWrite(orm.BaseModel):
  
  def run(self, context):
    if hasattr(context, '_identity_id') and context._identity_id != None:
      User = context.models['0']
      Identity = context.models['64']
      Session = context.models['70']
      entity = context._user
      if entity._is_guest:
        entity = context.model()
        entity.emails.append(context._email)
        entity.identities.value.append(Identity(identity=context._identity_id, email=context._email, primary=True))
        entity.state = 'active'
        session = new_session(Session, entity)
        # Right now this is the only way to record this entity.
        entity._use_rule_engine = False
        entity.write({})
        entity._record_arguments = {'agent': entity.key, 'action': context.action.key, 'ip_address': entity.ip_address}
        entity.record()
      else:
        if context._email not in entity.emails:
          entity.emails.append(context._email)
        used_identity = has_identity(entity, context._identity_id)
        if not used_identity:
          entity.identities.value.append(Identity(identity=context._identity_id, email=context._email, primary=False))
        else:
          used_identity.associated = True
          if used_identity.email != context._email:
            used_identity.email = context._email
        session = new_session(Session, entity)
        entity.write({'agent': entity.key, 'action': context.action.key, 'ip_address': entity.ip_address})
      context.model.set_current_user(entity, session)
      context._user = entity
      context.user = entity
      context._session = session
    context.output['entity'] = context._user
    if not context._user._is_guest:
      context.output['authorization_code'] = '%s|%s' % (context._user.key.urlsafe(), context._session.session_id)


class UserLogoutOutput(orm.BaseModel):
  
  def run(self, context):
    context._user.set_current_user(None, None)
    context.output['entity'] = context._user.current_user()


class UserUpdateSet(orm.BaseModel):
  
  def run(self, context):
    primary_email = context.input.get('primary_email')
    disassociate = context.input.get('disassociate')
    for identity in context._user.identities.value:
      if disassociate:
        if identity.identity in disassociate:
          identity.associated = False
      else:
        identity.associated = True
      if primary_email:
        identity.primary = False
        if identity.email == primary_email:
          identity.primary = True
          identity.associated = True


class UserReadDomains():
  
  def run(self, context):
    # We could go with this strategy perhaps!?
    # entity = context.user
    entity_key = context.input.get('key')
    entity = entity_key.get()
    entity.read()
    kwargs = {'user': context.user, 'action': context.action}
    rule_prepare(entity, True, False, **kwargs)
    rule_exec(entity, context.action)
    domains = []
    domain_users = []
    if entity.domains and len(entity.domains):
      # fastest way is this one
      # for every argument, there must be a set of keys that are lists e.g. iterables
      domains, domain_users = orm.get_multi_combined_clean(entity.domains, [orm.Key('8', entity.key_id_str, namespace=domain._urlsafe) for domain in entity.domains])
      # merge all keys and slice them when they arrive
      rule_prepare(domains, True, False, **kwargs)
      rule_prepare(domain_users, True, False, **kwargs)
    context.output['domains'] = domains
    context.output['domain_users'] = domain_users


class DomainCreateWrite(orm.BaseModel):
  
  def run(self, context):
    config_input = context.input.copy()
    Configuration = context.models['57']
    config = Configuration(parent=context.user.key, configuration_input=config_input, setup='setup_domain', state='active')
    config.put()
    context._config = config
