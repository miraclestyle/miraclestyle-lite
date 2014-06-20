# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib

from app import ndb, settings, memcache
from app.models.base import *
from app.plugins.base import *
from app.plugins import auth


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
  
  _virtual_fields = {
    'ip_address': ndb.SuperStringProperty(),
    '_primary_email': ndb.SuperComputedProperty(lambda self: self.primary_email()),
    '_records': SuperLocalStructuredRecordProperty('0', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('0', Action.build_key('0', 'login'), True,
                       'context.entity._is_guest or context.entity.state == "active"'),
      ActionPermission('0', [Action.build_key('0', 'read'),
                             Action.build_key('0', 'update'),
                             Action.build_key('0', 'logout'),
                             Action.build_key('0', 'read_domains')], True, 'not context.entity._is_guest and context.user.key == context.entity.key'),
      FieldPermission('0', ['created', 'updated', 'state'], False, True,
                      'not context.user._is_guest and context.user.key == context.entity.key'),
      FieldPermission('0', ['identities', 'emails', 'sessions', 'domains', '_primary_email'], True, True,
                      'not context.user._is_guest and context.user.key == context.entity.key'),
      # User is unit of administration, hence root admins need control over it!
      # Root admins can always: read user; search for users (exclusively);
      # read users history (exclusively); perform sudo operations (exclusively).
      ActionPermission('0', [Action.build_key('0', 'read'),
                             Action.build_key('0', 'search'),
                             Action.build_key('0', 'read_records'),
                             Action.build_key('0', 'sudo')], True, 'context.user._root_admin'),
      FieldPermission('0', ['created', 'updated', 'identities', 'emails', 'state', 'sessions', 'domains',
                            'ip_address', '_primary_email', '_records'], None, True, 'context.user._root_admin'),
      FieldPermission('0', ['state'], True, None, 'context.action.key_id_str == "sudo" and context.user._root_admin')
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
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            auth.UserLoginPrepare(),
            auth.UserIPAddress(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec(),
            auth.UserLoginOAuth(login_methods=settings.LOGIN_METHODS),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            auth.UserLoginUpdate(),
            RulePrepare(config={'skip_user_roles': True}),  # @todo Should run out of transaction!!!
            RuleRead(),
            RecordWrite(),
            auth.UserLoginOutput()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('0', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec(),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.0'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('0', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'primary_email': ndb.SuperStringProperty(),
        'disassociate': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            auth.UserUpdate(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(config={'paths': ['entities.0']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.0'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('0', 'search'),
      arguments={
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'created', 'operator': 'desc'}},
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
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec(),
            Search(config={'page': settings.SEARCH_PAGE}),
            RulePrepare(config={'to': 'entities', 'skip_user_roles': True}),
            RuleRead(config={'path': 'entities'}),
            Set(config={'d': {'output.entities': 'entities',
                              'output.search_cursor': 'search_cursor',
                              'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('0', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec(),
            RecordRead(config={'page': settings.RECORDS_PAGE}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.0',
                              'output.search_cursor': 'search_cursor',
                              'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    # @todo Treba obratiti paznju na to da suspenzija usera ujedno znaci
    # i izuzimanje svih negativnih i neutralnih feedbackova koje je user ostavio dok je bio aktivan.
    Action(
      key=Action.build_key('0', 'sudo'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'state': ndb.SuperStringProperty(required=True, choices=['active', 'suspended']),
        'message': ndb.SuperStringProperty(required=True),
        'note': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(config={'d': {'values.0.state': 'input.state'}}),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec(),
            auth.UserSudo()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(config={'paths': ['entities.0'],
                                'd': {'message': 'input.message', 'note': 'input.note'}}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.0'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('0', 'logout'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(config={'s': {'values.0.sessions': []}}),
            auth.UserIPAddress(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(config={'paths': ['entities.0'], 'd': {'ip_address': 'tmp.ip_address'}}),
            auth.UserLogoutOutput()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('0', 'read_domains'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec(),
            auth.UserReadDomains(),
            RulePrepare(config={'to': 'tmp.domains'}),
            RuleRead(config={'path': 'tmp.domains'}),
            RulePrepare(config={'to': 'tmp.domain_users'}),
            RuleRead(config={'path': 'tmp.domain_users'}),
            Set(config={'d': {'output.domains': 'tmp.domains', 'output.domain_users': 'tmp.domain_users'}})
            ]
          )
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
  
  @property
  def _is_cron(self):
    return memcache.temp_memory_get('_current_request_is_cron')
  
  def set_taskqueue(self, is_it):
    return memcache.temp_memory_set('_current_request_is_taskqueue', is_it)
  
  def set_cron(self, is_it):
    return memcache.temp_memory_set('_current_request_is_cron', is_it)
  
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
  def get_system_user(cls):
    user_key = cls.build_key('system')
    user = user_key.get()
    if not user:
      identities = [Identity(email='System', identity='1-0', associated=True, primary=True)]
      user = cls(key=user_key, state='active', emails=['System'], identities=identities)
      user.put()
    return user
  
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
  primary_contact = ndb.SuperKeyProperty('4', kind='8', indexed=False)  # This field is required, and is handeled in update action via argument!
  state = ndb.SuperStringProperty('5', required=True, choices=['active', 'suspended', 'su_suspended'])
  logo = ndb.SuperLocalStructuredProperty(Image, '6', required=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_primary_contact_email': ndb.SuperStringProperty(),
    '_records': SuperLocalStructuredRecordProperty('6', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('6', [Action.build_key('6', 'prepare'),
                             Action.build_key('6', 'create')], True, 'not context.user._is_guest'),
      ActionPermission('6', Action.build_key('6', 'update'), False,
                       'context.entity.state != "active"'),
      ActionPermission('6', Action.build_key('6', 'suspend'), False,
                       'context.entity.state != "active"'),
      ActionPermission('6', Action.build_key('6', 'activate'), False,
                       'context.entity.state == "active" or context.entity.state == "su_suspended"'),
      FieldPermission('6', ['created', 'updated', 'state'], False, None, 'True'),
      FieldPermission('6', ['name', 'primary_contact', 'logo', '_records', '_primary_contact_email'], False, None,
                      'context.entity.state != "active"'),
      FieldPermission('6', ['state'], True, None,
                      '(context.action.key_id_str == "activate" and context.value and context.value.state == "active") or (context.action.key_id_str == "suspend" and context.value and context.value.state == "suspended")'),
      # Domain is unit of administration, hence root admins need control over it!
      # Root admins can always: read domain; search for domains (exclusively);
      # read domain history; perform sudo operations (exclusively); log messages; read _records.note field (exclusively).
      ActionPermission('6', [Action.build_key('6', 'read'),
                             Action.build_key('6', 'search'),
                             Action.build_key('6', 'read_records'),
                             Action.build_key('6', 'sudo'),
                             Action.build_key('6', 'log_message')], True, 'context.user._root_admin'),
      ActionPermission('6', [Action.build_key('6', 'search'),
                             Action.build_key('6', 'sudo')], False, 'not context.user._root_admin'),
      FieldPermission('6', ['created', 'updated', 'name', 'primary_contact', 'state', 'logo', '_records',
                            '_primary_contact_email'], None, True, 'context.user._root_admin'),
      FieldPermission('6', ['_records.note'], True, True,
                      'context.user._root_admin'),
      FieldPermission('6', ['_records.note'], False, False,
                      'not context.user._root_admin'),
      FieldPermission('6', ['state'], True, None,
                      '(context.action.key_id_str == "sudo") and context.user._root_admin and context.value and (context.value.state == "active" or context.value.state == "su_suspended")')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('6', 'prepare'),
      arguments={
        'upload_url': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec(),
            BlobURL(config={'bucket': settings.DOMAIN_LOGO_BUCKET}),
            Set(config={'d': {'output.entity': 'entities.6'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'create'),
      arguments={
        # Domain
        'domain_name': ndb.SuperStringProperty(required=True),
        'domain_logo': ndb.SuperLocalStructuredImageProperty(Image, required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            BlobAlterImage(config={'read': 'input.domain_logo',
                                   'write': 'input.domain_logo',
                                   'config': {'transform': True, 'width': 240, 'height': 100,
                                              'crop_to_fit': True, 'crop_offset_x': 0.0, 'crop_offset_y': 0.0}}),
            auth.DomainCreate(),
            BlobUpdate(config={'write': 'input.domain_logo.image'}),
            RuleRead(),  # @todo Not sure if required, since the entity is just instantiated like in prepare action?
            Set(config={'d': {'output.entity': 'entities.6'}}),
            CallbackExec(config=[('callback',
                                 {'action_id': 'install', 'action_model': '57'},
                                 {'key': 'entities.57.key_urlsafe'})])
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            auth.DomainRead(),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.6'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'logo': ndb.SuperLocalStructuredImageProperty(Image),
        'primary_contact': ndb.SuperKeyProperty(required=True, kind='8', validator=auth.primary_contact_validator)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(config={'d': {'values.6.name': 'input.name',
                              'values.6.primary_contact': 'input.primary_contact',
                              'values.6.logo': 'input.logo'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Set(config={'d': {'tmp.original_logo': 'entities.6.logo'}}),
            RuleWrite(),
            Set(config={'d': {'tmp.new_logo': 'entities.6.logo'}}),
            BlobAlterImage(config={'read': 'entities.6.logo',
                                   'write': 'entities.6.logo',
                                   'config': {'transform': True, 'width': 240, 'height': 100,
                                              'crop_to_fit': True, 'crop_offset_x': 0.0, 'crop_offset_y': 0.0}}),
            Write(),
            RecordWrite(config={'paths': ['entities.6']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.6'}}),
            BlobUpdate(config={'delete': 'tmp.original_logo.image', 'write': 'tmp.new_logo.image'}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'search'),
      arguments={
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'created', 'operator': 'desc'}},
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
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec(),
            Search(config={'page': settings.SEARCH_PAGE}),
            auth.DomainSearch(),
            RulePrepare(config{'to': 'entities', 'skip_user_roles': True}),
            RuleRead(config={'path': 'entities'}),
            Set(config={'d': {'output.entities': 'entities',
                              'output.search_cursor': 'search_cursor',
                              'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RecordRead(config={'page': settings.RECORDS_PAGE}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.6',
                              'output.search_cursor': 'search_cursor',
                              'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'suspend'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(config={'s': {'values.6.state': 'suspended'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RulePrepare(),  # @todo Should run out of transaction!!!
            RecordWrite(config={'paths': ['entities.6'], 'd': {'message': 'input.message'}}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.6'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'activate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(config={'s': {'values.6.state': 'active'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RulePrepare(),  # @todo Should run out of transaction!!!
            RecordWrite(config={'paths': ['entities.6'], 'd': {'message': 'input.message'}}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.6'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
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
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(config={'d': {'values.6.state': 'input.state'}}),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RulePrepare(config={'skip_user_roles': True}),  # @todo Should run out of transaction!!!
            RecordWrite(config={'paths': ['entities.6'], 'd': {'message': 'input.message', 'note': 'input.note'}}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.6'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'log_message'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RecordWrite(config={'paths': ['entities.6'], 'd': {'message': 'input.message', 'note': 'input.note'}}),
            RuleRead(),
            Set(config{'d': {'output.entity': 'entities.6'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      )
    ]
  
  @property
  def key_namespace(self):
    return self.key.urlsafe()
  
  @property
  def namespace_entity(self):
    return self
