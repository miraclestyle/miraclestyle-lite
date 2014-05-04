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
        }
      ),
    Action(
      key=Action.build_key('0', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True)
        }
      ),
    Action(
      key=Action.build_key('0', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'primary_email': ndb.SuperStringProperty(),
        'disassociate': ndb.SuperStringProperty()
        }
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
        }
      ),
    Action(
      key=Action.build_key('0', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    Action(
      key=Action.build_key('0', 'sudo'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'state': ndb.SuperStringProperty(required=True, choices=['active', 'suspended']),
        'message': ndb.SuperStringProperty(required=True),
        'note': ndb.SuperStringProperty()
        }
      ),
    Action(
      key=Action.build_key('0', 'logout'),
      arguments={
        'csrf': ndb.SuperStringProperty(required=True)
        }
      ),
    Action(
      key=Action.build_key('0', 'read_domains'),
      arguments={}
      )
    ]
  
  """@todo Treba obratiti paznju na to da suspenzija usera ujedno znaci
    i izuzimanje svih negativnih i neutralnih feedbackova koje je user ostavio dok je bio aktivan.
    
    """
  _plugins = [
    common.Context(
      subscriptions=[
        Action.build_key('0', 'read'),
        Action.build_key('0', 'update'),
        Action.build_key('0', 'search'),
        Action.build_key('0', 'read_records'),
        Action.build_key('0', 'sudo'),
        Action.build_key('0', 'logout'),
        Action.build_key('0', 'read_domains')
        ]
      ),
    common.Prepare(
      subscriptions=[
        Action.build_key('0', 'search')
        ]
      ),
    common.Read(
      subscriptions=[
        Action.build_key('0', 'read'),
        Action.build_key('0', 'update'),
        Action.build_key('0', 'read_records'),
        Action.build_key('0', 'sudo')
        ]
      ),
    common.Set(
      subscriptions=[
        Action.build_key('0', 'sudo')
        ],
      dynamic_values={'values.0.state': 'input.state'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('0', 'logout'),
        Action.build_key('0', 'read_domains')
        ],
      dynamic_values={'entities.0': 'user'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('0', 'logout')
        ],
      static_values={'values.0.sessions': []}
      ),
    auth.UserLogout(
      subscriptions=[
        Action.build_key('0', 'logout')
        ],
      ),
    auth.UserUpdate(
      subscriptions=[
        Action.build_key('0', 'update')
        ]
      ),
    rule.Prepare(
      subscriptions=[
        Action.build_key('0', 'read'),
        Action.build_key('0', 'update'),
        Action.build_key('0', 'search'),
        Action.build_key('0', 'read_records'),
        Action.build_key('0', 'sudo'),
        Action.build_key('0', 'logout'),
        Action.build_key('0', 'read_domains')
        ],
      skip_user_roles=True,
      strict=False
      ),
    rule.Exec(
      subscriptions=[
        Action.build_key('0', 'read'),
        Action.build_key('0', 'update'),
        Action.build_key('0', 'search'),
        Action.build_key('0', 'read_records'),
        Action.build_key('0', 'sudo'),
        Action.build_key('0', 'logout'),
        Action.build_key('0', 'read_domains')
        ]
      ),
    auth.UserSudo(
      subscriptions=[
        Action.build_key('0', 'sudo')
        ]
      ),
    rule.Write(
      subscriptions=[
        Action.build_key('0', 'update'),
        Action.build_key('0', 'sudo'),
        Action.build_key('0', 'logout')
        ],
      transactional=True
      ),
    common.Write(
      subscriptions=[
        Action.build_key('0', 'update'),
        Action.build_key('0', 'sudo'),
        Action.build_key('0', 'logout')
        ],
      transactional=True
      ),
    log.Entity(
      subscriptions=[
        Action.build_key('0', 'update')
        ],
      transactional=True
      ),
    log.Entity(
      subscriptions=[
        Action.build_key('0', 'sudo')
        ],
      transactional=True,
      dynamic_arguments={'message': 'input.message', 'note': 'input.note'}
      ),
    log.Entity(
      subscriptions=[
        Action.build_key('0', 'logout')
        ],
      transactional=True,
      dynamic_arguments={'ip_address': 'ip_address'}
      ),
    log.Write(
      subscriptions=[
        Action.build_key('0', 'update'),
        Action.build_key('0', 'sudo'),
        Action.build_key('0', 'logout')
        ],
      transactional=True
      ),
    rule.Read(
      subscriptions=[
        Action.build_key('0', 'update'),
        Action.build_key('0', 'sudo')
        ],
      transactional=True
      ),
    common.Set(
      subscriptions=[
        Action.build_key('0', 'update'),
        Action.build_key('0', 'sudo')
        ],
      transactional=True,
      dynamic_values={'output.entity': 'entities.0'}
      ),
    callback.Payload(
      subscriptions=[
        Action.build_key('0', 'update'),
        Action.build_key('0', 'sudo')
        ],
      transactional=True,
      queue = 'notify',
      static_data = {'action_key': 'initiate', 'action_model': '61'},
      dynamic_data = {'caller_entity': 'entities.0.key_urlsafe'}
      ),
    callback.Exec(
      subscriptions=[
        Action.build_key('0', 'update'),
        Action.build_key('0', 'sudo')
        ],
      transactional=True,
      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'}
      ),
    auth.UserLogoutOutput(
      subscriptions=[
        Action.build_key('0', 'logout')
        ],
      transactional=True
      ),
    log.Read(
      subscriptions=[
        Action.build_key('0', 'read_records')
        ]
      ),
    common.Search(
      subscriptions=[
        Action.build_key('0', 'search')
        ]
      ),
    auth.UserReadDomains(
      subscriptions=[
        Action.build_key('0', 'read_domains')
        ]
      ),
    rule.Prepare(
      subscriptions=[
        Action.build_key('0', 'search')
        ],
      skip_user_roles=True,
      strict=False
      ),
    rule.Prepare(
      subscriptions=[
        Action.build_key('0', 'read_domains')
        ],
      skip_user_roles=False,
      strict=False
      ),
    rule.Read(
      subscriptions=[
        Action.build_key('0', 'read'),
        Action.build_key('0', 'search'),
        Action.build_key('0', 'read_records'),
        Action.build_key('0', 'read_domains')
        ]
      ),
    common.Set(
      subscriptions=[
        Action.build_key('0', 'read')
        ],
      dynamic_values={'output.entity': 'entities.0'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('0', 'search')
        ],
      dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'next_cursor', 'output.more': 'more'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('0', 'read_records')
        ],
      dynamic_values={'output.entity': 'entities.0', 'output.next_cursor': 'next_cursor', 'output.more': 'more'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('0', 'read_domains')
        ],
      dynamic_values={'output.entities': 'entities'}
      ),
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
  
  def generate_authorization_code(self, session):
    return '%s|%s' % (self.key.urlsafe(), session.session_id)
  
  def generate_session_id(self):
    session_ids = [session.session_id for session in self.sessions]
    while True:
      random_string = hashlib.md5(util.random_chars(30)).hexdigest()
      if random_string not in session_ids:
        break
    return random_string
  
  def new_session(self):
    session_id = self.generate_session_id()
    session = Session(session_id=session_id)
    self.sessions.append(session)
    return session
  
  def session_by_id(self, session_id):
    for session in self.sessions:
      if session.session_id == session_id:
        return session
    return None
  
  def has_identity(self, identity_id):
    for identity in self.identities:
      if identity.identity == identity_id:
        return identity
    return False
  
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
        }
      ),
    Action(
      key=Action.build_key('6', 'create'),
      arguments={
        # Domain
        'domain_name': ndb.SuperStringProperty(required=True),
        'domain_logo': ndb.SuperLocalStructuredImageProperty(blob.Image, required=True)
        }
      ),
    Action(
      key=Action.build_key('6', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
    Action(
      key=Action.build_key('6', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'primary_contact': ndb.SuperKeyProperty(required=True, kind='0')
        }
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
        }
      ),
    Action(
      key=Action.build_key('6', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    Action(
      key=Action.build_key('6', 'suspend'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True)
        }
      ),
    Action(
      key=Action.build_key('6', 'activate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True)
        }
      ),
    Action(
      key=Action.build_key('6', 'sudo'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'state': ndb.SuperStringProperty(required=True, choices=['active', 'suspended', 'su_suspended']),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty()
        }
      ),
    Action(
      key=Action.build_key('6', 'log_message'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty()
        }
      )
    ]
  
  _plugins = [
    common.Context(
      subscriptions=[
        Action.build_key('6', 'prepare'),
        Action.build_key('6', 'create'),
        Action.build_key('6', 'read'),
        Action.build_key('6', 'update'),
        Action.build_key('6', 'search'),
        Action.build_key('6', 'read_records'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ]
      ),
    common.Prepare(
      subscriptions=[
        Action.build_key('6', 'prepare'),
        Action.build_key('6', 'create'),
        Action.build_key('6', 'search')
        ]
      ),
    common.Read(
      subscriptions=[
        Action.build_key('6', 'read'),
        Action.build_key('6', 'update'),
        Action.build_key('6', 'read_records'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ]
      ),
    common.Set(
      subscriptions=[
        Action.build_key('6', 'update')
        ],
      dynamic_values={'values.6.name': 'input.name', 'values.6.primary_contact': 'input.primary_contact'}  # @todo Logo will be implemented later.
      ),
    common.Set(
      subscriptions=[
        Action.build_key('6', 'suspend')
        ],
      static_values={'values.6.state': 'suspended'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('6', 'activate')
        ],
      static_values={'values.6.state': 'active'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('6', 'sudo')
        ],
      dynamic_values={'values.6.state': 'input.state'}
      ),
    rule.Prepare(
      subscriptions=[
        Action.build_key('6', 'prepare'),
        Action.build_key('6', 'create'),
        Action.build_key('6', 'search')
        ],
      skip_user_roles=True,
      strict=False
      ),
    rule.Prepare(
      subscriptions=[
        Action.build_key('6', 'read'),
        Action.build_key('6', 'update'),
        Action.build_key('6', 'read_records'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ],
      skip_user_roles=False,
      strict=False
      ),
    rule.Exec(
      subscriptions=[
        Action.build_key('6', 'prepare'),
        Action.build_key('6', 'create'),
        Action.build_key('6', 'read'),
        Action.build_key('6', 'update'),
        Action.build_key('6', 'search'),
        Action.build_key('6', 'read_records'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ]
      ),
    auth.DomainCreate(
      subscriptions=[
        Action.build_key('6', 'create')
        ],
      transactional=True
      ),
    rule.Write(
      subscriptions=[
        Action.build_key('6', 'update'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo')
        ],
      transactional=True
      ),
    common.Write(
      subscriptions=[
        Action.build_key('6', 'update'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ],
      transactional=True
      ),
    log.Entity(
      subscriptions=[
        Action.build_key('6', 'update')
        ],
      transactional=True
      ),
    log.Entity(
      subscriptions=[
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate')
        ],
      transactional=True,
      dynamic_arguments={'message': 'input.message'}
      ),
    log.Entity(
      subscriptions=[
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ],
      transactional=True,
      dynamic_arguments={'message': 'input.message', 'note': 'input.note'}
      ),
    log.Write(
      subscriptions=[
        Action.build_key('6', 'update'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ],
      transactional=True
      ),
    rule.Read(
      subscriptions=[
        Action.build_key('6', 'create'),  # @todo Not sure if required, since the entity is just instantiated like in prepare action?
        Action.build_key('6', 'update'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ],
      transactional=True
      ),
    common.Set(
      subscriptions=[
        Action.build_key('6', 'create'),
        Action.build_key('6', 'update'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ],
      transactional=True,
      dynamic_values={'output.entity': 'entities.6'}
      ),
    callback.Payload(
      subscriptions=[
        Action.build_key('6', 'create')
        ],
      transactional=True,
      queue = 'callback',
      static_data = {'action_key': 'install', 'action_model': '57'},
      dynamic_data = {'key': 'entities.57.key_urlsafe'}
      ),
    callback.Payload(
      subscriptions=[
        Action.build_key('6', 'update'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ],
      transactional=True,
      queue = 'notify',
      static_data = {'action_key': 'initiate', 'action_model': '61'},
      dynamic_data = {'caller_entity': 'entities.6.key_urlsafe'}
      ),
    callback.Exec(
      subscriptions=[
        Action.build_key('6', 'create'),
        Action.build_key('6', 'update'),
        Action.build_key('6', 'suspend'),
        Action.build_key('6', 'activate'),
        Action.build_key('6', 'sudo'),
        Action.build_key('6', 'log_message')
        ],
      transactional=True,
      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'}
      ),
    log.Read(
      subscriptions=[
        Action.build_key('6', 'read_records')
        ]
      ),
    common.Search(
      subscriptions=[
        Action.build_key('6', 'search')
        ]
      ),
    auth.DomainSearch(
      subscriptions=[
        Action.build_key('6', 'search')
        ]
      ),
    auth.DomainRead(
      subscriptions=[
        Action.build_key('6', 'read')
        ]
      ),
    rule.Prepare(
      subscriptions=[
        Action.build_key('6', 'search')
        ],
      skip_user_roles=True,
      strict=False
      ),
    rule.Read(
      subscriptions=[
        Action.build_key('6', 'read'),
        Action.build_key('6', 'search'),
        Action.build_key('6', 'read_records')
        ]
      ),
    common.Set(
      subscriptions=[
        Action.build_key('6', 'prepare'),
        Action.build_key('6', 'read')
        ],
      dynamic_values={'output.entity': 'entities.6'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('6', 'search')
        ],
      dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'next_cursor', 'output.more': 'more'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('6', 'read_records')
        ],
      dynamic_values={'output.entity': 'entities.6', 'output.next_cursor': 'next_cursor', 'output.more': 'more'}
      ),
    auth.DomainPrepare(
      subscriptions=[
        Action.build_key('6', 'prepare')
        ]
      )
    ]
  
  @property
  def key_namespace(self):
    return self.key.urlsafe()
  
  @property
  def namespace_entity(self):
    return self
