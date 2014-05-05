# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib

from app import ndb, settings, memcache, util
from app.srv.event import Action
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.srv import log as ndb_log
from app.plugins import common, rule, log, callback, auth


class Session(ndb.BaseModel):
  
  _kind = 70
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True, indexed=False)
  session_id = ndb.SuperStringProperty('2', required=True, indexed=False)


class Identity(ndb.BaseModel):
  
  _kind = 64
  
  identity = ndb.SuperStringProperty('1', required=True)  # This property stores provider name joined with ID.
  email = ndb.SuperStringProperty('2', required=True)
  associated = ndb.SuperBooleanProperty('3', required=True, default=True)
  primary = ndb.SuperBooleanProperty('4', required=True, default=True)


class User(ndb.BaseExpando):
  
  _kind = 0
  
  _use_memcache = True
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  identities = ndb.SuperStructuredProperty(Identity, '3', repeated=True)  # Soft limit 100 instances.
  emails = ndb.SuperStringProperty('4', repeated=True)  # Soft limit 100 instances.
  state = ndb.SuperStringProperty('5', required=True, choices=['active', 'suspended'])  # @todo Shall we disable indexing here?
  sessions = ndb.SuperLocalStructuredProperty(Session, '6', repeated=True)  # Soft limit 100 instances.
  domains = ndb.SuperKeyProperty('7', kind='6', repeated=True)  # Soft limit 100 instances. @todo Shall we disable indexing here?
  
  _default_indexed = False
  
  _expando_fields = {}
  
  _virtual_fields = {
    'ip_address': ndb.SuperStringProperty(),
    '_primary_email': ndb.SuperComputedProperty(lambda self: self.primary_email()),
    '_records': ndb_log.SuperLocalStructuredRecordProperty('0', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('0', Action.build_key('0', 'login').urlsafe(), True,
                       "context.entities['0']._is_guest or context.entities['0'].state == 'active'"),
      ActionPermission('0', Action.build_key('0', 'update').urlsafe(), True,
                       "not context.entities['0']._is_guest and context.user.key == context.entities['0'].key"),
      ActionPermission('0', Action.build_key('0', 'logout').urlsafe(), True,
                       "not context.entities['0']._is_guest and context.user.key == context.entities['0'].key and context.entities['0']._csrf == context.input['csrf']"),
      ActionPermission('0', Action.build_key('0', 'read_domains').urlsafe(), True,
                       "not context.entities['0']._is_guest and context.user.key == context.entities['0'].key"),
      FieldPermission('0', ['created', 'updated', 'state'], False, True,
                      "not context.entities['0']._is_guest and context.user.key == context.entities['0'].key"),
      FieldPermission('0', ['identities', 'emails', 'sessions', 'domains', '_primary_email'], True, True,
                      "not context.entities['0']._is_guest and context.user.key == context.entities['0'].key"),
      # User is unit of administration, hence root admins need control over it!
      # Root admins can always: read user; search for users (exclusively); 
      # read users history (exclusively); perform sudo operations (exclusively).
      ActionPermission('0', Action.build_key('0', 'read').urlsafe(), True,
                       "context.user._root_admin or context.user.key == context.entities['0'].key"),
      ActionPermission('0', Action.build_key('0', 'search').urlsafe(), True, "context.user._root_admin"),
      ActionPermission('0', Action.build_key('0', 'search').urlsafe(), False, "not context.user._root_admin"),
      ActionPermission('0', Action.build_key('0', 'read_records').urlsafe(), True, "context.user._root_admin"),
      ActionPermission('0', Action.build_key('0', 'read_records').urlsafe(), False, "not context.user._root_admin"),
      ActionPermission('0', Action.build_key('0', 'sudo').urlsafe(), True, "context.user._root_admin"),
      ActionPermission('0', Action.build_key('0', 'sudo').urlsafe(), False, "not context.user._root_admin"),
      FieldPermission('0', ['created', 'updated', 'identities', 'emails', 'state', 'sessions', 'domains',
                                 'ip_address', '_primary_email', '_records'], False, True, "context.user._root_admin")
      # @todo Not sure how to handle field permissions (though some actions seem to not respect field permissions)?
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('0', 'login'),
      arguments={
        'login_method': ndb.SuperStringProperty(required=True, choices=settings.LOGIN_METHODS.keys()),
        'code': ndb.SuperStringProperty(),
        'error': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        auth.UserLoginPrepare(),
        auth.UserIPAddress(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        auth.UserLoginOAuth(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        auth.UserLoginUpdate(transactional=True),
        log.Entity(transactional=True, dynamic_arguments={'ip_address': 'ip_address'}),
        log.Write(transactional=True),
        rule.Prepare(transactional=True, skip_user_roles=True, strict=False),
        rule.Read(transactional=True),
        auth.UserLoginOutput(transactional=True)
        ]
      ),
    Action(
      key=Action.build_key('0', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.0'})
        ]
      ),
    Action(
      key=Action.build_key('0', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'primary_email': ndb.SuperStringProperty(),
        'disassociate': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        auth.UserUpdate(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.0'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.0.key_urlsafe'}),
        callback.Exec(transactional=True, dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('0', 'search'),
      arguments={
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "created", "operator": "desc"}},
          filters={
            'emails': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()}
            },
          indexes=[
            {'filter': ['emails'],
             'order_by': [['emails', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['state'],
             'order_by': [['emails', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': [],
             'order_by': [['emails', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]}
            ],
          order_by={
            'emails': {'operators': ['asc', 'desc']},
            'created': {'operators': ['asc', 'desc']},
            'updated': {'operators': ['asc', 'desc']}
            }
          ),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        common.Search(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('0', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        log.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.0', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    """@todo Treba obratiti paznju na to da suspenzija usera ujedno znaci
    i izuzimanje svih negativnih i neutralnih feedbackova koje je user ostavio dok je bio aktivan.
    
    """
    Action(
      key=Action.build_key('0', 'sudo'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'state': ndb.SuperStringProperty(required=True, choices=['active', 'suspended']),
        'message': ndb.SuperStringProperty(required=True),
        'note': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(dynamic_values={'values.0.state': 'input.state'}),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        auth.UserSudo(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message', 'note': 'input.note'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.0'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.0.key_urlsafe'}),
        callback.Exec(transactional=True, dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('0', 'logout'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'csrf': ndb.SuperStringProperty(required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(static_values={'values.0.sessions': []}),
        auth.UserIPAddress(),
        rule.Prepare(skip_user_roles=True,  strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True, dynamic_arguments={'ip_address': 'ip_address'}),
        log.Write(transactional=True),
        auth.UserLogoutOutput(transactional=True)
        ]
      ),
    Action(
      key=Action.build_key('0', 'read_domains'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        auth.UserReadDomains(),
        common.Set('entities': 'domains')
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set('entities': 'domain_users')
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.domains': 'domains', 'output.domain_users': 'domain_users'})
        ]
      )
    ]
  
  def get_output(self):
    dic = super(User, self).get_output()
    dic.update({'_csrf': self._csrf,  # We will need the csrf but it has to be incorporated into security mechanism (http://en.wikipedia.org/wiki/Cross-site_request_forgery).
                '_is_guest': self._is_guest,
                '_root_admin': self._root_admin})
    return dic
  
  @property
  def _is_taskqueue(self):
    return memcache.temp_memory_get('_current_request_is_taskqueue')
  
  def set_taskqueue(self, is_it):
    return memcache.temp_memory_set('_current_request_is_taskqueue', is_it)
  
  @property
  def _root_admin(self):
    return self._primary_email in settings.ROOT_ADMINS
  
  def primary_email(self):
    if not self.identities:
      return None
    for identity in self.identities:
      if identity.primary == True:
        return identity.email
    return identity.email
  
  @property
  def _csrf(self):
    session = self.current_user_session()
    if not session:
      return None
    return hashlib.md5(session.session_id).hexdigest()
  
  @property
  def _is_guest(self):
    return self.key == None
  
  @classmethod
  def set_current_user(cls, user, session=None):
    memcache.temp_memory_set('_current_user', user)
    memcache.temp_memory_set('_current_user_session', session)
  
  @classmethod
  def current_user(cls):
    current_user = memcache.temp_memory_get('_current_user')
    if not current_user:
      current_user = cls()
    return current_user
  
  @classmethod
  def current_user_session(cls):
    return memcache.temp_memory_get('_current_user_session')
  
  def session_by_id(self, session_id):
    for session in self.sessions:
      if session.session_id == session_id:
        return session
    return None
  
  @classmethod
  def login_from_authorization_code(cls, auth_code):
    try:
      user_key, session_id = auth_code.split('|')
    except:
      return  # Fail silently if the authorization code is not set properly, or it is corrupted somehow.
    if not session_id:
      return  # Fail silently if the session id is not found in the split sequence.
    user = ndb.Key(urlsafe=user_key).get()
    if user:
      session = user.session_by_id(session_id)
      if session:
        cls.set_current_user(user, session)


class Domain(ndb.BaseExpando):
  
  _kind = 6
  
  _use_memcache = True
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = ndb.SuperStringProperty('3', required=True)
  primary_contact = ndb.SuperKeyProperty('4', kind=User, required=True, indexed=False)
  state = ndb.SuperStringProperty('5', required=True, choices=['active', 'suspended', 'su_suspended'])
  logo = ndb.SuperLocalStructuredImageProperty(blob.Image, '6', required=True)
  
  _default_indexed = False
  
  _expando_fields = {}
  
  _virtual_fields = {
    '_primary_contact_email': ndb.SuperStringProperty(),
    '_records': ndb_log.SuperLocalStructuredRecordProperty('6', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('6', Action.build_key('6', 'prepare').urlsafe(), True,
                       "not context.user._is_guest"),
      ActionPermission('6', Action.build_key('6', 'create').urlsafe(), True,
                       "not context.user._is_guest"),
      ActionPermission('6', Action.build_key('6', 'update').urlsafe(), False,
                       "context.entities['6'].state != 'active'"),
      ActionPermission('6', Action.build_key('6', 'suspend').urlsafe(), False,
                       "context.entities['6'].state != 'active'"),
      ActionPermission('6', Action.build_key('6', 'activate').urlsafe(), False,
                       "context.entities['6'].state == 'active' or context.entities['6'].state == 'su_suspended'"),
      FieldPermission('6', ['name', 'primary_contact', 'logo', '_records', '_primary_contact_email'], False, None,
                      "context.entities['6'].state != 'active'"),
      FieldPermission('6', ['created', 'updated', 'state'], False, None, "True"),
      # Domain is unit of administration, hence root admins need control over it!
      # Root admins can always: read domain; search for domains (exclusively); 
      # read domain history; perform sudo operations (exclusively); log messages; read _records.note field (exclusively).
      ActionPermission('6', Action.build_key('6', 'read').urlsafe(), True,
                       "context.user._root_admin"),
      ActionPermission('6', Action.build_key('6', 'search').urlsafe(), True,
                       "context.user._root_admin"),
      ActionPermission('6', Action.build_key('6', 'search').urlsafe(), False,
                       "not context.user._root_admin"),
      ActionPermission('6', Action.build_key('6', 'read_records').urlsafe(), True,
                       "context.user._root_admin"),
      ActionPermission('6', Action.build_key('6', 'sudo').urlsafe(), True,
                       "context.user._root_admin"),
      ActionPermission('6', Action.build_key('6', 'sudo').urlsafe(), False,
                       "not context.user._root_admin"),
      ActionPermission('6', Action.build_key('6', 'log_message').urlsafe(), True,
                       "context.user._root_admin"),
      FieldPermission('6', ['created', 'updated', 'name', 'primary_contact', 'state', 'logo', '_records',
                            '_primary_contact_email'], False, True, "context.user._root_admin"),
      FieldPermission('6', ['_records.note'], True, True,
                      "context.user._root_admin"),
      FieldPermission('6', ['_records.note'], False, False,
                      "not context.user._root_admin")
      # @todo Not sure how to handle field permissions (though some actions seem to not respect field permissions)?
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('6', 'prepare'),
      arguments={
        'upload_url': ndb.SuperStringProperty(required=True)
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'output.entity': 'entities.6'}),
        auth.DomainPrepare()
        ]
      ),
    Action(
      key=Action.build_key('6', 'create'),
      arguments={
        # Domain
        'domain_name': ndb.SuperStringProperty(required=True),
        'domain_logo': ndb.SuperLocalStructuredImageProperty(blob.Image, required=True)
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        auth.DomainCreate(transactional=True),
        rule.Read(transactional=True),  # @todo Not sure if required, since the entity is just instantiated like in prepare action?
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.6'}),
        callback.Payload(transactional=True, queue = 'callback',
                         static_data = {'action_key': 'install', 'action_model': '57'},
                         dynamic_data = {'key': 'entities.57.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('6', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        auth.DomainRead(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.6'})
        ]
      ),
    Action(
      key=Action.build_key('6', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'primary_contact': ndb.SuperKeyProperty(required=True, kind='0')
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(dynamic_values={'values.6.name': 'input.name', 'values.6.primary_contact': 'input.primary_contact'}),  # @todo Logo will be implemented later.
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.6'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'key': 'entities.6.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('6', 'search'),
      arguments={
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "created", "operator": "desc"}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()}, 
            'state': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()}
            },
          indexes=[
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']], 
                          ['created', ['asc', 'desc']], 
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']], 
                          ['updated', ['asc', 'desc']]]},
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']], 
                          ['updated', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']},
            'created': {'operators': ['asc', 'desc']},
            'updated': {'operators': ['asc', 'desc']}
            },
          ),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        common.Search(),
        auth.DomainSearch(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('6', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.6', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('6', 'suspend'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(static_values={'values.6.state': 'suspended'}),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        rule.Prepare(transactional=True, skip_user_roles=False, strict=False),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.6'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'key': 'entities.6.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('6', 'activate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(static_values={'values.6.state': 'active'}),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        rule.Prepare(transactional=True, skip_user_roles=False, strict=False),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.6'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'key': 'entities.6.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('6', 'sudo'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'state': ndb.SuperStringProperty(required=True, choices=['active', 'suspended', 'su_suspended']),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(dynamic_values={'values.6.state': 'input.state'}),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        rule.Prepare(transactional=True, skip_user_roles=False, strict=False),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message', 'note': 'input.note'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.6'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'key': 'entities.6.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('6', 'log_message'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Write(transactional=True),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message', 'note': 'input.note'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.6'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'key': 'entities.6.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      )
    ]
  
  @property
  def key_namespace(self):
    return self.key.urlsafe()
  
  @property
  def namespace_entity(self):
    return self
