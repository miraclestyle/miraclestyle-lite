# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import os

from google.appengine.api import blobstore
from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings, memcache, util
from app.lib import oauth2
from app.srv import event, rule, log, setup, blob, callback


class Context():
  
  def __init__(self):
    self.user = User.current_user()


class Session(ndb.BaseModel):
  
  session_id = ndb.SuperStringProperty('1', required=True, indexed=False)
  created = ndb.SuperDateTimeProperty('2', required=True, auto_now_add=True, indexed=False)


class Identity(ndb.BaseModel):
  
  identity = ndb.SuperStringProperty('1', required=True)  # This property stores provider name joined with ID.
  email = ndb.SuperStringProperty('2', required=True)
  associated = ndb.SuperBooleanProperty('3', required=True, default=True)
  primary = ndb.SuperBooleanProperty('4', required=True, default=True)


class User(ndb.BaseExpando):
  
  _kind = 0
  
  _use_memcache = True
  
  identities = ndb.SuperStructuredProperty(Identity, '1', repeated=True)  # Soft limit 100 instances?
  emails = ndb.SuperStringProperty('2', repeated=True)  # Soft limit 100 instances?
  state = ndb.SuperStringProperty('3', required=True, choices=['active', 'suspended'])  # Shall we disable indexing here?
  sessions = ndb.SuperLocalStructuredProperty(Session, '4', repeated=True)  # Soft limit 100 instances?
  domains = ndb.SuperKeyProperty('5', kind='6', repeated=True)  # Soft limit 100 instances? Shall we disable indexing here?
  created = ndb.SuperDateTimeProperty('6', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('7', required=True, auto_now=True)
  
  _default_indexed = False
  
  _expando_fields = {
  
  }
  
  _virtual_fields = {
  
    '_csrf' : ndb.ComputedProperty(lambda self: self.csrf),
    '_is_guest' : ndb.ComputedProperty(lambda self: self.is_guest),
    '_primary_email' : ndb.ComputedProperty(lambda self: self.primary_email),
    '_root_admin' : ndb.ComputedProperty(lambda self: self.root_admin)            
  
  }
 
  _global_role = rule.GlobalRole(permissions=[
                                              rule.ActionPermission('0', event.Action.build_key('0-0').urlsafe(), True, "context.rule.entity._is_guest or context.rule.entity.state == 'active'"),
                                              rule.ActionPermission('0', event.Action.build_key('0-1').urlsafe(), True, "context.rule.entity.key == context.auth.user.key and not context.rule.entity._is_guest"),
                                              rule.ActionPermission('0', event.Action.build_key('0-2').urlsafe(), True, "context.auth.user.root_admin"),
                                              rule.ActionPermission('0', event.Action.build_key('0-2').urlsafe(), False, "not context.auth.user.root_admin"),
                                              rule.ActionPermission('0', event.Action.build_key('0-3').urlsafe(), True, "not context.rule.entity._is_guest"),
                                              rule.ActionPermission('0', event.Action.build_key('0-4').urlsafe(), True, "not context.rule.entity._is_guest"),
                                              rule.ActionPermission('0', event.Action.build_key('0-5').urlsafe(), True, "context.auth.user.root_admin"),
                                              rule.ActionPermission('0', event.Action.build_key('0-6').urlsafe(), True, "context.auth.user.root_admin or context.auth.user.key == context.rule.entity.key"),
                                              rule.ActionPermission('0', event.Action.build_key('0-7').urlsafe(), True, "context.auth.user.root_admin"),
                                              
                                              rule.FieldPermission('0', 'identities', True, True, True, 'True'),  # By default user can manage identities, no problem.
                  
                                              # What about field permission on state property?
                                              ])
  
  _actions = {
              'login': event.Action(id='0-0',
                                    arguments={
                                               'login_method': ndb.SuperStringProperty(required=True, choices=settings.LOGIN_METHODS.keys()),
                                               'code': ndb.SuperStringProperty(),
                                               'error': ndb.SuperStringProperty(),
                                               }),
              'update': event.Action(id='0-1',
                                     arguments={
                                                'key': ndb.SuperKeyProperty(kind='0', required=True),
                                                'primary_email': ndb.SuperStringProperty(),
                                                'disassociate': ndb.SuperStringProperty(),
                                                }),
              'sudo': event.Action(id='0-2',
                                   arguments={
                                              'key': ndb.SuperKeyProperty(kind='0', required=True),
                                              'state': ndb.SuperStringProperty(required=True, choices=['active', 'suspended']),
                                              'message': ndb.SuperStringProperty(required=True),
                                              'note': ndb.SuperStringProperty(required=True),
                                               }),
              'logout': event.Action(id='0-3',
                                     arguments={
                                                'csrf': ndb.SuperStringProperty(required=True),
                                                }),
              'apps': event.Action(id='0-4'),
              'history': event.Action(id='0-5',
                                      arguments={
                                                 'key': ndb.SuperKeyProperty(kind='0', required=True),
                                                 'next_cursor': ndb.SuperStringProperty(),
                                                 }),
              'read': event.Action(id='0-6',
                                   arguments={
                                              'key': ndb.SuperKeyProperty(kind='0', required=True),
                                              }),
              'sudo_search': event.Action(id='0-7',
                                          arguments={
                                                     'next_cursor': ndb.SuperStringProperty(),
                                                     }),}
   
  @property
  def is_taskqueue(self):
    return memcache.temp_memory_get('_current_request_is_taskqueue')
  
  def set_taskqueue(self, is_it):
    return memcache.temp_memory_set('_current_request_is_taskqueue', is_it)
  
  @property
  def root_admin(self):
    return self._primary_email in settings.ROOT_ADMINS
  
  @property
  def primary_email(self):
    if not self.identities:
      return None
    for identity in self.identities:
      if identity.primary == True:
        return identity.email
    return identity.email
  
  @property
  def csrf(self):
    session = self.current_user_session()
    if not session:
      return None
    return hashlib.md5(session.session_id).hexdigest()
  
  @property
  def is_guest(self):
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
      # Fail silently if the authorization code is not set properly, or it is corrupted somehow.
      return
    if not session_id:
      # Fail silently if the session id is not found in the split sequence.
      return
    user = ndb.Key(urlsafe=user_key).get()
    if user:
      session = user.session_by_id(session_id)
      if session:
        cls.set_current_user(user, session)
         
         
  @classmethod
  def sudo(cls, context):
    # @todo Treba obratiti paznju na to da suspenzija usera ujedno znaci
    # i izuzimanje svih negativnih i neutralnih feedbackova koje je user ostavio dok je bio aktivan.
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      state = context.input.get('state')
      message = context.input.get('message')
      note = context.input.get('note')
      entity = entity_key.get()
      context.rule.entity = entity
      rule.Engine.run(context, True)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      if state == 'suspended':
        entity.sessions = []  # Delete sessions.
      entity.state = state
      entity.put()
      context.log.entities.append((entity, {'message': message, 'note': note}))
      log.Engine.run(context)
    
    transaction()
    return context
  
  @classmethod
  def update(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      primary_email = context.input.get('primary_email')
      disassociate = context.input.get('disassociate')
      entity = cls.current_user()
      if entity_key != entity.key:
        entity = entity_key.get()
      context.rule.entity = entity
      rule.Engine.run(context, True)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      if rule.writable(context, 'identities'):  # Checks if identities prop
        for identity in entity.identities:
          if primary_email:
            identity.primary = False
            if identity.email == primary_email:
              identity.primary = True
          identity.associated = True
          if disassociate:
            if identity.identity in disassociate:
              identity.associated = False
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
    
    transaction()
    return context
  
  @classmethod
  def history(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    context.output = log.Record.get_logs(entity, context.input.get('next_cursor'))
    return context
  
  @classmethod
  def read(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    #rule.read(entity)
    
    return context
  
  @classmethod
  def sudo_search(cls, context):
    context.rule.entity = context.auth.user
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    query = cls.query().order(-cls.created)
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    entities, next_cursor, more = query.fetch_page(10, start_cursor=cursor)
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    context.output['entities'] = entities
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
    return context
  
  @classmethod
  def apps(cls, context):
    context.rule.entity = context.auth.user
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    entities = []
    if context.auth.user.domains:
      domains = ndb.get_multi(context.auth.user.domains)
      for domain in domains:
        if domain:
          # Rule engine run on domain.
          context.rule.entity = domain
          rule.Engine.run(context)
          domain_user_key = rule.DomainUser.build_key(context.auth.user.key_id_str, namespace=domain.key.urlsafe())
          domain_user = domain_user_key.get()
          # Rule engine run on domain user as well.
          context.rule.entity = domain_user
          rule.Engine.run(context)
          entities.append({'domain': domain, 'user': domain_user})
    
    context.rule.entity = context.auth.user  # Show permissions for initial entity.
    context.output['entities'] = entities
    return context
  
  @classmethod
  def logout(cls, context):
    entity = cls.current_user()
    context.rule.entity = entity
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      if not entity.csrf == context.input.get('csrf'):
        raise rule.ActionDenied(context)
      if entity.sessions:
        entity.sessions = []
      entity.put()
      context.log.entities.append((entity, {'ip_address': os.environ['REMOTE_ADDR']}))
      log.Engine.run(context)
      entity.set_current_user(None, None)
      context.output['anonymous_user'] = entity.current_user()
    
    transaction()
    return context
  
  @classmethod
  def login(cls, context):
    login_method = context.input.get('login_method')
    error = context.input.get('error')
    code = context.input.get('code')
    current_user = cls.current_user()
    context.rule.entity = current_user
    context.auth.user = current_user
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    context.output['providers'] = settings.LOGIN_METHODS.keys()  # Not sure what is expected in output?
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
      # raise custom exception!!!
      return context.error('oauth2_error', 'rejected_account_access')
    if code:
      client.get_token(code)
      if not client.access_token:
        # raise custom exception!!!
        return context.error('oauth2_error', 'failed_access_token')
      context.output['access_token'] = client.access_token
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
          rule.Engine.run(context, True)
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
          context.output.update({'user': entity,
                                 'authorization_code': entity.generate_authorization_code(session),
                                 'session': session,
                                 })
        
        transaction(user)
    return context


class Domain(ndb.BaseExpando):
  
  _kind = 6
  
  _use_memcache = True
  
  name = ndb.SuperStringProperty('1', required=True)
  primary_contact = ndb.SuperKeyProperty('2', kind=User, required=True, indexed=False)
  state = ndb.SuperStringProperty('3', required=True, choices=['active', 'suspended', 'su_suspended'])
  created = ndb.SuperDateTimeProperty('4', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('5', required=True, auto_now=True)
  
  _default_indexed = False
  
  _expando_fields = {

  }
  
  _global_role = rule.GlobalRole(permissions=[
                                              # is_guest check is not needed on other actions because it requires a loaded domain which will be evaluated with roles.
                                              rule.ActionPermission('6', event.Action.build_key('6-0').urlsafe(), True, "not context.auth.user._is_guest"),
                                              rule.ActionPermission('6', event.Action.build_key('6-1').urlsafe(), False, "not context.rule.entity.state == 'active'"),
                                              rule.ActionPermission('6', event.Action.build_key('6-2').urlsafe(), False, "context.rule.entity.state == 'active' or context.rule.entity.state == 'su_suspended'"),
                                              rule.ActionPermission('6', event.Action.build_key('6-3').urlsafe(), True, "context.auth.user.root_admin"),
                                              rule.ActionPermission('6', event.Action.build_key('6-3').urlsafe(), False, "not context.auth.user.root_admin"),
                                              rule.ActionPermission('6', event.Action.build_key('6-4').urlsafe(), False, "not context.rule.entity.state == 'active'"),
                                              rule.ActionPermission('6', event.Action.build_key('6-6').urlsafe(), False, "not context.rule.entity.state == 'active'"),
                                              rule.ActionPermission('6', event.Action.build_key('6-7').urlsafe(), True, "context.auth.user.root_admin"),
                                              rule.ActionPermission('6', event.Action.build_key('6-8').urlsafe(), True, "not context.auth.user._is_guest"),
                                              rule.ActionPermission('6', event.Action.build_key('6-9').urlsafe(), True, "context.auth.user.root_admin"),
                                              rule.ActionPermission('6', event.Action.build_key('6-10').urlsafe(), True, "context.auth.user.root_admin"),
                                              rule.ActionPermission('6', event.Action.build_key('6-10').urlsafe(), False, "not context.auth.user.root_admin"),
                                              ])
  
  _actions = {
              'create': event.Action(id='6-0',
                                     arguments={
                                                # domain
                                                'domain_name': ndb.SuperStringProperty(required=True),
                                                # company
                                                'company_name': ndb.SuperStringProperty(required=True),
                                                'company_logo': ndb.SuperLocalStructuredImageProperty(blob.Image, required=True),
                                                # company expando
                                                'company_country': ndb.SuperKeyProperty(kind='15'),
                                                'company_region': ndb.SuperKeyProperty(kind='16'),
                                                'company_city': ndb.SuperStringProperty(),
                                                'company_postal_code': ndb.SuperStringProperty(),
                                                'company_street': ndb.SuperStringProperty(),
                                                'company_email': ndb.SuperStringProperty(),
                                                'company_telephone': ndb.SuperStringProperty(),
                                                'company_currency': ndb.SuperKeyProperty(kind='19'),
                                                'company_paypal_email': ndb.SuperStringProperty(),
                                                'company_tracking_id': ndb.SuperStringProperty(),
                                                'company_location_exclusion': ndb.SuperBooleanProperty(),
                                                }),
              'update': event.Action(id='6-6',
                                     arguments={
                                                'key': ndb.SuperKeyProperty(kind='6', required=True),
                                                'name': ndb.SuperStringProperty(required=True),
                                                'primary_contact': ndb.SuperKeyProperty(required=True, kind='0'),
                                                }),
              'suspend': event.Action(id='6-1',
                                      arguments={
                                                 'key': ndb.SuperKeyProperty(kind='6', required=True),
                                                 'message': ndb.SuperTextProperty(required=True),
                                                 }),
              'activate': event.Action(id='6-2',
                                       arguments={
                                                  'key': ndb.SuperKeyProperty(kind='6', required=True),
                                                  'message': ndb.SuperTextProperty(required=True),
                                                  }),
              'sudo': event.Action(id='6-3',
                                   arguments={
                                              'key': ndb.SuperKeyProperty(kind='6', required=True),
                                              'state': ndb.SuperStringProperty(required=True, choices=['active', 'suspended', 'su_suspended']),
                                              'message': ndb.SuperTextProperty(required=True),
                                              'note': ndb.SuperTextProperty(required=True),
                                              }),
              'log_message': event.Action(id='6-4',
                                          arguments={
                                                     'key': ndb.SuperKeyProperty(kind='6', required=True),
                                                     'message': ndb.SuperTextProperty(required=True),
                                                     'note': ndb.SuperTextProperty(required=True),
                                                     }),
              'read': event.Action(id='6-7',
                                   arguments={
                                              'key': ndb.SuperKeyProperty(kind='6', required=True),
                                              }),
              'prepare': event.Action(id='6-8',
                                      arguments={
                                                 'upload_url': ndb.SuperStringProperty(required=True),
                                                 }),
              'history': event.Action(id='6-9',
                                      arguments={
                                                 'key': ndb.SuperKeyProperty(kind='6', required=True),
                                                 'next_cursor': ndb.SuperStringProperty(),
                                                 }),
              'sudo_search': event.Action(id='6-10',
                                          arguments={
                                                     'next_cursor': ndb.SuperStringProperty(),
                                                     }),}
  
  @property
  def key_namespace(self):
    return self.key.urlsafe()
  
  @property
  def namespace_entity(self):
    return self
  
  @classmethod
  def sudo_search(cls, context):
    context.rule.entity = cls()
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    query = cls.query().order(-cls.created)
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    entities, next_cursor, more = query.fetch_page(10, start_cursor=cursor)
    
    @ndb.tasklet
    def async(entity):
      new_entity = entity.__todict__()
      user = yield entity.primary_contact.get_async()
      new_entity['primary_email'] = user._primary_email
      raise ndb.Return(new_entity)
    
    @ndb.tasklet
    def helper(entities):
      entities = yield map(async, entities)
      raise ndb.Return(entities)
    
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    entities = helper(entities).get_result()
    context.output['entities'] = entities
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
    return context
  
  @classmethod
  def create(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity = cls(state='active', primary_contact=context.auth.user.key)
      context.rule.entity = entity
      rule.Engine.run(context, True)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      config_input = context.input.copy()
      company_logo = config_input.get('company_logo')
      blob.Manager.used_blobs(company_logo.image)
      config_input['domain_primary_contact'] = context.auth.user.key
      config = setup.Configuration(parent=context.auth.user.key, configuration_input=config_input, setup='setup_domain', state='active')
      config.put()
      context.callback.inputs.append({
                                      'action_key': 'install',
                                      'action_model': 'srv.setup.Configuration',
                                      'key': config.key.urlsafe(),
                                      })
      callback.Engine.run(context)
    
    transaction()
    return context
  
  @classmethod
  def prepare(cls, context):
    entity = cls(state='active', primary_contact=context.auth.user.key)
    context.rule.entity = entity
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    context.output['upload_url'] = blobstore.create_upload_url(context.input.get('upload_url'), gs_bucket_name=settings.COMPANY_LOGO_BUCKET)
    return context
  
  @classmethod
  def read(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    primary_contact = entity.primary_contact.get_async()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    entity_dict = entity.__todict__()
    primary_contact = primary_contact.get_result()
    entity_dict['primary_contact_email'] = primary_contact._primary_email
    context.output['entity'] = entity_dict
    return context
  
  @classmethod
  def history(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    context.output = log.Record.get_logs(entity, context.input.get('next_cursor'))
    return context
  
  @classmethod
  def update(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      if rule.writable(context, 'name'):
        entity.name = context.input.get('name')
      if rule.writable(context, 'primary_contact'):
        entity.primary_contact = context.input.get('primary_contact')
      entity.put()
      context.log.entities.append((entity,))
      log.Engine.run(context)
    
    transaction()
    return context
  
  @classmethod
  def suspend(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      entity.state = 'suspended'
      entity.put()
      rule.Engine.run(context)
      context.log.entities.append((entity, {'message': context.input.get('message')}))
      log.Engine.run(context)
    
    transaction()
    return context
  
  @classmethod
  def activate(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      entity.state = 'active'
      entity.put()
      rule.Engine.run(context)
      context.log.entities.append((entity, {'message': context.input.get('message')}))
      log.Engine.run(context)
    
    transaction()
    return context
  
  @classmethod
  def sudo(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      entity.state = context.input.get('state')
      entity.put()
      rule.Engine.run(context)
      context.log.entities.append((entity, {'message': context.input.get('message'), 'note': context.input.get('note')}))
      log.Engine.run(context)
    
    transaction()
    return context
  
  @classmethod
  def log_message(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      entity.put()  # We update this entity (before logging it) in order to set the value of the 'updated' property to newest date.
      context.log.entities.append((entity, {'message': context.input.get('message'), 'note': context.input.get('note')}))
      log.Engine.run(context)
    
    transaction()
    return context
