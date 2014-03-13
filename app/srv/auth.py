# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import os
import copy

from google.appengine.api import blobstore
from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings, memcache, util
from app.lib import oauth2
from app.srv import event, rule, log, setup, blob, callback


class Context():
  
  def __init__(self):
    self.user = User.current_user()


class Session(ndb.BaseModel):
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True, indexed=False)
  session_id = ndb.SuperStringProperty('2', required=True, indexed=False)


class Identity(ndb.BaseModel):
  
  identity = ndb.SuperStringProperty('1', required=True)  # This property stores provider name joined with ID.
  email = ndb.SuperStringProperty('2', required=True)
  associated = ndb.SuperBooleanProperty('3', required=True, default=True)
  primary = ndb.SuperBooleanProperty('4', required=True, default=True)


class User(ndb.BaseExpando):
  
  _kind = 0
  
  _use_memcache = True
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  identities = ndb.SuperStructuredProperty(Identity, '3', repeated=True)  # Soft limit 100 instances?
  emails = ndb.SuperStringProperty('4', repeated=True)  # Soft limit 100 instances?
  state = ndb.SuperStringProperty('5', required=True, choices=['active', 'suspended'])  # Shall we disable indexing here?
  sessions = ndb.SuperLocalStructuredProperty(Session, '6', repeated=True)  # Soft limit 100 instances?
  domains = ndb.SuperKeyProperty('7', kind='6', repeated=True)  # Soft limit 100 instances? Shall we disable indexing here?
  
  _default_indexed = False
  
  _expando_fields = {}
  
  _virtual_fields = {
    # By default these are helper properties that operate mainly on 'self' without performing any queries.
    'ip_address': ndb.SuperStringProperty(),
    '_csrf': ndb.ComputedProperty(lambda self: self.csrf()),  # We will need the csrf but it has to be incorporated into security mechanism (http://en.wikipedia.org/wiki/Cross-site_request_forgery).
    '_is_guest': ndb.ComputedProperty(lambda self: self.is_guest()),
    '_primary_email': ndb.ComputedProperty(lambda self: self.primary_email()),
    '_root_admin': ndb.ComputedProperty(lambda self: self.root_admin()),
    '_is_taskqueue': ndb.ComputedProperty(lambda self: self.is_taskqueue()),
    '_records': log.SuperLocalStructuredRecordProperty('0', repeated=True),
    '_records_next_cursor': ndb.SuperStringProperty(),
    '_records_more': ndb.SuperBooleanProperty()
    }
  
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
      rule.FieldPermission('0', 'identities', True, True, 'True'),  # User can change identities.
      # Expose these fields by default.
      rule.FieldPermission('0', ['_csrf', '_is_guest', '_primary_email',
                                 '_root_admin', 'created', 'updated', 'state'], False, True, 'True'),
      rule.FieldPermission('0', '_records', True, True, 'True'),
      rule.FieldPermission('0', '_records.note', False, False, 'not context.auth.user.root_admin'),
      rule.FieldPermission('0', '_records.note', True, True, 'context.auth.user.root_admin')
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
    'apps': event.Action(id='0-4'),
    'read_records': event.Action(
      id='0-5',
      arguments={
        'key': ndb.SuperKeyProperty(kind='0', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    'read': event.Action(id='0-6',arguments={'key': ndb.SuperKeyProperty(kind='0', required=True)}),
    'sudo_search': event.Action(id='0-7', arguments={'next_cursor': ndb.SuperStringProperty()})
    }
  
  def is_taskqueue(self):
    return memcache.temp_memory_get('_current_request_is_taskqueue')
  
  def set_taskqueue(self, is_it):
    return memcache.temp_memory_set('_current_request_is_taskqueue', is_it)
  
  def root_admin(self):
    return self._primary_email in settings.ROOT_ADMINS
  
  def primary_email(self):
    if not self.identities:
      return None
    for identity in self.identities:
      if identity.primary == True:
        return identity.email
    return identity.email
  
  def csrf(self):
    session = self.current_user_session()
    if not session:
      return None
    return hashlib.md5(session.session_id).hexdigest()
  
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
        entity.sessions = []  # Delete sessions. @todo Should we put this into rule.writable (see def logout as well)?
      rule.write(entity, {'state': state})  # @todo Since rule.write doesn't take 'message' and 'note', are field permissions for those two fields respected?
      entity.put()
      context.log.entities.append((entity, {'message': message, 'note': note}))  # Are field permissions for 'message' and 'note' fields respected?
      log.Engine.run(context)
      context.output['entity'] = entity
    
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
      rule.write(entity, {'identities' : identities})
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
      context.output['entity'] = entity
    
    transaction()
    return context
  
  @classmethod
  def read_records(cls, context):
    entity_key = context.input.get('key')
    next_cursor = context.input.get('next_cursor')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    entities, next_cursor, more = log.Record.get_records(entity, next_cursor)
    entity._records = entities
    entity._records_next_cursor = next_cursor
    entity._records_more = more
    rule.read(entity)
    context.output['entity'] = entity
    return context
  
  @classmethod
  def read(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    rule.read(entity)
    context.output['entity'] = entity
    return context
  
  @classmethod
  def sudo_search(cls, context):  # Name of this function will most likely remain sudo_ prefixed (taking search UI into consideration)!
    context.rule.entity = context.auth.user
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    query = cls.query().order(-cls.created)
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    entities, next_cursor, more = query.fetch_page(10, start_cursor=cursor)
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    context.output['entity'] = context.auth.user
    context.output['entities'] = entities
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
    return context
  
  @classmethod
  def apps(cls, context):  # Name of this function is not decided yet.
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
          domain_user = domain_user_key.get()  # These gets have to be done in async!
          # Rule engine run on domain user as well.
          context.rule.entity = domain_user
          rule.Engine.run(context)
          entities.append({'domain': domain, 'user': domain_user})
    
    context.output['entity'] = context.auth.user
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
      if not entity._csrf == context.input.get('csrf'):  # We will see what will be done about this, because CSRF protection must be done globally.
        raise rule.ActionDenied(context)
      if entity.sessions:
        entity.sessions = []  # @todo Not sure if rule.write is needed here (this is logout)?
      entity.put()
      context.log.entities.append((entity, {'ip_address': os.environ['REMOTE_ADDR']}))
      log.Engine.run(context)
      entity.set_current_user(None, None)
      context.output['entity'] = entity.current_user()
    
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
          context.output.update({'entity': entity,
                                 'authorization_code': entity.generate_authorization_code(session)})
        
        transaction(user)
    return context


class Domain(ndb.BaseExpando):
  
  _kind = 6
  
  _use_memcache = True
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = ndb.SuperStringProperty('3', required=True)
  primary_contact = ndb.SuperKeyProperty('4', kind=User, required=True, indexed=False)
  state = ndb.SuperStringProperty('5', required=True, choices=['active', 'suspended', 'su_suspended'])
  
  _default_indexed = False
  
  _expando_fields = {}
  
  _virtual_fields = {
    '_primary_contact_email': ndb.SuperStringProperty(),
    '_records': log.SuperLocalStructuredRecordProperty('6', repeated=True),
    '_records_next_cursor': ndb.SuperStringProperty(),
    '_records_more': ndb.SuperBooleanProperty()
    }
  
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
      rule.FieldPermission('6', '_records.note', False, False, 'not context.auth.user.root_admin'),
      rule.FieldPermission('6', '_records.note', False, True, 'context.auth.user.root_admin')
      ]
    )
  
  _actions = {
    'create': event.Action(
      id='6-0',
      arguments={
        # Domain
        'domain_name': ndb.SuperStringProperty(required=True),
        # Company
        'company_name': ndb.SuperStringProperty(required=True),
        'company_logo': ndb.SuperLocalStructuredImageProperty(blob.Image, required=True),
        # Company Expando
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
        'company_location_exclusion': ndb.SuperBooleanProperty()
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
    'sudo_search': event.Action(id='6-10', arguments={'next_cursor': ndb.SuperStringProperty()})
    }
  
  @property
  def key_namespace(self):
    return self.key.urlsafe()
  
  @property
  def namespace_entity(self):
    return self
  
  @classmethod
  def sudo_search(cls, context):  # Name of this function will most likely remain sudo_ prefixed (taking search UI into consideration)!
    entity = cls()
    context.rule.entity = entity
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    query = cls.query().order(-cls.created)
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    entities, next_cursor, more = query.fetch_page(10, start_cursor=cursor)
    
    @ndb.tasklet
    def async(entity):
      user = yield entity.primary_contact.get_async()
      entity._primary_contact_email = user._primary_email
      raise ndb.Return(entity)
    
    @ndb.tasklet
    def helper(entities):
      entities = yield map(async, entities)
      raise ndb.Return(entities)
    
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    entities = helper(entities).get_result()
    context.output['entity'] = entity
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
      context.callback.inputs.append({'action_key': 'install',
                                      'action_model': '57',
                                      'key': config.key.urlsafe()})
      callback.Engine.run(context)
      context.output['entity'] = entity
    
    transaction()
    return context
  
  @classmethod
  def prepare(cls, context):
    entity = cls(state='active', primary_contact=context.auth.user.key)
    context.rule.entity = entity
    rule.Engine.run(context, True)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    # @todo Not sure if we should put here rule.read?
    context.output['entity'] = entity
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
    primary_contact = primary_contact.get_result()
    entity._primary_contact_email = primary_contact._primary_email
    rule.read(entity)
    context.output['entity'] = entity
    return context
  
  @classmethod
  def read_records(cls, context):
    entity_key = context.input.get('key')
    next_cursor = context.input.get('next_cursor')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    entities, next_cursor, more = log.Record.get_records(entity, next_cursor)
    entity._records = entities
    entity._records_next_cursor = next_cursor
    entity._records_more = more
    rule.read(entity)
    context.output['entity'] = entity
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
      rule.write(entity, {'name': context.input.get('name'),
                          'primary_contact': context.input.get('primary_contact')})
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
      context.output['entity'] = entity
    
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
      rule.write(entity, {'state': 'suspended'})  # @todo Since rule.write doesn't take 'message', are field permissions for that field respected?
      entity.put()
      rule.Engine.run(context)
      context.log.entities.append((entity, {'message': context.input.get('message')}))
      log.Engine.run(context)
      context.output['entity'] = entity
    
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
      rule.write(entity, {'state': 'active'})  # @todo Since rule.write doesn't take 'message', are field permissions for that field respected?
      entity.put()
      rule.Engine.run(context)
      context.log.entities.append((entity, {'message': context.input.get('message')}))
      log.Engine.run(context)
      context.output['entity'] = entity
    
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
      rule.write(entity, {'state': context.input.get('state')})  # @todo Since rule.write doesn't take 'message' and 'note', are field permissions for those two fields respected?
      entity.put()
      rule.Engine.run(context)
      context.log.entities.append((entity, {'message': context.input.get('message'), 'note': context.input.get('note')}))
      log.Engine.run(context)
      context.output['entity'] = entity
    
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
      # @todo Why is rule.write missing here?
      entity.put()  # We update this entity (before logging it) in order to set the value of the 'updated' property to newest date.
      context.log.entities.append((entity, {'message': context.input.get('message'), 'note': context.input.get('note')}))
      log.Engine.run(context)
      context.output['entity'] = entity
    
    transaction()
    return context
