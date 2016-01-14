# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import os
import datetime

import orm
import tools
import settings
import notifications
from plugins.base import *
from plugins.account import *


__all__ = ['AccountCacheGroup', 'AccountSession', 'AccountIdentity', 'Account']


class AccountCacheGroup(orm.BaseModel):

  _kind = 135

  _use_rule_engine = False

  keys = orm.SuperStringProperty(repeated=True, indexed=False) # stores 128bit md5 = can hold aprox 22k items

  
  def condition_taskqueue_or_admin(account, **kwargs):
    return account._is_taskqueue or account._root_admin

  _permissions = [
      orm.ExecuteActionPermission('update', condition_taskqueue_or_admin)
  ]

  _actions = [
      orm.Action(
          id='update',
          arguments={
              'ids': orm.SuperStringProperty(repeated=True),
              'keys': orm.SuperTextProperty(), # compressed base64 encoded data
              'delete': orm.SuperBooleanProperty(default=False)
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context()
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      AccountCacheGroupUpdate()
                  ]
              )
          ]
      ),
  ]

class AccountSession(orm.BaseModel):

  _kind = 9

  _use_rule_engine = False

  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True, indexed=False)
  session_id = orm.SuperStringProperty('2', required=True, indexed=False)
  ip_address = orm.SuperStringProperty('3', required=True, indexed=False)


class AccountIdentity(orm.BaseModel):

  _kind = 10

  _use_rule_engine = False

  identity = orm.SuperStringProperty('1', required=True)  # This property stores provider name joined with ID.
  email = orm.SuperStringProperty('2', required=True)
  primary = orm.SuperBooleanProperty('3', required=True, default=True)


class Account(orm.BaseExpando):

  _kind = 11

  _use_record_engine = True

  '''
  Cache:
  11_<account.id>
  '''

  READ_CACHE_POLICY = {'group': lambda context: '11_%s' % context.account.key_id_str, 'cache': ['account']}
  DELETE_CACHE_POLICY = {'group': ['admin', lambda context: '11_%s' % context._account.key_id_str, lambda context: '11_%s' % context.account.key_id_str]}

  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  state = orm.SuperStringProperty('3', required=True, default='active', choices=('active', 'suspended'))
  identities = orm.SuperStructuredProperty(AccountIdentity, '4', repeated=True)  # Soft limit 100 instances.
  sessions = orm.SuperLocalStructuredProperty(AccountSession, '5', repeated=True)  # Soft limit 100 instances.

  _default_indexed = False

  _virtual_fields = {
      'ip_address': orm.SuperComputedProperty(lambda self: os.environ.get('REMOTE_ADDR')),
      '_primary_email': orm.SuperComputedProperty(lambda self: self.primary_email()),
      '_csrf': orm.SuperComputedProperty(lambda self: self.get_csrf()),
      '_records': orm.SuperRecordProperty('11')
  }

  def condition_guest_and_active(entity, **kwargs):
    return entity._is_guest or entity._original.state == "active"

  def condition_true(entity, **kwargs):
    return True

  def condition_not_guest_and_owner(account, entity, **kwargs):
    return not account._is_guest and account.key == entity._original.key

  def condition_not_guest(account, **kwargs):
    return not account._is_guest

  def condition_root(account, **kwargs):
    return account._root_admin

  def condition_sudo_action_and_root(account, action, **kwargs):
    return action.key_id_str == "sudo" and account._root_admin
  
  def condition_account_has_identities(account, **kwargs):
    account.identities.read()
    if not account.identities.value:
      return False
    else:
      return True

  _permissions = [
      orm.ExecuteActionPermission('login', condition_guest_and_active),
      orm.ExecuteActionPermission('current_account', condition_true),
      orm.ExecuteActionPermission(('read', 'update', 'logout'), condition_not_guest_and_owner),
      orm.ExecuteActionPermission(('blob_upload_url', 'create_channel'), condition_not_guest),
      orm.ExecuteActionPermission(('read', 'search', 'sudo'), condition_root),
      orm.ReadFieldPermission(('created', 'updated', 'state', 'identities', 'sessions', '_primary_email'), condition_not_guest_and_owner),
      orm.ReadFieldPermission(('created', 'updated', 'state', 'identities', 'sessions', '_primary_email',
                               'ip_address', '_records'), condition_root),
      orm.WriteFieldPermission(('state', 'identities', 'sessions', '_primary_email', '_records'), condition_not_guest_and_owner),
      orm.WriteFieldPermission(('state', 'sessions', '_records'), condition_sudo_action_and_root)
  ]

  _actions = [
      orm.Action(
          id='login',
          skip_csrf=True,
          arguments={
              'login_method': orm.SuperStringProperty(required=True, choices=[login_method['type'] for login_method in settings.LOGIN_METHODS]),
              'code': orm.SuperStringProperty(),
              'error_message': orm.SuperStringProperty(),
              'state': orm.SuperStringProperty(),
              'error': orm.SuperStringProperty(),
              'redirect_to': orm.SuperStringProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      AccountLoginInit(cfg={'methods': settings.LOGIN_METHODS, 'get_host_url': settings.get_host_url})
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      AccountLoginWrite(),
                      DeleteCache(cfg=DELETE_CACHE_POLICY)
                  ]
              )
          ]
      ),
      orm.Action(
          id='current_account',
          skip_csrf=True,
          arguments={
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(cfg={'source': 'account.key'}),
                      RulePrepare(),
                      RuleExec(),
                      Set(cfg={'d': {'output.entity': '_account'}}),
                      CallbackExec()
                  ]
              )
          ]
      ),
      orm.Action(
          id='read',
          arguments={
              'key': orm.SuperKeyProperty(kind='11', required=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      GetCache(cfg=READ_CACHE_POLICY),
                      Read(),
                      RulePrepare(),
                      RuleExec(),
                      Set(cfg={'d': {'output.entity': '_account'}}),
                      CallbackExec()
                  ]
              )
          ]
      ),
      orm.Action(
          id='update',
          arguments={
              'key': orm.SuperKeyProperty(kind='11', required=True),
              'primary_identity': orm.SuperStringProperty(),
              'disassociate': orm.SuperStringProperty(repeated=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      AccountUpdateSet(),
                      RulePrepare(),
                      RuleExec()
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      Write(),
                      DeleteCache(cfg=DELETE_CACHE_POLICY),
                      Set(cfg={'d': {'output.entity': '_account'}}),
                      CallbackExec(cfg=[('callback',
                                         {'action_id': 'account_discontinue', 'action_model': '31'},
                                         {'account': '_account.key_urlsafe', 'account_state': '_account.state'},
                                         lambda account, account_state, **kwargs: account_state == 'suspended')])
                  ]
              )
          ]
      ),
      orm.Action(
          id='search',
          arguments={
              'search': orm.SuperSearchProperty(
                  default={'filters': [], 'orders': [{'field': 'created', 'operator': 'desc'}]},
                  cfg={
                      'search_arguments': {'kind': '11', 'options': {'limit': settings.SEARCH_PAGE}},
                      'filters': {'key': orm.SuperVirtualKeyProperty(kind='11', searchable=False),
                                  'state': orm.SuperStringProperty(choices=('active', 'suspended')),
                                  'identities.email': orm.SuperStringProperty(searchable=False)},
                      'indexes': [{'orders': [('created', ['asc', 'desc'])]},
                                  {'orders': [('updated', ['asc', 'desc'])]},
                                  {'filters': [('key', ['=='])]},
                                  {'filters': [('identities.email', ['=='])]},
                                  {'filters': [('state', ['=='])], 'orders': [('created', ['asc', 'desc'])]},
                                  {'filters': [('state', ['=='])], 'orders': [('updated', ['asc', 'desc'])]}]
                  }
              )
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      GetCache(cfg={'group': 'admin', 'cache': ['admin']}),
                      Read(),
                      RulePrepare(),
                      RuleExec(),
                      Search(),
                      RulePrepare(cfg={'path': '_entities'}),
                      Set(cfg={'d': {'output.entities': '_entities',
                                     'output.cursor': '_cursor',
                                     'output.more': '_more'}})
                  ]
              )
          ]
      ),
      orm.Action(
          id='sudo',
          arguments={
              'key': orm.SuperKeyProperty(kind='11', required=True),
              'state': orm.SuperStringProperty(required=True, choices=('active', 'suspended')),
              'message': orm.SuperTextProperty(required=True),
              'note': orm.SuperTextProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      Set(cfg={'rm': ['_account.sessions'], 'd': {'_account.state': 'input.state'}}),
                      RulePrepare(),
                      RuleExec()
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      Write(),
                      Set(cfg={'d': {'output.entity': '_account'}}),
                      Notify(cfg={'s': {'subject': notifications.ACCOUNT_SUDO_SUBJECT,
                                        'body': notifications.ACCOUNT_SUDO_BODY,
                                        'sender': settings.NOTIFY_EMAIL},
                                  'd': {'recipient': '_account._primary_email'}}),
                      DeleteCache(cfg=DELETE_CACHE_POLICY),
                      CallbackExec(cfg=[('callback',
                                         {'action_id': 'account_discontinue', 'action_model': '31'},
                                         {'account': '_account.key_urlsafe', 'account_state': '_account.state'},
                                         lambda account, account_state, **kwargs: account_state == 'suspended')])
                  ]
              )
          ]
      ),
      orm.Action(
          id='logout',
          arguments={
              'key': orm.SuperKeyProperty(kind='11', required=True)
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      Set(cfg={'rm': ['_account.sessions']}),
                      RulePrepare(),
                      RuleExec()
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      Write(cfg={'dra': {'ip_address': '_account.ip_address'}}),
                      DeleteCache(cfg=DELETE_CACHE_POLICY),
                      AccountLogoutOutput()
                  ]
              )
          ]
      ),
      orm.Action(
          id='blob_upload_url',
          arguments={
              'upload_url': orm.SuperStringProperty(required=True)
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      RulePrepare(),
                      RuleExec(),
                      BlobURL(cfg={'bucket': settings.BUCKET_PATH}),
                      Set(cfg={'d': {'output.upload_url': '_blob_url'}})
                  ]
              )
          ]
      ),
      orm.Action(
          id='create_channel',
          arguments={},
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      RulePrepare(),
                      RuleExec(),
                      CreateChannel(),
                      Set(cfg={'d': {'output.token': '_token'}})
                  ]
              )
          ]
      )
  ]

  def get_output(self):
    dic = super(Account, self).get_output()
    dic.update({'_is_guest': self._is_guest,
                '_is_system': self._is_system,
                '_csrf': self._csrf,
                '_root_admin': self._root_admin})
    location = self.current_location_data()
    if isinstance(location, dict):
      dic.update(location)
    return dic

  @property
  def _root_admin(self):
    return self._primary_email in settings.ROOT_ADMINS

  @property
  def _is_taskqueue(self):
    return tools.mem_temp_get('current_request_is_taskqueue')

  @property
  def _is_cron(self):
    return tools.mem_temp_get('current_request_is_cron')

  @property
  def _is_system(self):
    return self.key_id_str == 'system'

  @property
  def _is_guest(self):
    return self.key is None

  def primary_email(self):
    self.identities.read()
    if not self.identities.value:
      return None
    for identity in self.identities.value:
      if identity.primary:
        return identity.email

  def get_csrf(self):
    session = self.current_account_session()
    if not session:
      return hashlib.md5(os.environ['REMOTE_ADDR'] + settings.CSRF_SALT).hexdigest()
    return hashlib.md5('%s-%s' % (session.session_id, settings.CSRF_SALT)).hexdigest()

  @classmethod
  def current_account(cls):
    current_account = tools.mem_temp_get('current_account')
    if not current_account:
      current_account = cls()
      cls.set_current_account(current_account)
    return current_account

  @classmethod
  def system_account(cls):
    account_key = cls.build_key('system')
    account = account_key.get()
    if not account:
      identities = [AccountIdentity(email='System', identity='1-0', primary=True)]
      account = cls(key=account_key, state='active', identities=identities)
      account._use_rule_engine = False
      account.put()
      account._use_rule_engine = True
    return account

  @classmethod
  def current_account_session(cls):
    return tools.mem_temp_get('current_account_session')

  @staticmethod
  def hash_session_id(session_id):
    return hashlib.md5('%s%s' % (session_id, settings.AUTH_SALT1)).hexdigest()

  def session_by_id(self, session_id):
    for session in self.sessions.value:
      if session.session_id == session_id:
        return session
    return None

  def new_session(self):
    account = self
    session_ids = set()
    for session in account.sessions.value:
      if session.created < (datetime.datetime.now() - datetime.timedelta(days=10)):
        session._state = 'deleted'
      session_ids.add(session.session_id)
    while True:
      session_id = hashlib.md5(tools.random_chars(30)).hexdigest()
      if session_id not in session_ids:
        break
    session = AccountSession(session_id=session_id, ip_address=self.ip_address)
    account.sessions = [session]
    return session

  @classmethod
  def current_location_data(cls):
    return tools.mem_temp_get('current_request_location_data')
  
  @classmethod
  def set_location_data(cls, data):
    if data:
      if data.get('_country') and data.get('_country').lower() != 'zz':
        data['_country'] = orm.Key('12', data['_country'].lower())
        if data.get('_region'):
          data['_region'] = orm.Key('13', '%s-%s' % (data['_country']._id_str, data['_region'].lower()), parent=data['_country'])
      else:
        data['_region'] = None
        data['_country'] = None
    return tools.mem_temp_set('current_request_location_data', data)
  
  @classmethod
  def set_taskqueue(cls, flag):
    return tools.mem_temp_set('current_request_is_taskqueue', flag)

  @classmethod
  def set_cron(self, flag):
    return tools.mem_temp_set('current_request_is_cron', flag)

  @classmethod
  def set_current_account(cls, account, session=None):
    tools.mem_temp_set('current_account', account)
    tools.mem_temp_set('current_account_session', session)

  @classmethod
  def set_current_account_from_access_token(cls, access_token):
    try:
      account_key, session_id = access_token.split('|')
    except:
      return False  # Fail silently if the authorization code is not set properly, or it is corrupted somehow.
    if not session_id:
      return False  # Fail silently if the session id is not found in the split sequence.
    account_key = orm.Key(urlsafe=account_key)
    if account_key.kind() != cls.get_kind() or account_key.id() == 'system':
      return False  # Fail silently if the kind is not valid
    account = account_key.get()
    if account:
      account.read()
      session = account.session_by_id(session_id)
      if session:
        cls.set_current_account(account, session)
        return account
