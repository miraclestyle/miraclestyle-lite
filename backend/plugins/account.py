# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import zlib
import base64

from google.appengine.runtime.apiproxy_errors import RequestTooLargeError

import orm
import tools


class OAuth2Error(Exception):

  def __init__(self, error):
    self.message = {'oauth2_error': error}


class AccountLoginInit(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def parse_result_3(self, result):
    return {
      'id': result['id'],
      'email': result['emailAddress']
    }

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    get_host_url = self.cfg.get('get_host_url')
    login_methods = self.cfg.get('methods', [])
    context._account = context.model.current_account()
    context.account = context.model.current_account()
    kwargs = {'account': context.account, 'action': context.action}
    tools.rule_prepare(context._account, **kwargs)
    tools.rule_exec(context._account, context.action)
    login_method = context.input.get('login_method')
    error = context.input.get('error')
    if not error:
      error = context.input.get('error_message')
    code = context.input.get('code')
    state = context.input.get('state')
    if code and state != context.account._csrf:
      raise OAuth2Error('state_error')
    for login in login_methods:
      if login['type'] == login_method:
        oauth2_cfg = login.copy()
        oauth2_cfg['state'] = context.account._csrf
        break
    client = tools.OAuth2Client(**oauth2_cfg)
    context.output['authorization_url'] = client.get_authorization_code_uri()
    urls = {}
    for cfg in login_methods:
      urls_oauth2_cfg = cfg.copy()
      urls_oauth2_cfg['redirect_uri'] = '%s%s' % (get_host_url(), urls_oauth2_cfg['redirect_uri'])
      urls_oauth2_cfg['state'] = context.account._csrf
      urls_client = tools.OAuth2Client(**urls_oauth2_cfg)
      urls[urls_oauth2_cfg['type']] = urls_client.get_authorization_code_uri()
    context.output['authorization_urls'] = urls
    if error:
      raise OAuth2Error('rejected_account_access')
    if code:
      client.get_token(code)
      if not client.access_token:
        raise OAuth2Error('failed_access_token')
      account_info = oauth2_cfg['account_info']
      info = client.resource_request(url=account_info)
      parse = getattr(self, 'parse_result_%s' % login_method, None)
      if parse:
        info = parse(info)
      if info and 'email' in info:
        identity = oauth2_cfg['type']
        context._identity_id = '%s-%s' % (info['id'], identity)
        context._email = info['email'].lower()  # we lowercase the email because datastore data searches are case sensetive
        account = context.model.query(context.model.identities.identity == context._identity_id).get()
        if account:
          own_account = context.account.key == account.key
          if context.account._is_guest or own_account:
            account.read()
            context._account = account
            context.account = account
          elif not own_account and not context.account._is_guest:
            raise OAuth2Error('taken_by_other_account')
      else:
        raise OAuth2Error('no_email_provided')
    kwargs = {'account': context.account, 'action': context.action}
    tools.rule_prepare(context._account, **kwargs)
    tools.rule_exec(context._account, context.action)


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
        buyer = Buyer(parent=entity.key, id='buyer')  # create buyer profile right away
        buyer._use_rule_engine = False
        buyer.write({})
        entity._record_arguments = {'agent': entity.key, 'action': context.action.key, 'ip_address': entity.ip_address}
        entity.record()
      else:
        current_identity = False
        for identity in entity.identities.value:
          identity.primary = False
          if identity.identity == context._identity_id:
            if identity.email != context._email:
              identity.email = context._email
            identity.primary = True
            current_identity = identity
        if not current_identity:
          entity.identities = [AccountIdentity(identity=context._identity_id, email=context._email, primary=True)]
          if not context.account._is_guest:
            context.output['identity_added'] = True
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
    any_identity = filter(lambda x: x._state != 'deleted', context._account.identities.value)
    if not any_identity:
      context._account.state = 'suspended'
      tools.del_attr(context, '_account.sessions')


class AccountCacheGroupUpdate(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    AccountCacheGroup = context.models['135']
    delete = context.input.get('delete')
    keys = context.input.get('keys')
    if keys:
      keys = context.input.get('keys')
      if keys:
        keys = zlib.decompress(base64.b64decode(keys)).split(',')
    ids = [AccountCacheGroup.build_key(id) for id in context.input.get('ids')]
    groups = orm.get_multi(ids)
    save = []
    active = []
    delete_active = []
    def make_active(k):
      return '%s_active' % k
    for i, group in enumerate(groups):
      changes = False
      if not group:
        changes = True
        group = AccountCacheGroup(id=context.input.get('ids')[i], keys=[])
      for k in keys:
        if k in group.keys:
          changes = True
          if delete:
            group.keys.remove(k)
            delete_active.extend([make_active(kk) for kk in group.keys])
        else:
          changes = True
          group.keys.append(k)
        active.extend([make_active(kk) for kk in group.keys])
      if changes:
        save.append(group)
    try:
      orm.put_multi(save)
      tools.mem_delete_multi(delete_active)
      tools.mem_set_multi(dict((k, True) for k in active))
    except RequestTooLargeError as e: # size of entity exceeded
      if not delete:
        delete_keys = []
        for s in save:
          delete_keys.extend(s.keys)
          s.keys = keys
        orm.put_multi(save)
        if delete_keys:
          tools.mem_delete_multi(delete_keys)

