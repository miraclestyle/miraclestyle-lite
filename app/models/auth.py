# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import os

from app import orm, memcache, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.auth import *


class Session(orm.BaseModel):
  
  _kind = 70
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True, indexed=False)
  session_id = orm.SuperStringProperty('2', required=True, indexed=False)


class Identity(orm.BaseModel):
  
  _kind = 64
  
  identity = orm.SuperStringProperty('1', required=True)  # This property stores provider name joined with ID.
  email = orm.SuperStringProperty('2', required=True)
  associated = orm.SuperBooleanProperty('3', required=True, default=True)
  primary = orm.SuperBooleanProperty('4', required=True, default=True)


class User(orm.BaseExpando):
  
  _kind = 0
  
  _use_memcache = True
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  identities = orm.SuperStructuredProperty(Identity, '3', repeated=True)  # Soft limit 100 instances.
  emails = orm.SuperStringProperty('4', repeated=True)  # Soft limit 100 instances.
  state = orm.SuperStringProperty('5', required=True, choices=['active', 'suspended'])  # @todo Shall we disable indexing here?
  sessions = orm.SuperLocalStructuredProperty(Session, '6', repeated=True)  # Soft limit 100 instances.
  domains = orm.SuperKeyProperty('7', kind='6', repeated=True)  # Soft limit 100 instances. @todo Shall we disable indexing here?
  
  _default_indexed = False
  
  _virtual_fields = {
    'ip_address': orm.SuperComputedProperty(lambda self: os.environ.get('REMOTE_ADDR')),
    '_primary_email': orm.SuperComputedProperty(lambda self: self.primary_email()),
    '_records': orm.SuperRecordProperty('0'),
    # these properties are not loaded on every user entity when they are fetched from datastore
    # they should be read individually like so:
    # user._domains.read_async()
    # user._domain_users.read_async()
    # and then you have it
    # for domain in user._domains:
    #   ...
    # for domain_user in user._domain_users:
    #   ...
    '_domains': orm.SuperStorageStructuredProperty('6', autoload=False, storage='reference', repeated=True, updateable=False, deleteable=False,
                                                   storage_config={'callback' : lambda self: orm.get_multi_async([domain_key for domain_key in self.domains])}),
    '_domain_users': orm.SuperStorageStructuredProperty('8', autoload=False, storage='reference', repeated=True, updateable=False, deleteable=False,
                                                        storage_config={'callback' : lambda self: orm.get_multi_async([orm.Key('8', self.key_id_str, namespace=domain_key.urlsafe()) for domain_key in self.domains])})
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('0', orm.Action.build_key('0', 'login'), True,
                           'entity._is_guest or entity._original.state == "active"'),
      orm.ActionPermission('0', [orm.Action.build_key('0', 'read'),
                                 orm.Action.build_key('0', 'update'),
                                 orm.Action.build_key('0', 'logout')], True, 'not entity._is_guest and user.key == entity._original.key'),
      orm.FieldPermission('0', ['created', 'updated', 'state', 'domains', '_domains', '_domain_users'], False, True,
                          'not user._is_guest and user.key == entity._original.key'),
      orm.FieldPermission('0', ['identities', 'emails', 'sessions', '_primary_email'], True, True,
                          'not user._is_guest and user.key == entity._original.key'),
      # User is unit of administration, hence root admins need control over it!
      # Root admins can always: read user; search for users (exclusively);
      # read users history (exclusively); perform sudo operations (exclusively).
      orm.ActionPermission('0', [orm.Action.build_key('0', 'read'),
                                 orm.Action.build_key('0', 'search'),
                                 orm.Action.build_key('0', 'sudo')], True, 'user._root_admin'),
      orm.FieldPermission('0', ['created', 'updated', 'identities', 'emails', 'state', 'sessions', 'domains',
                                'ip_address', '_primary_email', '_records', '_domains', '_domain_users'], None, True, 'user._root_admin'),
      orm.FieldPermission('0', ['state'], True, None, 'action.key_id_str == "sudo" and user._root_admin')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('0', 'login'),
      arguments={
        'login_method': orm.SuperStringProperty(required=True, choices=settings.LOGIN_METHODS.keys()),
        'code': orm.SuperStringProperty(),
        'error': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            UserLoginInit(cfg={'methods': settings.LOGIN_METHODS})
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            UserLoginWrite()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('0', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='0', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_user'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('0', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='0', required=True),
        'primary_email': orm.SuperStringProperty(),
        'disassociate': orm.SuperStringProperty(repeated=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            UserUpdateSet(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_user'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('0', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'created', 'operator': 'desc'}},
          filters={
            'emails': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()}
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
        'search_cursor': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Search(cfg={'page': settings.SEARCH_PAGE}),
            RulePrepare(cfg={'path': '_entities', 'skip_user_roles': True}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    # @todo Treba obratiti paznju na to da suspenzija usera ujedno znaci
    # i izuzimanje svih negativnih i neutralnih feedbackova koje je user ostavio dok je bio aktivan.
    orm.Action(
      key=orm.Action.build_key('0', 'sudo'),
      arguments={
        'key': orm.SuperKeyProperty(kind='0', required=True),
        'state': orm.SuperStringProperty(required=True, choices=['active', 'suspended']),
        'message': orm.SuperStringProperty(required=True),
        'note': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_user.state': 'input.state'}, 's': {'_user.sessions': []}}), # if we reset user sessions on every sudo we will log him out
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),
            Set(cfg={'d': {'output.entity': '_user'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('0', 'logout'),
      arguments={
        'key': orm.SuperKeyProperty(kind='0', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_user.sessions': []}}),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'ip_address': '_user.ip_address'}}),
            UserLogoutOutput()
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
  def _root_admin(self):
    return self._primary_email in settings.ROOT_ADMINS
  
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
  
  def primary_email(self):
    if not self.identities.value:
      return None
    for identity in self.identities.value:
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
    for session in self.sessions.value:
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
    user = orm.Key(urlsafe=user_key).get()
    if user:
      session = user.session_by_id(session_id)
      if session:
        cls.set_current_user(user, session)


class Domain(orm.BaseExpando):
  
  _kind = 6
  
  _use_memcache = True
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = orm.SuperStringProperty('3', required=True)
  primary_contact = orm.SuperKeyProperty('4', kind='8', indexed=False)  # This field is required, and is handeled in update action via argument!
  state = orm.SuperStringProperty('5', required=True, choices=['active', 'suspended', 'su_suspended'])
  logo = SuperImageLocalStructuredProperty(Image, '6', required=True,
                                               process_config={'transform': True, 'width': 240, 'height': 100,
                                                               'crop_to_fit': True, 'crop_offset_x': 0.0,
                                                               'crop_offset_y': 0.0})
  
  _default_indexed = False
  
  _virtual_fields = {
    '_primary_contact_email': orm.SuperReferenceProperty(target_field='primary_contact',
                                                         format_callback=lambda self, value: value._primary_email),
    '_records': orm.SuperRecordProperty('6')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('6', [orm.Action.build_key('6', 'prepare'),
                                 orm.Action.build_key('6', 'create')], True, 'not user._is_guest'),
      orm.ActionPermission('6', orm.Action.build_key('6', 'update'), False,
                           'entity._original.state != "active"'),
      orm.ActionPermission('6', orm.Action.build_key('6', 'suspend'), False,
                           'entity._original.state != "active"'),
      orm.ActionPermission('6', orm.Action.build_key('6', 'activate'), False,
                           'entity._original.state == "active" or entity._original.state == "su_suspended"'),
      orm.FieldPermission('6', ['created', 'updated', 'state'], False, None, 'True'),
      orm.FieldPermission('6', ['name', 'primary_contact', 'logo', '_records', '_primary_contact_email'], False, None,
                          'entity._original.state != "active"'),
      orm.FieldPermission('6', ['state'], True, None,
                          '(action.key_id_str == "activate" and entity.state == "active") or (action.key_id_str == "suspend" and entity.state == "suspended")'),
      # Domain is unit of administration, hence root admins need control over it!
      # Root admins can always: read domain; search for domains (exclusively);
      # read domain history; perform sudo operations (exclusively); log messages; read _records.note field (exclusively).
      orm.ActionPermission('6', [orm.Action.build_key('6', 'read'),
                                 orm.Action.build_key('6', 'search'),
                                 orm.Action.build_key('6', 'sudo'),
                                 orm.Action.build_key('6', 'log_message')], True, 'user._root_admin'),
      orm.ActionPermission('6', [orm.Action.build_key('6', 'search'),
                                 orm.Action.build_key('6', 'sudo')], False, 'not user._root_admin'),
      orm.FieldPermission('6', ['created', 'updated', 'name', 'primary_contact', 'state', 'logo', '_records',
                                '_primary_contact_email'], None, True, 'user._root_admin'),
      orm.FieldPermission('6', ['_records.note'], True, True,
                          'user._root_admin'),
      orm.FieldPermission('6', ['_records.note'], False, False,
                          'not user._root_admin'),
      orm.FieldPermission('6', ['state'], True, None,
                          '(action.key_id_str == "sudo") and user._root_admin and (entity.state == "active" or entity.state == "su_suspended")')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('6', 'prepare'),
      arguments={
        'upload_url': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            BlobURL(cfg={'bucket': settings.DOMAIN_LOGO_BUCKET}),
            Set(cfg={'d': {'output.entity': '_domain',
                           'output.upload_url': '_blob_url'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'create'),
      arguments={
        # Domain
        'domain_name': orm.SuperStringProperty(required=True),
        'domain_logo': SuperImageLocalStructuredProperty(Image, required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            # @todo Embed image uploading & processing plugin here somewhere!
            # ive put it in setup for now, we cant put it here because entity is not created yet
            DomainCreateWrite(),
            Set(cfg={'d': {'output.entity': '_domain'}}),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'install', 'action_model': '57'},
                               {'key': '_config.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'read_arguments': orm.SuperJsonProperty(),
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_domain'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'name': orm.SuperStringProperty(required=True),
        'logo': SuperImageLocalStructuredProperty(Image),
        'primary_contact': orm.SuperKeyProperty(required=True, kind='8', validator=primary_contact_validator)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_domain.name': 'input.name',
                           '_domain.primary_contact': 'input.primary_contact',
                           '_domain.logo': 'input.logo'}}), # if we do this then input.logo will set domain.logo to be none!
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            # @todo Embed image uploading & processing plugin here somewhere!
            # ...
            ProcessImages(),
            Write(),
            Set(cfg={'d': {'output.entity': '_domain'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'created', 'operator': 'desc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()}
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
        'search_cursor': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Search(cfg={'page': settings.SEARCH_PAGE}),
            RulePrepare(cfg={'path': '_entities', 'skip_user_roles': True}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'suspend'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'message': orm.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_domain.state': 'suspended'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            RulePrepare(),  # @todo Should run out of transaction!!!
            Set(cfg={'d': {'output.entity': '_domain'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'activate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'message': orm.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_domain.state': 'active'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            RulePrepare(),  # @todo Should run out of transaction!!!
            Set(cfg={'d': {'output.entity': '_domain'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'sudo'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'state': orm.SuperStringProperty(required=True, choices=['active', 'suspended', 'su_suspended']),
        'message': orm.SuperTextProperty(required=True),
        'note': orm.SuperTextProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_domain.state': 'input.state'}}),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),
            RulePrepare(cfg={'skip_user_roles': True}),  # @todo Should run out of transaction!!!
            Set(cfg={'d': {'output.entity': '_domain'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'log_message'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'message': orm.SuperTextProperty(required=True),
        'note': orm.SuperTextProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),
            Set(cfg={'d': {'output.entity': '_domain'}}),
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
