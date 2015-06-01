# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib

import orm
from tools import oauth2
from tools.base import *
from util import *


class OAuth2Error(Exception):
  
  def __init__(self, error):
    self.message = {'oauth2_error': error}


class AccountLoginInit(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    login_methods = self.cfg.get('methods', [])
    context._account = context.model.current_account()
    context.account = context.model.current_account()
    kwargs = {'account': context.account, 'action': context.action}
    rule_prepare(context._account, False, **kwargs)
    rule_exec(context._account, context.action)
    login_method = context.input.get('login_method')
    error = context.input.get('error')
    code = context.input.get('code')
    for login in login_methods:
      if login['type'] == login_method:
        oauth2_cfg = login
        break
    client = oauth2.Client(**oauth2_cfg)
    context.output['authorization_url'] = client.get_authorization_code_uri()
    urls = {}
    for cfg in login_methods:
      urls_oauth2_cfg = cfg
      urls_client = oauth2.Client(**urls_oauth2_cfg)
      urls[urls_oauth2_cfg['type']] = urls_client.get_authorization_code_uri()
    context.output['authorization_urls'] = urls
    if error:
      raise OAuth2Error('rejected_account_access')
    if code:
      client.get_token(code)
      if not client.access_token:
        raise OAuth2Error('failed_access_token')
      account_info = oauth2_cfg['accountinfo']
      info = client.resource_request(url=account_info)
      if info and 'email' in info:
        identity = oauth2_cfg['type']
        context._identity_id = '%s-%s' % (info['id'], identity)
        context._email = info['email'].lower() # we lowercase the email because datastore data searches are case sensetive
        account = context.model.query(context.model.identities.identity == context._identity_id).get()
        if account:
          account.read()
          context._account = account
          context.account = account
    kwargs = {'account': context.account, 'action': context.action}
    rule_prepare(context._account, False, **kwargs)
    rule_exec(context._account, context.action)


class AccountLoginWrite(orm.BaseModel):
  
  def run(self, context):
    
    if hasattr(context, '_identity_id') and context._identity_id is not None:
      Account = context.models['11']
      Buyer = context.models['19']
      AccountIdentity = context.models['10']
      entity = context._account
      if entity._is_guest:
        entity = context.model()
        entity.read()
        entity.identities = [AccountIdentity(identity=context._identity_id, email=context._email, primary=True)]
        entity.state = 'active'
        session = entity.new_session()
        # We separate record procedure from write in this case, since we are creating new entity which is record agent at the same time!
        entity._use_rule_engine = False
        entity.write({})
        buyer = Buyer(parent=entity.key, id='buyer') # create buyer profile right away
        buyer._use_rule_engine = False
        buyer.write({})
        entity._record_arguments = {'agent': entity.key, 'action': context.action.key, 'ip_address': entity.ip_address}
        entity.record()
      else:
        used_identity = False
        for identity in entity.identities.value:
          if identity.identity == context._identity_id:
            if identity.email != context._email:
              identity.email = context._email
            identity.primary = True
            used_identity = True
            break
        if not used_identity:
          identity = AccountIdentity(identity=context._identity_id, email=context._email, primary=True)
          entity.identities = [identity]
        for ident in entity.identities.value:
          if ident == identity:
            continue
          else:
            ident.primary = False
        session = entity.new_session()
        entity.write({'agent': entity.key, 'action': context.action.key, 'ip_address': entity.ip_address})
      context.model.set_current_account(entity, session)
      context._account = entity
      context.account = entity
      context._session = session
    context.output['entity'] = context._account
    if not context._account._is_guest and hasattr(context, '_session'):
      context.output['access_token'] = '%s|%s' % (context._account.key.urlsafe(), context._session.session_id)


class AccountLogoutOutput(orm.BaseModel):
  
  def run(self, context):
    context._account.set_current_account(None, None)
    context.output['entity'] = context._account.current_account()


class AccountUpdateSet(orm.BaseModel):
  
  def run(self, context):
    primary_canceled = False
    disassociate = context.input.get('disassociate')
    for identity in context._account.identities.value:
      if disassociate:
        if identity.identity in disassociate:
          identity._state = 'deleted'
          if identity.primary:
            primary_canceled = True
      else:
        identity._state = None
    if primary_canceled:
      for identity in context._account.identities.value:
        if identity._state != 'deleted':
          identity.primary = True
          break
