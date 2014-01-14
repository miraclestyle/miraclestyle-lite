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
from app.srv import log
  
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
 
    _default_indexed = False
  
    _expando_fields = {  
      'roles' : ndb.SuperKeyProperty('5', kind='13', repeated=True, indexed=False)
    }
    
    _global_role = None
    
    _actions = {
       'login' : event.Action(id='login',
                              arguments={
                                 'login_method' : ndb.SuperStringProperty(required=True),
                                 'code' : ndb.SuperStringProperty(),
                                 'error' : ndb.SuperStringProperty()
                              }
                             ),
                
       'logout' : event.Action(id='logout',
                              arguments={
                                'code' : ndb.SuperStringProperty(required=True),
                              }
                             )
    }
 
    def __todict__(self):
      
        d = super(User, self).__todict__()
        
        d['logout_code'] = self.logout_code
        d['is_guest'] = self.is_guest
        
        return d 
    
    @property
    def primary_email(self):
        for i in self.identities:
            if i.primary == True:
               return i.email
           
        return i.email
    
    @property
    def logout_code(self):
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
               return True
        return False
    
    @classmethod  
    def logout(cls, args):
          
        action = cls._actions.get('logout')
        context = action.process(args)
        
        if not context.has_error():
          
          current_user = cls.current_user()
          context.rule.entity = current_user
          rule.Engine.run(context, True)
          
          if not rule.executable(context):
             return context.not_authorized()
          
          @ndb.transactional(xg=True)
          def transaction():
               
              if current_user.is_guest:
                 return context.error('login', 'already_logged_out')
             
              if not current_user.logout_code == context.event._args.get('code'):
                 return context.error('login', 'invalid_code')
           
              if current_user.sessions:
                 current_user.sessions = []
   
              context.log.entities.append((current_user, {'ip_address' : os.environ['REMOTE_ADDR']}))
              
              log.Engine.run(context)
              
              current_user.put()
              
              current_user.set_current_user(None, None)
              
              context.status('logged_out')
          
          try:
              transaction()
          except Exception as e:
              context.transaction_error(e)
              
        return context
     
    @classmethod
    def login(cls, args):
        
        action = cls._actions.get('login')
        context = action.process(args)
    
        if not context.has_error():
 
           login_method = context.event._args.get('login_method')
           error = context.event._args.get('error')
           code = context.event._args.get('code')
           current_user = cls.current_user()
           
           if not current_user.is_guest:
             
             context.rule.entity = current_user
             context.auth.user = current_user
             rule.Engine.run(context, True)
             
             if not rule.executable(context):
                return context.not_authorized()
           
           if login_method not in settings.LOGIN_METHODS:
              context.error('login_method', 'not_allowed')
           else:
              context.response['providers'] = settings.LOGIN_METHODS
              
              cfg = getattr(settings, '%s_OAUTH2' % login_method.upper())
              client = oauth2.Client(**cfg)
              
              context.response['authorization_url'] = client.get_authorization_code_uri()
        
              if error:
                 return context.error('oauth2_error', 'rejected_account_access')
               
              if code:
                
                 client.get_token(code)
                 
                 if not client.access_token:
                    return context.error('oauth2_error', 'failed_access_token')
                  
                 context.response['access_token'] = client.access_token
                 
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
                          return context.not_authorized()
                        
                     
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
                          
                          if not user.has_identity(identity_id):
                             user.append(Identity(identity=identity_id, email=email, primary=False))
                          
                          session = user.new_session()   
                          user.put()
                            
                        cls.set_current_user(user, session)
                        context.auth.user = user
                        
                        context.log.entities.append((user, {'ip_address' : os.environ['REMOTE_ADDR']}))
                        log.Engine.run(context)
                         
                        context.response.update({'user' : user,
                                                 'authorization_code' : user.generate_authorization_code(session),
                                                 'session' : session
                                                 })
                     try:
                        transaction(user) 
                     except Exception as e:
                        context.transaction_error(e)
               
        return context