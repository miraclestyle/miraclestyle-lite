# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib

from app import ndb, settings, memcache
from app.srv.event import Action, PluginGroup
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.srv import log as ndb_log
from app.srv import blob as ndb_blob
from app.plugins import common, rule, log, callback, blob, auth


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
    '_records': ndb_log.SuperLocalStructuredRecordProperty('0', repeated=True)
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
            common.Context(),
            auth.UserLoginPrepare(),
            auth.UserIPAddress(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            auth.UserLoginOAuth(login_methods=settings.LOGIN_METHODS),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            auth.UserLoginUpdate(),
            rule.Prepare(skip_user_roles=True, strict=False),  # @todo Should run out of transaction!!!
            rule.Read(),
            log.Write(),
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
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.0'})
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
            common.Context(),
            common.Read(),
            auth.UserUpdate(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            log.Entity(),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.0'}),
            callback.Notify(),
            callback.Exec()
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
            common.Context(),
            common.Prepare(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            common.Search(page_size=settings.SEARCH_PAGE),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Read(),
            common.Set(dynamic_values={'output.entities': 'entities',
                                       'output.search_cursor': 'search_cursor',
                                       'output.search_more': 'search_more'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('0', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            log.Read(page_size=settings.RECORDS_PAGE),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.0',
                                       'output.log_read_cursor': 'log_read_cursor',
                                       'output.log_read_more': 'log_read_more'})
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
            common.Context(),
            common.Read(),
            common.Set(dynamic_values={'values.0.state': 'input.state'}),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            auth.UserSudo()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            log.Entity(dynamic_arguments={'message': 'input.message', 'note': 'input.note'}),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.0'}),
            callback.Notify(),
            callback.Exec()
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
            common.Context(),
            common.Read(),
            common.Set(static_values={'values.0.sessions': []}),
            auth.UserIPAddress(),
            rule.Prepare(skip_user_roles=True,  strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            log.Entity(dynamic_arguments={'ip_address': 'tmp.ip_address'}),
            log.Write(),
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
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            auth.UserReadDomains(),
            common.Set(dynamic_values={'entities': 'tmp.domains'}),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Read(),
            common.Set(dynamic_values={'entities': 'tmp.domain_users'}),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Read(),
            common.Set(dynamic_values={'output.domains': 'tmp.domains', 'output.domain_users': 'tmp.domain_users'})
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
  logo = ndb.SuperLocalStructuredProperty(ndb_blob.Image, '6', required=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_primary_contact_email': ndb.SuperStringProperty(),
    '_records': ndb_log.SuperLocalStructuredRecordProperty('6', repeated=True)
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
            common.Context(),
            common.Prepare(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            blob.URL(gs_bucket_name=settings.COMPANY_LOGO_BUCKET),
            common.Set(dynamic_values={'output.entity': 'entities.6'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'create'),
      arguments={
        # Domain
        'domain_name': ndb.SuperStringProperty(required=True),
        'domain_logo': ndb.SuperLocalStructuredImageProperty(ndb_blob.Image, required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            blob.AlterImage(source='input.domain_logo',
                            destination='input.domain_logo',
                            config={'transform': True, 'width': 240, 'height': 100,
                                    'crop_to_fit': True, 'crop_offset_x': 0.0, 'crop_offset_y': 0.0}),
            auth.DomainCreate(),
            blob.Update(blob_write='input.domain_logo.image'),
            rule.Read(),  # @todo Not sure if required, since the entity is just instantiated like in prepare action?
            common.Set(dynamic_values={'output.entity': 'entities.6'}),
            callback.Payload(queue='callback',
                             static_data={'action_id': 'install', 'action_model': '57'},
                             dynamic_data={'key': 'entities.57.key_urlsafe'}),
            callback.Exec()
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
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            auth.DomainRead(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.6'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'logo': ndb.SuperLocalStructuredImageProperty(ndb_blob.Image),
        'primary_contact': ndb.SuperKeyProperty(required=True, kind='8', validator=auth.primary_contact_validator)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            common.Set(dynamic_values={'values.6.name': 'input.name',
                                       'values.6.primary_contact': 'input.primary_contact',
                                       'values.6.logo': 'input.logo'}),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            common.Set(dynamic_values={'tmp.original_logo': 'entities.6.logo'}),
            rule.Write(),
            common.Set(dynamic_values={'tmp.new_logo': 'entities.6.logo'}),
            blob.AlterImage(source='entities.6.logo',
                            destination='entities.6.logo',
                            config={'transform': True, 'width': 240, 'height': 100,
                                    'crop_to_fit': True, 'crop_offset_x': 0.0, 'crop_offset_y': 0.0}),
            common.Write(),       
            log.Entity(),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.6'}),
            blob.Update(blob_delete='tmp.original_logo.image', blob_write='tmp.new_logo.image'),
            callback.Notify(),
            callback.Exec()
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
            common.Context(),
            common.Prepare(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            common.Search(page_size=settings.SEARCH_PAGE),
            auth.DomainSearch(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Read(),
            common.Set(dynamic_values={'output.entities': 'entities',
                                       'output.search_cursor': 'search_cursor',
                                       'output.search_more': 'search_more'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('6', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            log.Read(page_size=settings.RECORDS_PAGE),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.6',
                                       'output.log_read_cursor': 'log_read_cursor',
                                       'output.log_read_more': 'log_read_more'})
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
            common.Context(),
            common.Read(),
            common.Set(static_values={'values.6.state': 'suspended'}),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            rule.Prepare(skip_user_roles=False, strict=False),  # @todo Should run out of transaction!!!
            log.Entity(dynamic_arguments={'message': 'input.message'}),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.6'}),
            callback.Notify(),
            callback.Exec()
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
            common.Context(),
            common.Read(),
            common.Set(static_values={'values.6.state': 'active'}),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            rule.Prepare(skip_user_roles=False, strict=False),  # @todo Should run out of transaction!!!
            log.Entity(dynamic_arguments={'message': 'input.message'}),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.6'}),
            callback.Notify(),
            callback.Exec()
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
            common.Context(),
            common.Read(),
            common.Set(dynamic_values={'values.6.state': 'input.state'}),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            rule.Prepare(skip_user_roles=True, strict=False),  # @todo Should run out of transaction!!!
            log.Entity(dynamic_arguments={'message': 'input.message', 'note': 'input.note'}),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.6'}),
            callback.Notify(),
            callback.Exec()
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
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            common.Write(),
            log.Entity(dynamic_arguments={'message': 'input.message', 'note': 'input.note'}),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.6'}),
            callback.Notify(),
            callback.Exec()
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
