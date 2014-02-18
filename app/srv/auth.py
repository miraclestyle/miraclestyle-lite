# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import hashlib
import os

from app import ndb, settings, memcache, util
from app.srv import event, rule
from app.lib import oauth2
from app.srv import log, setup
  
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
    created = ndb.SuperDateTimeProperty('5', auto_now_add=True)
    updated = ndb.SuperDateTimeProperty('6', auto_now=True)
 
    _default_indexed = False
  
    _expando_fields = {  

    }
    
    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('0', event.Action.build_key('0-0').urlsafe(), True, "context.rule.entity.is_guest or context.rule.entity.state == 'active'"),
                                                rule.ActionPermission('0', event.Action.build_key('0-1').urlsafe(), True, "not context.rule.entity.is_guest"),
                                                rule.ActionPermission('0', event.Action.build_key('0-2').urlsafe(), True, "context.auth.user.root_admin"),
                                                rule.ActionPermission('0', event.Action.build_key('0-2').urlsafe(), False, "not context.auth.user.root_admin"),
                                                rule.ActionPermission('0', event.Action.build_key('0-3').urlsafe(), True, "not context.rule.entity.is_guest"),
                                                rule.ActionPermission('0', event.Action.build_key('0-4').urlsafe(), True, "not context.rule.entity.is_guest"),
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
                                 'primary_email' : ndb.SuperStringProperty(),
                                 'disassociate' : ndb.SuperStringProperty(),
                              }
                             ),
                
       'sudo' : event.Action(id='0-2',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='0', required=True),
                                 'message' : ndb.SuperKeyProperty(required=True),
                                 'state' : ndb.SuperStringProperty(required=True),
                                 'note' : ndb.SuperKeyProperty(required=True)
                              }
                             ),
                
       'logout' : event.Action(id='0-3',
                              arguments={
                                'csrf' : ndb.SuperStringProperty(required=True),
                              }
                             ),
                
       'account_manage' : event.Action(id='0-4',
                              arguments={}
                             )
    }
 
    def __todict__(self):
      
        d = super(User, self).__todict__()
        
        d['csrf'] = self.csrf
        d['is_guest'] = self.is_guest
        d['primary_email'] = self.primary_email
        
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
    def account_manage(cls, context):
        record = log.Record.query(log.Record.action==cls._actions.get('login').key, ancestor=context.auth.user.key).get()
        context.output['registered'] = record.logged
        return context
      
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
            
            context.status(user_to_update)
            
        transaction()
           
        return context
      
    @classmethod
    def update(cls, context):
  
        @ndb.transactional(xg=True)
        def transaction():
        
            current_user = cls.current_user()
            context.rule.entity = current_user
            rule.Engine.run(context, True)
            
            if not rule.executable(context):
               raise rule.ActionDenied(context)
 
            primary_email = context.input.get('primary_email')
            disassociate = context.input.get('disassociate')
 

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
            
            context.output['updated_user'] = current_user
            
        transaction()
           
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
                                            rule.ActionPermission('6', event.Action.build_key('6-5').urlsafe(), True, "not context.auth.user.is_guest"),
                                            rule.ActionPermission('6', event.Action.build_key('6-8').urlsafe(), True, "True"),
                                          ])
    # unique action naming, possible usage is '_kind_id-manage'
    _actions = {
       'create' : event.Action(id='6-0',
                              arguments={
                                 'name' : ndb.SuperStringProperty(required=True),
                               
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
                                 #'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'activate' : event.Action(id='6-2',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 #'note' : ndb.SuperTextProperty(required=True)
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
                
       'list' : event.Action(id='6-5',
                              arguments={
                              }
                             ),
                
       'read' : event.Action(id='6-7',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='6', required=True),
                              }
                             ),
       'prepare' : event.Action(id='6-8',
                              arguments={}
                             ),
    }
 
    @property
    def key_namespace(self):
      return self.key.urlsafe()
    
    @property
    def namespace_entity(self):
      return self
      
    def _unused__todict__(self):
      
      d = super(Domain, self).__todict__()
      
      d['users'] = rule.DomainUser.query(namespace=self.key_namespace).fetch()
      d['roles'] = rule.DomainRole.query(namespace=self.key_namespace).fetch()
      d['logs'] = log.Record.query(ancestor=self.key).fetch()
      
      return d
    
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
       
            context.setup.name = 'create_domain'
            context.setup.input = context.input.copy()
            context.setup.input['user'] = context.auth.user
            setup.Engine.run(context)
           
        transaction()
            
        return context
      
    @classmethod
    def prepare(cls, context):
      
      entity = cls(state='active', primary_contact=context.auth.user.key)
      
      context.rule.entity = entity
      
      rule.Engine.run(context, True)
      
      if not rule.executable(context):
         raise rule.ActionDenied(context)
      
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
               
            context.output['updated_domain'] = entity
           
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
            
           context.status(entity)
           
       transaction()
           
       return context
      
    @classmethod
    def list(cls, context):
      
        context.rule.entity = cls()
      
        rule.Engine.run(context, True)
        
        if not rule.executable(context):
           raise rule.ActionDenied(context)
 
        context.output['domains'] = cls.query().order(-cls.created).fetch()
              
        return context
        