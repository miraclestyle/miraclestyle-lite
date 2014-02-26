# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
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
    
      session_id = ndb.SuperStringProperty('1', indexed=False)
      updated = ndb.SuperDateTimeProperty('2', auto_now_add=True, indexed=False)
 
     
class Identity(ndb.BaseModel):
 
    # StructuredProperty model
    identity = ndb.SuperStringProperty('1', required=True)# spojen je i provider name sa id-jem
    email = ndb.SuperStringProperty('2', required=True)
    associated = ndb.SuperBooleanProperty('3', default=True)
    primary = ndb.SuperBooleanProperty('4', default=True)
 
class User(ndb.BaseExpando):
    
    _kind = 0
 
    _use_memcache = True
    
    identities = ndb.SuperStructuredProperty(Identity, '1', repeated=True)# soft limit 100x
    emails = ndb.SuperStringProperty('2', repeated=True)# soft limit 100x
    state = ndb.SuperStringProperty('3', required=True)
    sessions = ndb.SuperLocalStructuredProperty(Session, '4', repeated=True)
    domains = ndb.SuperKeyProperty('5', kind='6', repeated=True)
    created = ndb.SuperDateTimeProperty('6', auto_now_add=True)
    updated = ndb.SuperDateTimeProperty('7', auto_now=True)
 
    _default_indexed = False
  
    _expando_fields = {  

    }
    
    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('0', event.Action.build_key('0-0').urlsafe(), True, "context.rule.entity.is_guest or context.rule.entity.state == 'active'"),
                                                rule.ActionPermission('0', event.Action.build_key('0-1').urlsafe(), True, "context.rule.entity.key == context.auth.user.key and not context.rule.entity.is_guest"),
                                                
                                                rule.ActionPermission('0', event.Action.build_key('0-2').urlsafe(), True, "context.auth.user.root_admin"),
                                                rule.ActionPermission('0', event.Action.build_key('0-2').urlsafe(), False, "not context.auth.user.root_admin"),
                                                
                                                rule.ActionPermission('0', event.Action.build_key('0-3').urlsafe(), True, "not context.rule.entity.is_guest"),
                                                rule.ActionPermission('0', event.Action.build_key('0-4').urlsafe(), True, "not context.rule.entity.is_guest"),
                                                
                                                rule.ActionPermission('0', event.Action.build_key('0-5').urlsafe(), True, "context.auth.user.root_admin"),
                                                rule.ActionPermission('0', event.Action.build_key('0-6').urlsafe(), True, "context.auth.user.root_admin or context.auth.user.key == context.rule.entity.key"),

                                                rule.ActionPermission('0', event.Action.build_key('0-7').urlsafe(), True, "context.auth.user.root_admin"),
                                                
                                                rule.FieldPermission('0', 'identities', True, True, True, 'context.auth.user.key == context.rule.entity.key') # by default user can manage identities no problem
                                               
                                               ])
    
    _actions = {
       'login' : event.Action(id='0-0',
                              arguments={
                                 'login_method' : ndb.SuperStringProperty(required=True),
                                 'code' : ndb.SuperStringProperty(),
                                 'error' : ndb.SuperStringProperty()
                              }
                             ),
                
       'update' : event.Action(id='0-1',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='0', required=True),
                                 'primary_email' : ndb.SuperStringProperty(),
                                 'disassociate' : ndb.SuperStringProperty(),
                              }
                             ),
                
       'sudo' : event.Action(id='0-2',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='0', required=True),
                                 'message' : ndb.SuperStringProperty(required=True),
                                 'state' : ndb.SuperStringProperty(required=True, choices=['active', 'suspended']),
                                 'note' : ndb.SuperStringProperty(required=True)
                              }
                             ),
                
       'logout' : event.Action(id='0-3',
                              arguments={
                                'csrf' : ndb.SuperStringProperty(required=True),
                              }
                             ),
                
       'apps' : event.Action(id='0-4'),
                
       'history' : event.Action(id='0-5',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='0', required=True),
                                 'next_cursor' : ndb.SuperStringProperty()
                              }
                             ),
                
       'read' : event.Action(id='0-6',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='0', required=True),
                              }
                             ),
                
       'sudo_search' : event.Action(id='0-7', 
                                    arguments={
                                       'next_cursor' : ndb.SuperStringProperty()
                                    }),                
                
    }
 
    def __todict__(self):
      
        d = super(User, self).__todict__()
        
        d['csrf'] = self.csrf
        d['is_guest'] = self.is_guest
        d['primary_email'] = self.primary_email
        d['root_admin'] = self.root_admin
        
        return d 
    
    @property
    def is_taskqueue(self):
       return memcache.temp_memory_get('_current_request_is_taskqueue')
     
    def set_taskqueue(self, is_it):
       return memcache.temp_memory_set('_current_request_is_taskqueue', is_it)
    
    @property
    def root_admin(self):
       return self.primary_email in settings.ROOT_ADMINS
    
    @property
    def primary_email(self):
        if not self.identities:
           return None
        for i in self.identities:
            if i.primary == True:
               return i.email   
        return i.email
    
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
    
    def generate_authorization_code(self, session):
        return '%s|%s' % (self.key.urlsafe(), session.session_id)
    
    def new_session(self):
        session_id = self.generate_session_id()
        session = Session(session_id=session_id)
        self.sessions.append(session)
        
        return session
  
    def session_by_id(self, sid):
        for s in self.sessions:
            if s.session_id == sid:
               return s
        return None
    
    def generate_session_id(self):
        sids = [s.session_id for s in self.sessions]
        while True:
              random_str = hashlib.md5(util.random_chars(30)).hexdigest()
              if random_str not in sids:
                  break
        return random_str
    
    @classmethod
    def current_user_session(cls):
        return memcache.temp_memory_get('_current_user_session')
    
    @classmethod
    def login_from_authorization_code(cls, auth):
 
        try:
           user_key, session_id = auth.split('|')
        except:
           # fail silently if the authorization code is not set properly, or its corrupted somehow
           return
        
        if not session_id:
           # fail silently if the session id is not found in the split sequence
           return
        
        user = ndb.Key(urlsafe=user_key).get()
        if user:
           session = user.session_by_id(session_id)
           if session:
              cls.set_current_user(user, session)
               
    def has_identity(self, identity_id):
        for i in self.identities:
            if i.identity == identity_id:
               return i
        return False
      
    @classmethod
    def sudo(cls, context):
      
        # @todo Treba obratiti paznju na to da suspenzija usera ujedno znaci i izuzimanje svih negativnih i neutralnih feedbackova
        # koje je user ostavio dok je bio aktivan.
  
        @ndb.transactional(xg=True)
        def transaction():
          
            user_to_update_key = context.input.get('key')
            message = context.input.get('message')
            note = context.input.get('note')
        
            user_to_update = user_to_update_key.get()
            context.rule.entity = user_to_update
            rule.Engine.run(context, True)
            
            if not rule.executable(context):
               raise rule.ActionDenied(context)
             
            new_state = context.input.get('state')
            
            if new_state not in ('active', 'suspended'):
             # raise custom exception!!!
              return context.error('state', 'invalid_state')
 
            
            if user_to_update.state == 'active':
               new_state = 'suspended'
               user_to_update.sessions = [] # delete sessions

            user_to_update.state = new_state
            user_to_update.put()
            
            context.log.entities.append((user_to_update, {'message' : message, 'note' : note}))
            log.Engine.run(context)
 
        transaction()
           
        return context
      
    @classmethod
    def update(cls, context):
  
        @ndb.transactional(xg=True)
        def transaction():
        
            current_user = cls.current_user()
            
            entity_key = context.input.get('key')
            
            if entity_key != current_user.key:
               current_user = entity_key.get()
            
            context.rule.entity = current_user
            rule.Engine.run(context, True)
            
            if not rule.executable(context):
               raise rule.ActionDenied(context)
 
            primary_email = context.input.get('primary_email')
            disassociate = context.input.get('disassociate')
            
            if rule.writable(context, 'identities'): # checks if identities prop is writable?
              for identity in current_user.identities:
                  if primary_email:
                      identity.primary = False
                      if identity.email == primary_email:
                         identity.primary = True
                         
                  identity.associated = True
                   
                  if disassociate:  
                      if identity.identity in disassociate:
                         identity.associated = False
    
            current_user.put()
            
            context.log.entities.append((current_user, ))
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
       
      context.output['entities'] = entities
      context.output['next_cursor'] = next_cursor.urlsafe()
      context.output['more'] = more
       
      return context
 
      
    @classmethod
    def apps(cls, context):
 
        context.rule.entity = context.auth.user
      
        rule.Engine.run(context, True)
        
        if not rule.executable(context):
           raise rule.ActionDenied(context)
 
        domains = ndb.get_multi(context.auth.user.domains)
        entities = []
        
        for domain in domains:
          
            # rule engine run on domain
            context.rule.entity = domain
            rule.Engine.run(context)
            
            domain_user_key = rule.DomainUser.build_key(context.auth.user.key_id_str, namespace=domain.key.urlsafe())
            domain_user = domain_user_key.get()
            
            # rule engine on domain user as well...
            
            context.rule.entity = domain_user
            rule.Engine.run(context)
    
            entities.append({'domain' : domain, 'user' : domain_user})
            
        context.rule.entity = context.auth.user # show perms for initial entity
 
        context.output['entities'] = entities
              
        return context
  
    
    @classmethod  
    def logout(cls, context):
 
        current_user = cls.current_user()
        context.rule.entity = current_user
        rule.Engine.run(context, True)
       
        if not rule.executable(context):
           raise rule.ActionDenied(context)
        
        @ndb.transactional(xg=True)
        def transaction():

            if not current_user.csrf == context.input.get('csrf'):
               raise rule.ActionDenied(context)
         
            if current_user.sessions:
               current_user.sessions = []
 
            current_user.put()
            
            context.log.entities.append((current_user, {'ip_address' : os.environ['REMOTE_ADDR']}))
            
            log.Engine.run(context)
            
            current_user.set_current_user(None, None)
            context.output['anonymous_user'] = current_user.current_user()
 
        
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
        
        if login_method not in settings.LOGIN_METHODS:
          # raise custom exception!!!
           context.error('login_method', 'not_allowed')
        else:
           context.output['providers'] = settings.LOGIN_METHODS
           
           cfg = getattr(settings, '%s_OAUTH2' % login_method.upper())
           client = oauth2.Client(**cfg)
           
           context.output['authorization_url'] = client.get_authorization_code_uri()
           
           urls = {}
           
           for label,key in settings.LOGIN_METHODS.items():
               get_cfg = getattr(settings, '%s_OAUTH2' % label.upper())
               generated_client = oauth2.Client(**get_cfg)
               urls[key] = generated_client.get_authorization_code_uri()
           
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
              
              userinfo = getattr(settings, '%s_OAUTH2_USERINFO' % login_method.upper())
              info = client.resource_request(url=userinfo)
              
              if info and 'email' in info:
                
                  identity = settings.LOGIN_METHODS.get(login_method)
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
                  def transaction(user):
                    
                     if not user or user.is_guest:
                       
                        user = cls()
                        user.emails.append(email)
                        user.identities.append(Identity(identity=identity_id, email=email, primary=True))
                        user.state = 'active'
                        session = user.new_session()
                        
                        user.put()
                          
                     else:
                       
                       if email not in user.emails:
                          user.emails.append(email)
                          
                       used_identity = user.has_identity(identity_id)
                       
                       if not used_identity:
                          user.append(Identity(identity=identity_id, email=email, primary=False))
                       else:
                          used_identity.associated = True
                          if used_identity.email != email:
                             used_identity.email = email
                       
                       session = user.new_session()   
                       user.put()
                         
                     cls.set_current_user(user, session)
                     context.auth.user = user
                     
                     context.log.entities.append((user, {'ip_address' : os.environ['REMOTE_ADDR']}))
                     log.Engine.run(context)
                      
                     context.output.update({'user' : user,
                                            'authorization_code' : user.generate_authorization_code(session),
                                            'session' : session
                                           })
                  transaction(user)
               
        return context
      
class Domain(ndb.BaseExpando):
    
    # domain will use in-memory cache and memcache
     
    _use_memcache = True
    
    _kind = 6
    
    # root
    # composite index: ancestor:no - state,name
    name = ndb.SuperStringProperty('1', required=True)
    primary_contact = ndb.SuperKeyProperty('2', kind=User, required=True, indexed=False)
    updated = ndb.SuperDateTimeProperty('3', auto_now=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True)
    state = ndb.SuperStringProperty('5', required=True)
    
    _default_indexed = False
    
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('6', event.Action.build_key('6-0').urlsafe(), True, "not context.auth.user.is_guest"),
                                            rule.ActionPermission('6', event.Action.build_key('6-6').urlsafe(), False, "not context.rule.entity.state == 'active'"),
                                            rule.ActionPermission('6', event.Action.build_key('6-1').urlsafe(), False, "not context.rule.entity.state == 'active'"),
                                            rule.ActionPermission('6', event.Action.build_key('6-2').urlsafe(), False, "context.rule.entity.state == 'active' or context.rule.entity.state == 'su_suspended'"),
                                            rule.ActionPermission('6', event.Action.build_key('6-3').urlsafe(), True, "context.auth.user.root_admin"),
                                            rule.ActionPermission('6', event.Action.build_key('6-3').urlsafe(), False, "not context.auth.user.root_admin"),
                                            rule.ActionPermission('6', event.Action.build_key('6-4').urlsafe(), False, "not context.rule.entity.state == 'active'"),
                                            rule.ActionPermission('6', event.Action.build_key('6-8').urlsafe(), True, "not context.auth.user.is_guest"),
                                            
                                            rule.ActionPermission('6', event.Action.build_key('6-7').urlsafe(), True, "context.auth.user.root_admin"),
                                            rule.ActionPermission('6', event.Action.build_key('6-9').urlsafe(), True, "context.auth.user.root_admin"),
                                            rule.ActionPermission('6', event.Action.build_key('6-10').urlsafe(), True, "context.auth.user.root_admin"),
                                            rule.ActionPermission('6', event.Action.build_key('6-10').urlsafe(), False, "not context.auth.user.root_admin"),
                                            
                                            
                                            # for basic checks it goes two field permissions per field, usually.
                                            rule.FieldPermission('6', 'name', True, True, True, "context.rule.entity.state == 'active'"), #  these might need context.rule.entity.state == 'active' and inversion?
                                            rule.FieldPermission('6', 'name', False, True, True, "not context.rule.entity.state == 'active'"), 
                                            
                                            rule.FieldPermission('6', 'primary_contact', True, True, True, "context.rule.entity.state == 'active'"), # these might need context.rule.entity == 'active' and inversion?
                                            rule.FieldPermission('6', 'primary_contact', False, True, True, "not context.rule.entity.state == 'active'")
                                            
                                            ])
    # unique action naming, possible usage is '_kind_id-manage'
    _actions = {
       'create' : event.Action(id='6-0',
                              arguments={
                                 
                                 # domain
                                 'domain_name' : ndb.SuperStringProperty(required=True),
                                 
                                 # company
                                 'company_name' : ndb.SuperStringProperty(required=True),
                                 'company_logo' : ndb.SuperLocalStructuredImageProperty(blob.Image, required=True),
                
                                 # company expando
                                 'company_country' : ndb.SuperKeyProperty(kind='15'),
                                 'company_region' : ndb.SuperKeyProperty(kind='16'),
                                 'company_city' : ndb.SuperStringProperty(),
                                 'company_postal_code' : ndb.SuperStringProperty(),
                                 'company_street' : ndb.SuperStringProperty(),
                                 'company_email' : ndb.SuperStringProperty(),
                                 'company_telephone' : ndb.SuperStringProperty(),
                                 'company_currency' : ndb.SuperKeyProperty(kind='19'),
                                 'company_paypal_email' : ndb.SuperStringProperty(),
                                 'company_tracking_id' : ndb.SuperStringProperty(),
                                 'company_location_exclusion' : ndb.SuperBooleanProperty(),
                                                             
                              }
                             ),
                
       'update' : event.Action(id='6-6',
                              arguments={
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'key' : ndb.SuperKeyProperty(kind='6', required=True),
                              }
                             ),
                
       'suspend' : event.Action(id='6-1',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                   
                              }
                             ),
                
       'activate' : event.Action(id='6-2',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                
                              }
                             ),
                
       'sudo' : event.Action(id='6-3',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'state' : ndb.SuperStringProperty(required=True, choices=('active', 'suspended', 'su_suspended')),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'log_message' : event.Action(id='6-4',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True),
                              }
                             ),
 
                
       'read' : event.Action(id='6-7',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='6', required=True),
                              }
                             ),
       'prepare' : event.Action(id='6-8',
                              arguments={
                                 'upload_url' : ndb.SuperStringProperty(required=True)           
                              }
                             ),
       'history' : event.Action(id='6-9',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'next_cursor' : ndb.SuperStringProperty()
                              }
                             ),
       'sudo_search' : event.Action(id='6-10', 
                                    arguments={
                                       'next_cursor' : ndb.SuperStringProperty()
                                    }),       
    }
 
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
      def _async(entity):
      
        new_entity = entity.__todict__()
        
        user = yield entity.primary_contact.get_async()
         
        new_entity['primary_email'] = user.primary_email
 
        raise ndb.Return(new_entity)
      
      @ndb.tasklet
      def helper(entities):
        
          entities = yield map(_async, entities)
        
          raise ndb.Return(entities)
        
      entities = helper(entities).get_result()
       
      context.output['entities'] = entities
      context.output['next_cursor'] = next_cursor.urlsafe()
      context.output['more'] = more
       
      return context
  
    @classmethod
    def create(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
          
            entity = cls(state='active', primary_contact=context.auth.user.key)
           
            context.rule.entity = entity
            
            # no need for role check because the domain is not created
            rule.Engine.run(context, True)
 
            if not rule.executable(context):
               raise rule.ActionDenied(context)
 
            # context setup variables
            config_input = context.input.copy()
            
            company_logo = config_input.get('company_logo')
            
            blob.Manager.used_blobs(company_logo.image)
            
            config_input['domain_primary_contact'] = context.auth.user.key
            
            config = setup.Configuration(parent=context.auth.user.key, configuration_input=config_input, setup='setup_domain', state='active')
            config.put()
            
            context.callback.inputs.append({'action_key' : 'setup_domain',
                                            'configuration_key' : config.key.urlsafe()})
            
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
      
      context.rule.entity = entity
      
      rule.Engine.run(context)
      
      if not rule.executable(context):
         raise rule.ActionDenied(context)
 
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
                
            primary_contact = context.input.get('primary_contact')
            
            if not primary_contact:
               primary_contact = context.auth.user.key
             
            entity.name = context.input.get('name')
            entity.primary_contact = primary_contact
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
            
            context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
            log.Engine.run(context)
             
            context.output['updated_domain'] = entity

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
           
           context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
           log.Engine.run(context)
            
           context.output['updated_domain'] = entity
           
       transaction()
           
       return context
    
    # Ova akcija suspenduje ili aktivira domenu. Ovde cemo dalje opisati posledice suspenzije
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
           
           context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
           log.Engine.run(context)
            
           context.output['updated_domain'] = entity
 
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
            
           entity.put() # ref project-documentation.py #L-244

           context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
           log.Engine.run(context)
 
       transaction()
           
       return context