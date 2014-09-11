# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import os

from app import orm, mem, settings
from app.models import *
from app.plugins import *


class AccountSession(orm.BaseModel):
  
  _kind = 9
  
  _use_rule_engine = False
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True, indexed=False)
  session_id = orm.SuperStringProperty('2', required=True, indexed=False)


class AccountIdentity(orm.BaseModel):
  
  _kind = 10
  
  _use_rule_engine = False
  
  identity = orm.SuperStringProperty('1', required=True)  # This property stores provider name joined with ID.
  email = orm.SuperStringProperty('2', required=True)
  associated = orm.SuperBooleanProperty('3', required=True, default=True)
  primary = orm.SuperBooleanProperty('4', required=True, default=True)


# @todo We need to trigger account_discontinue on catalogs during account suspension!
class Account(orm.BaseExpando):
  
  _kind = 11
  
  _use_memcache = True
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  identities = orm.SuperStructuredProperty(AccountIdentity, '3', repeated=True)  # Soft limit 100 instances.
  emails = orm.SuperStringProperty('4', repeated=True)  # Soft limit 100 instances.
  state = orm.SuperStringProperty('5', required=True, choices=['active', 'suspended', 'su_suspended'])  # @todo Not sure what to do here? Shall we disable indexing here?
  sessions = orm.SuperLocalStructuredProperty(AccountSession, '6', repeated=True)  # Soft limit 100 instances.
  
  _default_indexed = False
  
  _virtual_fields = {
    'ip_address': orm.SuperComputedProperty(lambda self: os.environ.get('REMOTE_ADDR')),
    '_primary_email': orm.SuperComputedProperty(lambda self: self.primary_email()),
    '_records': orm.SuperRecordProperty('11')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('11', orm.Action.build_key('11', 'login'), True,
                           'entity._is_guest or entity._original.state == "active"'),
      orm.ActionPermission('11', [orm.Action.build_key('11', 'read'),
                                  orm.Action.build_key('11', 'update'),
                                  orm.Action.build_key('11', 'logout'),
                                  orm.Action.build_key('11', 'blob_upload_url')], True,
                           'not account._is_guest and account.key == entity._original.key'),
      orm.FieldPermission('11', ['created', 'updated', 'state'], False, True,
                          'not account._is_guest and account.key == entity._original.key'),
      orm.FieldPermission('11', ['identities', 'emails', 'sessions', '_primary_email'], True, True,
                          'not account._is_guest and account.key == entity._original.key'),
      # Account is unit of administration, hence root admins need control over it!
      # Root admins can always: read account; search for accounts (exclusively);
      # read accounts history (exclusively); perform sudo operations (exclusively).
      orm.ActionPermission('11', [orm.Action.build_key('11', 'read'),
                                  orm.Action.build_key('11', 'search'),
                                  orm.Action.build_key('11', 'sudo')], True, 'account._root_admin'),
      orm.FieldPermission('11', ['created', 'updated', 'identities', 'emails', 'state', 'sessions',
                                 'ip_address', '_primary_email', '_records'], None, True, 'account._root_admin'),
      orm.FieldPermission('11', ['state'], True, None, 'action.key_id_str == "sudo" and account._root_admin')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('11', 'login'),
      arguments={
        'login_method': orm.SuperStringProperty(required=True, choices=settings.LOGIN_METHODS.keys()),
        'code': orm.SuperStringProperty(),
        'error': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            AccountLoginInit(cfg={'methods': settings.LOGIN_METHODS})
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            AccountLoginWrite()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('11', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='11', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_account'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('11', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='11', required=True),
        'primary_email': orm.SuperStringProperty(),
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
            Set(cfg={'d': {'output.entity': '_account'}}),
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('11', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'orders': [{'field': 'created', 'operator': 'desc'}]},
          cfg={
            'search_arguments': {'kind': '11', 'options': {'limit': settings.SEARCH_PAGE}},
            'filters': {'emails': orm.SuperStringProperty(),
                        'state': orm.SuperStringProperty()},
            'indexes': [{'orders': [('emails', ['asc', 'desc'])]},
                        {'orders': [('created', ['asc', 'desc'])]},
                        {'orders': [('updated', ['asc', 'desc'])]},
                        {'filters': [('emails', ['==', '!='])],
                         'orders': [('created', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!='])],
                         'orders': [('created', ['asc', 'desc'])]}]
            }
          )
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
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
    # @todo Treba obratiti paznju na to da suspenzija accounta ujedno znaci
    # i izuzimanje svih negativnih i neutralnih feedbackova koje je account ostavio dok je bio aktivan.
    orm.Action(
      key=orm.Action.build_key('11', 'sudo'),
      arguments={
        'key': orm.SuperKeyProperty(kind='11', required=True),
        'state': orm.SuperStringProperty(required=True, choices=['active', 'suspended']),
        'message': orm.SuperStringProperty(required=True),
        'note': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_account.state': 'input.state'}, 's': {'_account.sessions': []}}),
            RulePrepare(),
            RuleExec(),
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),
            Set(cfg={'d': {'output.entity': '_account'}}),
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('11', 'logout'),
      arguments={
        'key': orm.SuperKeyProperty(kind='11', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_account.sessions': []}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'ip_address': '_account.ip_address'}}),
            AccountLogoutOutput()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('11', 'blob_upload_url'),
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
      )
    ]
  
  def get_output(self):
    dic = super(Account, self).get_output()
    dic.update({'_csrf': self._csrf,  # We will need the csrf but it has to be incorporated into security mechanism (http://en.wikipedia.org/wiki/Cross-site_request_forgery).
                '_is_guest': self._is_guest,
                '_root_admin': self._root_admin})
    return dic
  
  @property
  def _root_admin(self):
    return self._primary_email in settings.ROOT_ADMINS
  
  @property
  def _is_taskqueue(self):
    return mem.temp_get('_current_request_is_taskqueue')
  
  @property
  def _is_cron(self):
    return mem.temp_get('_current_request_is_cron')
  
  def set_taskqueue(self, is_it):
    return mem.temp_set('_current_request_is_taskqueue', is_it)
  
  def set_cron(self, is_it):
    return mem.temp_set('_current_request_is_cron', is_it)
  
  def primary_email(self):
    if not self.identities.value:
      return None
    for identity in self.identities.value:
      if identity.primary == True:
        return identity.email
    return identity.email
  
  @property
  def _csrf(self):
    session = self.current_account_session()
    if not session:
      return None
    return hashlib.md5(session.session_id).hexdigest()
  
  @property
  def _is_guest(self):
    return self.key is None
  
  @classmethod
  def set_current_account(cls, account, session=None):
    mem.temp_set('_current_account', account)
    mem.temp_set('_current_account_session', session)
  
  @classmethod
  def current_account(cls):
    current_account = mem.temp_get('_current_account')
    if not current_account:
      current_account = cls()
      cls.set_current_account(current_account)
    return current_account
  
  @classmethod
  def get_system_account(cls):
    account_key = cls.build_key('system')
    account = account_key.get()
    if not account:
      identities = [AccountIdentity(email='System', identity='1-0', associated=True, primary=True)]
      account = cls(key=account_key, state='active', emails=['System'], identities=identities)
      account.put()
    return account
  
  @classmethod
  def current_account_session(cls):
    return mem.temp_get('_current_account_session')
  
  def session_by_id(self, session_id):
    for session in self.sessions.value:
      if session.session_id == session_id:
        return session
    return None
  
  @classmethod
  def set_current_account_from_auth_code(cls, auth_code):
    try:
      account_key, session_id = auth_code.split('|')
    except:
      return False # Fail silently if the authorization code is not set properly, or it is corrupted somehow.
    if not session_id:
      return False # Fail silently if the session id is not found in the split sequence.
    account_key = orm.Key(urlsafe=account_key)
    if account_key.kind() != cls.get_kind():
      return False # Fail silently if the kind is not valid
    account = account_key.get()
    if account and account.key_id != 'system':
      account.read()
      session = account.session_by_id(session_id)
      if session:
        cls.set_current_account(account, session)
        return account
