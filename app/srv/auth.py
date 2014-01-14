# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import hashlib

from app import ndb, settings, memcache, util
from app.srv import event, rule, log

class Context():
  
  def __init__(self):
    self.user = User.current_user()
 
  
class Session(ndb.BaseModel):
    
      session_id = ndb.SuperStringProperty('1', indexed=False)
      updated = ndb.SuperDateTimeProperty('2', auto_now_add=True, indexed=False)
 
     
class Identity(ndb.BaseModel):
    
    _kind = 2
    
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
    state = ndb.SuperIntegerProperty('3', required=True)
    sessions = ndb.SuperLocalStructuredProperty(Session, '4', repeated=True)
 
    _default_indexed = False
  
    _expando_fields = {  
      'roles' : ndb.SuperKeyProperty('5', kind='13', repeated=True, indexed=False)
    }
    
    _actions = {
       'login' : event.Action(name='login',
                              arguments={
                                 'login_method' : ndb.SuperStringProperty(required=True),
                                 'code' : ndb.SuperStringProperty(),
                                 'error' : ndb.SuperStringProperty(),
                                 'redirect_uri' : ndb.SuperStringProperty(),
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
    def entity_is_authenticated(self):
        """ Checks if the loaded model is an authenticated entity user. """
        return self.key.id() == settings.USER_AUTHENTICATED_KEYNAME
    
    @property
    def entity_is_anonymous(self):
        """ Checks if the loaded model is an anonymous user. """
        return self.key.id() == settings.USER_ANONYMOUS_KEYNAME
    
    @property
    def is_guest(self):
        return self.entity_is_anonymous
 
    @classmethod
    def auth_or_anon(cls, what):
        key_name = getattr(settings, 'USER_%s_KEYNAME' % what.upper())
        if key_name:
           # always query these models from memory if any
           result = cls.get_by_id(key_name)
           if result is None:
              result = cls(id=key_name, state=cls.default_state())
              result.put()
           return result
        return None
    
    @classmethod
    def authenticated_user(cls):
        """ Returns authenticated user entity. """
        return cls.auth_or_anon('AUTHENTICATED')
    
    @classmethod
    def anonymous_user(cls):
        """ Returns anonymous user entity """
        return cls.auth_or_anon('ANONYMOUS')
    
    @classmethod
    def set_current_user(cls, user, session=None):
        memcache.temp_memory_set('_current_user', user)
        memcache.temp_memory_set('_current_user_session', session)
        
    @classmethod
    def current_user(cls):
        return memcache.temp_memory_get('_current_user', cls.anonymous_user())
    
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
      
    def logout(self, **kwds):
         
        action = self._actions.get('logout')
        context = action.process(kwds)
        
        @ndb.transactional(xg=True)
        def transaction():
             
            if self.is_guest:
               return context.error('login', 'already_logged_in')
           
            if not self.logout_code == kwds.get('code'):
               return context.error('login', 'invalid_code')
         
            if self.sessions:
               self.sessions = []
 
            context.log.entities.append((self,))
            
            log.Engine.run(context)
            
            self.put()
            
            self.set_current_user(self.anonymous_user())
            
            context.status('logged_out')
        
        try:
            transaction()
        except Exception as e:
            context.transaction_error(e)
            
        return context.response
    
    
    @classmethod
    def login(cls, **kwds):
      
        action = cls._actions.get('login')
        context = action.process(kwds)
        
        if context:
           
           login_method = context.event.args.get('login_method')
           
           if login_method not in settings.LOGIN_METHODS:
              context.error('login_method', 'not_allowed')
           else:
              context.response['providers'] = settings.LOGIN_METHODS
          
           return context.response