# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import logging
from webapp2_extras.i18n import _
from webapp2_extras import sessions

from app import settings
from app import ndb
from app.memcache import get_temp_memory, set_temp_memory

class WorkflowTransitionError(Exception):
      pass
  
class WorkflowStateError(Exception):
      pass
  
class WorkflowEventError(Exception):
      pass
 
class Workflow():
    
      @classmethod
      def _resolve_event_code(cls, event_code):
          if not settings.OBJECT_EVENTS.has_key(cls.__name__):
             raise WorkflowEventError('This model does not have any events defined, check settings.OBJECT_EVENTS for reference.' % settings.OBJECT_STATES)
          
          codes = settings.OBJECT_EVENTS[cls.__name__]
          code = codes.get(event_code)
          if not code:
             raise WorkflowEventError('This model does not have event code %s, while available %s' % (event_code, codes))
          
          return code
    
      @classmethod
      def _resolve_state_code(cls, state_code):
          if not settings.OBJECT_STATES.has_key(cls.__name__):
             raise WorkflowStateError('This model does not have any states defined, check settings.OBJECT_STATES for reference' % settings.OBJECT_STATES)
          
          codes = settings.OBJECT_STATES[cls.__name__]
          code = codes.get(state_code)
          if not code:
             raise WorkflowStateError('This model does not have state code %s, while available %s' % (state_code, codes))
          
          return code
      
      def _resolve_state(self, new_state_code):
          code = self._resolve_state_code(new_state_code)
          state = self.state
          
          # if the state is changing
          if code != new_state_code:
             transitions = settings.OBJECT_TRANSITIONS[self.__name__]
             transition = transitions.get(code)
             if new_state_code not in transition:
                raise WorkflowTransitionError('You cannot move this object from state %s to %s according to %s transition config.' % (state, new_state_code, transitions))
             else:
                return new_state_code
          return code
            
      def _resolve_event(self, new_event_code):
          return self._resolve_event_code(new_event_code)
            
      def new_state(self, state, **kwargs):
          return ObjectLog(state=self._resolve_state(state), parent=self.key, **kwargs).put()
          
      def new_event(self, event, **kwargs):
          return ObjectLog(event=self._resolve_event(event), parent=self.key, **kwargs).put()
      
      @property
      def logs(self):
          return ObjectLog.query(ancestor=self.key)

class User(ndb.BaseExpando, Workflow):
 
    state = ndb.IntegerProperty('1', required=True)
    _default_indexed = False
    
    def logout(self):
        self._self_clear_memcache()
        
    
    @property
    def primary_email(self):
        b = self._self_from_memory('primary_email', -1)
        if b == -1:
           a = {} 
           lia = []
           for e in self.emails.fetch():
               if e.primary == True:
                  a['primary_email'] = e
                  b = e
                  lia.append(e)
                  
           a['emails'] = lia
           self._self_make_memory(a) 
           
        if isinstance(b, UserEmail):
           return b.email
        else:
           return 'N/A'
    
    @property
    def emails(self):
        """
          Returns Query iterator for user emails entity
        """
        return UserEmail.query(ancestor=self.key)
  
    @staticmethod
    def current_user_is_guest():
        u = User.get_current_user()
        return u == 0 or u == None
    
    @staticmethod
    def current_user_is_logged():
        return User.current_user_is_guest() == False
    
    is_logged = current_user_is_logged
         
    @staticmethod
    def get_current_user():
        u = get_temp_memory('user', None)
        if u == None:
            logging.info('get_current_user')
            sess = sessions.get_store().get_session(backend=settings.SESSION_STORAGE)
            if sess.has_key(settings.USER_SESSION_KEY):
               u = sess[settings.USER_SESSION_KEY].get()
               if not u:
                  u = 0
            else:
               u = 0
            set_temp_memory('user', u)
             
        return u
     
    def new_state(self, state, **kwargs):
        return super(User, self).new_state(state, agent=self.key, **kwargs)
        
    def new_event(self, event, **kwargs):
        return super(User, self).new_event(event, agent=self.key, **kwargs)  
    
    def has_permission(self, obj, permission_name=None, strict=False):
        return self._has_permission(self, obj, permission_name, strict)
    
    @classmethod
    def _has_permission(cls, user, obj, permission_name=None, strict=False):
        """
        
        Can be called as `User._has_permission(user_key....)` as well
        
        Params
        `obj` = Entity.key or Entity
        `permission_name` = list, tuple or str
        `strict` = require that all provided permissions need to be checked
        
        Usage...
        
        user = User.get_current_user()
 
        if user.has_permission(store_key, 'store_edit') 
        
        or multiple (if any found)
        
        if user.has_permission(store_key, ['catalog_create', 'catalog_publish'])
        
        or multiple strict mode (must have all of them)
        
        if user.has_permission(store_key, ['catalog_create', 'catalog_publish'], True)
        
        this could also be done by choosing between tuple () and [] to determine if it will be strict, but thats debatable
  
        returns mixed, depending on permission_name==None
        """
        if not isinstance(obj, ndb.Key):
           obj = obj.key
            
        if isinstance(user, basestring):
           user = ndb.Key(user)
           
        if isinstance(user, int):
           user = ndb.Key(cls, user)
           
        if isinstance(user, ndb.Key):
           raise Exception('Not instance of ndb.Key')
   
        memory = User._get_from_memory(user.id())
  
        if memory == None:
           memory = {}
         
        obj_id = obj.id()
        
        if not memory.has_key('permissions'):
           memory['permissions'] = {}
              
        if not memory['permissions'].has_key(obj_id):
           ag_ = AggregateUserPermission.query(AggregateUserPermission.reference==obj, ancestor=user).get(projection=[AggregateUserPermission.permissions])
           ag = memory['permissions'][obj_id] = ag_.permissions
           User._make_memory(user, memory)
        else:
           ag = memory['permissions'].get(obj_id)
           
        # free variable
        del memory
            
        if not ag:
           return False
       
        if ag:
           if permission_name == None:
              return ag
           else:
              if not isinstance(permission_name, (list, tuple)):
                 permission_name = [permission_name]
                 
              for p in permission_name:
                  if strict:
                      if p not in ag:
                         return False
                  else:
                      if p in ag:
                         return True
              return True
        else:
           return False
    
     
class ObjectLog(ndb.BaseModel):
    
    # ancestor Any
    # kind izvlacimo iz kljuca pomocu key.kind() funkcije
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    agent = ndb.KeyProperty('2', kind=User, required=True)
    event = ndb.IntegerProperty('3', required=True)
    state = ndb.IntegerProperty('4', required=True)
    message = ndb.TextProperty('5') # nema potrebe da bude ovo required
    note = ndb.TextProperty('6') # nema potrebe da bude ovo required
    log = ndb.TextProperty('7') # nema potrebe da bude ovo required

class UserEmail(ndb.BaseModel):
    
    # ancestor User
    email = ndb.StringProperty('1', required=True)
    primary = ndb.BooleanProperty('2', default=True, indexed=False)


class UserIdentity(ndb.BaseModel):
    
    # ancestor User
    # index identity only
    user_email = ndb.KeyProperty('1', kind=UserEmail, required=True, indexed=False)
    # provider = ndb.IntegerProperty('2', required=True, indexed=False)# ? ovo nam vise ne treba ja mislim, jer cu da spojim identity-<identity-id> fuck it..
    identity = ndb.StringProperty('3', required=True, indexed=True)# ?
    associated = ndb.BooleanProperty('4', default=True, indexed=False)


class UserIPAddress(ndb.BaseModel):
    
    # ancestor User
    ip_address = ndb.StringProperty('1', required=True, indexed=False)
    logged = ndb.DateTimeProperty('2', auto_now_add=True)


class Role(ndb.BaseModel):
    
    # ancestor Store (Any)
    name = ndb.StringProperty('1', required=True, indexed=False)
    permissions = ndb.StringProperty('2', repeated=True, indexed=False)
    readonly = ndb.BooleanProperty('3', default=True, indexed=False)
    
class UserRole(ndb.Model):
    
    # ancestor User
    role = ndb.KeyProperty('1', kind=Role, required=True)


class AggregateUserPermission(ndb.BaseModel):
    
    # ancestor User
    reference = ndb.KeyProperty('1',required=True)
    permissions = ndb.StringProperty('2', repeated=True, indexed=False)



    