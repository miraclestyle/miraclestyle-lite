# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import os
import copy

from google.appengine.api import blobstore

from app import ndb, settings, memcache, util
from app.lib import oauth2
from app.srv import event, rule, log, setup, blob, callback, cruds


class OAuth2Error(Exception):
  
  def __init__(self, error):
    self.message = {'oauth2_error' : error}


class Context():
  
  def __init__(self):
    self.user = User.current_user()


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
    '_records': log.SuperLocalStructuredRecordProperty('0', repeated=True)
    }
  
  # 0 login
  # 1 update
  # 2 sudo
  # 3 logout
  # 4 read_domains
  # 5 read records
  # 6 read
  # 7 search
 
  _global_role = rule.GlobalRole(
    permissions=[
      rule.ActionPermission('0', event.Action.build_key('0-0').urlsafe(), True,
                            "context.rule.entity._is_guest or context.rule.entity.state == 'active'"),
      rule.ActionPermission('0', event.Action.build_key('0-1').urlsafe(), True,
                            "context.rule.entity.key == context.auth.user.key and not context.rule.entity._is_guest"),
      rule.ActionPermission('0', event.Action.build_key('0-2').urlsafe(), True, "context.auth.user._root_admin"),
      rule.ActionPermission('0', event.Action.build_key('0-2').urlsafe(), False, "not context.auth.user._root_admin"),
      rule.ActionPermission('0', event.Action.build_key('0-3').urlsafe(), True, "not context.rule.entity._is_guest"),
      rule.ActionPermission('0', event.Action.build_key('0-4').urlsafe(), True, "not context.rule.entity._is_guest"),
      rule.ActionPermission('0', event.Action.build_key('0-5').urlsafe(), True, "context.auth.user._root_admin"),
      rule.ActionPermission('0', event.Action.build_key('0-6').urlsafe(), True,
                            "context.auth.user._root_admin or context.auth.user.key == context.rule.entity.key"),
      rule.ActionPermission('0', event.Action.build_key('0-7').urlsafe(), True, "context.auth.user._root_admin"),
      rule.FieldPermission('0', 'identities', True, True, "True"),  # User can change identities.
      # Expose these fields by default.
      rule.FieldPermission('0', ['created', 'updated', 'state', '_primary_email'], False, True, "True"),
      rule.FieldPermission('0', '_records', True, True, "True"),
      rule.FieldPermission('0', '_records.note', False, False, "not context.auth.user._root_admin"),
      rule.FieldPermission('0', '_records.note', True, True, "context.auth.user._root_admin")
      ]
    )
  
  _actions = {
    'login': event.Action(
      id='0-0',
      arguments={
        'login_method': ndb.SuperStringProperty(required=True, choices=settings.LOGIN_METHODS.keys()),
        'code': ndb.SuperStringProperty(),
        'error': ndb.SuperStringProperty()
        }
      ),
    'update': event.Action(
      id='0-1',
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'primary_email': ndb.SuperStringProperty(),
        'disassociate': ndb.SuperStringProperty()
        }
      ),
    'sudo': event.Action(
      id='0-2',
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'state': ndb.SuperStringProperty(required=True, choices=['active', 'suspended']),
        'message': ndb.SuperStringProperty(required=True),
        'note': ndb.SuperStringProperty()
        }
      ),
    'logout': event.Action(id='0-3', arguments={'csrf': ndb.SuperStringProperty(required=True)}),
    'read_domains': event.Action(id='0-4'),
    'read_records': event.Action(
      id='0-5',
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    'read': event.Action(id='0-6', arguments={'key': ndb.SuperKeyProperty(kind='0', required=True)}),
    'search': event.Action(
      id='0-7',
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
      )
    }
  
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
  
  @classmethod
  def sudo(cls, context):
    """@todo Treba obratiti paznju na to da suspenzija usera ujedno znaci
    i izuzimanje svih negativnih i neutralnih feedbackova koje je user ostavio dok je bio aktivan.
    
    """
    entity_key = context.input.get('key')
    state = context.input.get('state')
    message = context.input.get('message')
    note = context.input.get('note')
    entity = entity_key.get()
    context.rule.entity = entity
    context.rule.skip_user_roles = True
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      values = {'state': state}
      if rule.writable(context, 'state') and state == 'suspended':
        values['sessions'] = []  # Delete sessions.
      rule.write(entity, values)
      entity.put()
      values = {'message': message, 'note': note}  # This is confusing due to the fact that action argument 'message' is required, and if field 'message' should implement field permissions...
      if not rule.writable(context, '_records.note'):
        values.pop('note')
      context.log.entities.append((entity, values))
      log.Engine.run(context)
      context.callback.payloads.append(('notify',
                                        {'action_key': 'initiate',
                                         'action_model': '61',
                                         'caller_entity': entity.key.urlsafe()}))
      callback.Engine.run(context)
      rule.read(entity)
      context.output['entity'] = entity
    
    transaction()
  
  @classmethod
  def update(cls, context):
    entity_key = context.input.get('key')
    primary_email = context.input.get('primary_email')
    disassociate = context.input.get('disassociate')
    entity = cls.current_user()
    if entity_key != entity.key:
      entity = entity_key.get()
    context.rule.entity = entity
    context.rule.skip_user_roles = True
    identities = copy.deepcopy(entity.identities)
    for identity in identities:
      if primary_email:
        identity.primary = False
        if identity.email == primary_email:
          identity.primary = True
      identity.associated = True
      if disassociate:
        if identity.identity in disassociate:
          identity.associated = False
    context.cruds.model = cls
    context.cruds.values = {'identities': identities}
    cruds.Engine.update(context)
  
  @classmethod
  def read_records(cls, context):
    context.rule.skip_user_roles = True
    context.cruds.model = cls
    cruds.Engine.read_records(context)
  
  @classmethod
  def read(cls, context):
    context.rule.skip_user_roles = True
    context.cruds.model = cls
    cruds.Engine.read(context)
  
  @classmethod
  def search(cls, context):
    context.rule.entity = context.auth.user
    context.rule.skip_user_roles = True
    context.cruds.model = cls
    cruds.Engine.search(context)
  
  @classmethod
  def read_domains(cls, context):
    context.rule.entity = context.auth.user
    context.rule.skip_user_roles = True
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    entities = []
    if context.auth.user.domains:
      entities = ndb.get_multi(context.auth.user.domains)
      context.rule.skip_user_roles = False
      
      @ndb.tasklet
      def async(entity):
        if entity:
          # Rule engine cannot run in tasklets because the context.rule.entity gets in wrong places for some reason... which
          # also causes rule engine to not work properly with _action_permissions, this i could not debug because it is impossible to determine what is going on in iterator
          domain_user_key = rule.DomainUser.build_key(context.auth.user.key_id_str, namespace=entity.key_namespace)
          domain_user = yield domain_user_key.get_async()
          entity._domain_user = domain_user
          entity.add_output('_domain_user')
        raise ndb.Return(entity)
      
      @ndb.tasklet
      def helper(entities):
        entities = yield map(async, entities)
        raise ndb.Return(entities)
      
      entities = helper(entities).get_result()
      for entity in entities:
        context.rule.entity = entity
        rule.Engine.run(context)
        context.rule.entity = entity._domain_user
        rule.Engine.run(context)
    context.output['entities'] = entities
  
  @classmethod
  def logout(cls, context):
    entity = cls.current_user()
    context.rule.entity = entity
    context.rule.skip_user_roles = True
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      if not entity._csrf == context.input.get('csrf'):  # We will see what will be done about this, because CSRF protection must be done globally.
        raise rule.ActionDenied(context)
      if entity.sessions:
        entity.sessions = []
      entity.put()
      context.log.entities.append((entity, {'ip_address': os.environ['REMOTE_ADDR']}))
      log.Engine.run(context)
      entity.set_current_user(None, None)
      context.output['entity'] = entity.current_user()
    
    transaction()
  
  @classmethod
  def login(cls, context):
    login_method = context.input.get('login_method')
    error = context.input.get('error')
    code = context.input.get('code')
    current_user = cls.current_user()
    context.rule.entity = current_user
    context.auth.user = current_user
    context.rule.skip_user_roles = True
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    oauth2_cfg = settings.LOGIN_METHODS[login_method]['oauth2']
    client = oauth2.Client(**oauth2_cfg)
    context.output['authorization_url'] = client.get_authorization_code_uri()
    urls = {}
    for urls_login_method, cfg in settings.LOGIN_METHODS.items():
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
      userinfo = oauth2_cfg['userinfo']
      info = client.resource_request(url=userinfo)
      if info and 'email' in info:
        identity = oauth2_cfg['type']
        identity_id = '%s-%s' % (info['id'], identity)
        email = info['email']
        user = cls.query(cls.identities.identity == identity_id).get()
        if not user:
          user = cls.query(cls.emails == email).get()
        if user:
          context.rule.entity = user
          context.auth.user = user
          context.rule.skip_user_roles = True
          rule.Engine.run(context)
          if not rule.executable(context):
            raise rule.ActionDenied(context)
        
        @ndb.transactional(xg=True)
        def transaction(entity):
          if not entity or entity._is_guest:
            entity = cls()
            entity.emails.append(email)
            entity.identities.append(Identity(identity=identity_id, email=email, primary=True))
            entity.state = 'active'
            session = entity.new_session()
            entity.put()
          else:
            if email not in entity.emails:
              entity.emails.append(email)
            used_identity = entity.has_identity(identity_id)
            if not used_identity:
              entity.append(Identity(identity=identity_id, email=email, primary=False))
            else:
              used_identity.associated = True
              if used_identity.email != email:
                used_identity.email = email
            session = entity.new_session()
            entity.put()
          cls.set_current_user(entity, session)
          context.auth.user = entity
          context.log.entities.append((entity, {'ip_address': os.environ['REMOTE_ADDR']}))
          log.Engine.run(context)
          context.rule.entity = entity
          rule.Engine.run(context)
          rule.read(entity)
          context.output.update({'entity': entity,
                                 'authorization_code': entity.generate_authorization_code(session)})
        
        transaction(user)


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
    '_records': log.SuperLocalStructuredRecordProperty('6', repeated=True)
    }
  
  # 0 create
  # 1 suspend
  # 2 activate
  # 3 sudo
  # 4 log message
  # 6 update
  # 7 read
  # 8 prepare
  # 9 read records
  # 10 search
  
  _global_role = rule.GlobalRole(
    permissions=[
      # is_guest check is not needed on other actions because it requires a loaded domain which will be evaluated with roles.
      rule.ActionPermission('6', event.Action.build_key('6-0').urlsafe(), True, "not context.auth.user._is_guest"),
      rule.ActionPermission('6', event.Action.build_key('6-1').urlsafe(), False, "not context.rule.entity.state == 'active'"),
      rule.ActionPermission('6', event.Action.build_key('6-2').urlsafe(), False,
                            "context.rule.entity.state == 'active' or context.rule.entity.state == 'su_suspended'"),
      rule.ActionPermission('6', event.Action.build_key('6-3').urlsafe(), True, "context.auth.user._root_admin"),
      rule.ActionPermission('6', event.Action.build_key('6-3').urlsafe(), False, "not context.auth.user._root_admin"),
      rule.ActionPermission('6', event.Action.build_key('6-4').urlsafe(), False, "not context.rule.entity.state == 'active'"),
      rule.ActionPermission('6', event.Action.build_key('6-6').urlsafe(), False, "not context.rule.entity.state == 'active'"),
      rule.ActionPermission('6', event.Action.build_key('6-7').urlsafe(), True, "context.auth.user._root_admin"),
      rule.ActionPermission('6', event.Action.build_key('6-8').urlsafe(), True, "not context.auth.user._is_guest"),
      rule.ActionPermission('6', event.Action.build_key('6-9').urlsafe(), True, "context.auth.user._root_admin"),
      rule.ActionPermission('6', event.Action.build_key('6-10').urlsafe(), True, "context.auth.user._root_admin"),
      rule.ActionPermission('6', event.Action.build_key('6-10').urlsafe(), False, "not context.auth.user._root_admin"),
      # All fields that are returned by get_fields() have writable and visible set to true upon domain creation.
      rule.FieldPermission('6', '_records.note', False, False, "not context.auth.user._root_admin"),
      rule.FieldPermission('6', '_records.note', False, True, "context.auth.user._root_admin")
      ]
    )
  
  _actions = {
    'create': event.Action(
      id='6-0',
      arguments={
        # Domain
        'domain_name': ndb.SuperStringProperty(required=True),
        'domain_logo': ndb.SuperLocalStructuredImageProperty(blob.Image, required=True)
        }
      ),
    'update': event.Action(
      id='6-6',
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'primary_contact': ndb.SuperKeyProperty(required=True, kind='0')
        }
      ),
    'suspend': event.Action(
      id='6-1',
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True)
        }
      ),
    'activate': event.Action(
      id='6-2',
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True)
        }
      ),
    'sudo': event.Action(
      id='6-3',
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'state': ndb.SuperStringProperty(required=True, choices=['active', 'suspended', 'su_suspended']),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty()
        }
      ),
    'log_message': event.Action(
      id='6-4',
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty()
        }
      ),
    'read': event.Action(id='6-7', arguments={'key': ndb.SuperKeyProperty(kind='6', required=True)}),
    'prepare': event.Action(id='6-8', arguments={'upload_url': ndb.SuperStringProperty(required=True)}),
    'read_records': event.Action(
      id='6-9',
      arguments={
        'key': ndb.SuperKeyProperty(kind='6', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    'search': event.Action(
      id='6-10',
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
      )
    }
  
  @property
  def key_namespace(self):
    return self.key.urlsafe()
  
  @property
  def namespace_entity(self):
    return self
  
  @classmethod
  def search(cls, context):
    context.rule.skip_user_roles = True
    
    @ndb.tasklet
    def async(entity):
      user = yield entity.primary_contact.get_async()
      entity._primary_contact_email = user._primary_email
      raise ndb.Return(entity)
    
    @ndb.tasklet
    def helper(entities):
      entities = yield map(async, entities)
      raise ndb.Return(entities)
    
    def mapper(context, entities):
      return helper(entities).get_result()
    
    context.cruds.search_entities_callback = mapper
    context.cruds.model = cls
    cruds.Engine.search(context)
  
  @classmethod
  def create(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity = cls(state='active', primary_contact=context.auth.user.key)
      context.rule.entity = entity
      context.rule.skip_user_roles = True
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      config_input = context.input.copy()
      domain_logo = config_input.get('domain_logo')
      blob.Manager.used_blobs(domain_logo.image)
      config_input['domain_primary_contact'] = context.auth.user.key
      config = setup.Configuration(parent=context.auth.user.key, configuration_input=config_input, setup='setup_domain', state='active')
      config.put()
      context.callback.payloads.append(('callback', {'action_key': 'install',
                                      'action_model': '57',
                                      'key': config.key.urlsafe()}))
      callback.Engine.run(context)
      rule.read(entity)
      context.output['entity'] = entity
    
    transaction()
  
  @classmethod
  def prepare(cls, context):
    entity = cls(state='active', primary_contact=context.auth.user.key)
    context.rule.entity = entity
    context.rule.skip_user_roles = True
    context.cruds.model = cls
    cruds.Engine.prepare(context)
    context.output['upload_url'] = blobstore.create_upload_url(context.input.get('upload_url'), gs_bucket_name=settings.COMPANY_LOGO_BUCKET)
  
  @classmethod
  def read(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    primary_contact = entity.primary_contact.get_async()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    primary_contact = primary_contact.get_result()
    entity._primary_contact_email = primary_contact._primary_email
    rule.read(entity)
    context.output['entity'] = entity
  
  @classmethod
  def read_records(cls, context):
    context.cruds.model = cls
    cruds.Engine.read_records(context)
  
  @classmethod
  def update(cls, context):
    context.cruds.values = {'name': context.input.get('name'), 'primary_contact': context.input.get('primary_contact')}  # @todo Logo will be implemented later.
    context.cruds.model = cls
    cruds.Engine.update(context)
  
  @classmethod
  def suspend(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      rule.write(entity, {'state': 'suspended'})
      entity.put()
      rule.Engine.run(context)
      context.log.entities.append((entity, {'message': context.input.get('message')}))
      log.Engine.run(context)
      context.callback.payloads.append(('notify',
                                        {'action_key': 'initiate',
                                         'action_model': '61',
                                         'caller_entity': entity.key.urlsafe()}))
      callback.Engine.run(context)
      rule.read(entity)
      context.output['entity'] = entity
    
    transaction()
  
  @classmethod
  def activate(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      rule.write(entity, {'state': 'active'})
      entity.put()
      rule.Engine.run(context)
      context.log.entities.append((entity, {'message': context.input.get('message')}))
      log.Engine.run(context)
      context.callback.payloads.append(('notify',
                                        {'action_key': 'initiate',
                                         'action_model': '61',
                                         'caller_entity': entity.key.urlsafe()}))
      callback.Engine.run(context)
      rule.read(entity)
      context.output['entity'] = entity
    
    transaction()
  
  @classmethod
  def sudo(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      rule.write(entity, {'state': context.input.get('state')})
      entity.put()
      rule.Engine.run(context)
      values = {'message': context.input.get('message'), 'note': context.input.get('note')}
      if not rule.writable(context, '_records.note'):
        values.pop('note')
      context.log.entities.append((entity, values))
      log.Engine.run(context)
      context.callback.payloads.append(('notify',
                                        {'action_key': 'initiate',
                                         'action_model': '61',
                                         'caller_entity': entity.key.urlsafe()}))
      callback.Engine.run(context)
      rule.read(entity)
      context.output['entity'] = entity
    
    transaction()
  
  @classmethod
  def log_message(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      entity.put()  # We update this entity (before logging it) in order to set the value of the 'updated' property to newest date.
      values = {'message': context.input.get('message'), 'note': context.input.get('note')}
      if not rule.writable(context, '_records.note'):
        values.pop('note')
      context.log.entities.append((entity, values))
      log.Engine.run(context)
      context.callback.payloads.append(('notify',
                                        {'action_key': 'initiate',
                                         'action_model': '61',
                                         'caller_entity': entity.key.urlsafe()}))
      callback.Engine.run(context)
      rule.read(entity)
      context.output['entity'] = entity
    
    transaction()
