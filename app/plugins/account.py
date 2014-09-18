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


class OAuth2Error(Exception):
  
  def __init__(self, error):
    self.message = {'oauth2_error': error}


class AccountLoginInit(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    login_methods = self.cfg.get('methods', {})
    context._account = context.model.current_account()
    context.account = context.model.current_account()
    kwargs = {'account': context.account, 'action': context.action}
    rule_prepare(context._account, False, **kwargs)
    rule_exec(context._account, context.action)
    login_method = context.input.get('login_method')
    error = context.input.get('error')
    code = context.input.get('code')
    oauth2_cfg = login_methods[login_method]['oauth2']
    client = oauth2.Client(**oauth2_cfg)
    context.output['authorization_url'] = client.get_authorization_code_uri()
    urls = {}
    for urls_login_method, cfg in login_methods.iteritems():
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
      accountinfo = oauth2_cfg['accountinfo']
      info = client.resource_request(url=accountinfo)
      if info and 'email' in info:
        identity = oauth2_cfg['type']
        context._identity_id = '%s-%s' % (info['id'], identity)
        context._email = info['email']
        account = context.model.query(context.model.identities.identity == context._identity_id).get()
        if not account:
          account = context.model.query(context.model.emails == context._email).get()
        if account:
          context._account = account
          context.account = account
    kwargs = {'account': context.account, 'action': context.action}
    rule_prepare(context._account, False, **kwargs)
    rule_exec(context._account, context.action)


class AccountLoginWrite(orm.BaseModel):
  
  def run(self, context):
    def new_session(entity):
      AccountSession = context.models['9']
      session_ids = [session.session_id for session in entity.sessions.value]
      while True:
        session_id = hashlib.md5(random_chars(30)).hexdigest()
        if session_id not in session_ids:
          break
      session = AccountSession(session_id=session_id)
      entity.sessions = [session]
      return session
    
    if hasattr(context, '_identity_id') and context._identity_id is not None:
      Account = context.models['11']
      AccountIdentity = context.models['10']
      entity = context._account
      if entity._is_guest:
        entity = context.model()
        entity.read()
        entity.emails = [context._email]
        entity.identities = [AccountIdentity(identity=context._identity_id, email=context._email, primary=True)]
        entity.state = 'active'
        session = new_session(entity)
        # We separate record procedure from write in this case, since we are creating new entity which is record agent at the same time!
        entity._use_rule_engine = False
        entity.write({})
        entity._record_arguments = {'agent': entity.key, 'action': context.action.key, 'ip_address': entity.ip_address}
        entity.record()
      else:
        if context._email not in entity.emails:
          entity.emails.append(context._email)
        used_identity = False
        for identity in entity.identities.value:
          if identity.identity == context._identity_id:
            identity.associated = True
            if identity.email != context._email:
              identity.email = context._email
            used_identity = True
            break
        if not used_identity:
          entity.identities = [AccountIdentity(identity=context._identity_id, email=context._email, primary=False)]
        session = new_session(entity)
        entity.write({'agent': entity.key, 'action': context.action.key, 'ip_address': entity.ip_address})
      context.model.set_current_account(entity, session)
      context._account = entity
      context.account = entity
      context._session = session
    context.output['entity'] = context._account
    if not context._account._is_guest and hasattr(context, '_session'):
      context.output['authorization_code'] = '%s|%s' % (context._account.key.urlsafe(), context._session.session_id)


class AccountLogoutOutput(orm.BaseModel):
  
  def run(self, context):
    context._account.set_current_account(None, None)
    context.output['entity'] = context._account.current_account()


class AccountUpdateSet(orm.BaseModel):
  
  def run(self, context):
    primary_email = context.input.get('primary_email')
    disassociate = context.input.get('disassociate')
    for identity in context._account.identities.value:
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
