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
from app.core import get_temp_memory, set_temp_memory

from google.appengine.api import memcache
 
class Workflow():
    
      OBJECT_TYPE = 0
      OBJECT_STATES = {}
      OBJECT_EVENTS = {}
      OBJECT_DEFAULT_STATE = 1
      OBJECT_TRANSITIONS = {}
      
      def new_state(self, state, **kwargs):
          return ObjectLog(state=state, parent=self.key, **kwargs).put()
          
      def new_event(self, event, **kwargs):
          return ObjectLog(event=event, parent=self.key, **kwargs).put()
      
      @property
      def logs(self):
          return ObjectLog.query(ancestor=self.key)

class User(ndb.BaseExpando, Workflow):
    
    OBJECT_TYPE = 1
    OBJECT_STATES = {
        1 : _('Active'),
        2 : _('Banned'),
    }
    OBJECT_EVENTS = {
        1 : _('Registered'),
        2 : _('Logged in'),
        3 : _('Logged out'),

    }
    
    state = ndb.IntegerProperty('1', required=True)
    _default_indexed = False
  
    @staticmethod
    def is_guest():
        return User.get_current_user() == 2
    
    @staticmethod
    def is_logged():
        return User.is_guest() == False
         
    @staticmethod
    def get_current_user():
        u = get_temp_memory('user', 1)
        if u == 1:
            logging.info('get_current_user')
            sess = sessions.get_store().get_session(backend=settings.SESSION_STORAGE)
            if sess.has_key(settings.USER_SESSION_KEY):
               u = sess[settings.USER_SESSION_KEY].get()
               if not u:
                  u = 2
            else:
               u = 2
            set_temp_memory('user', u)
             
        return u
     
    def new_state(self, state, **kwargs):
        return super(User, self).new_state(state, agent=self.key, **kwargs)
        
    def new_event(self, event, **kwargs):
        return super(User, self).new_event(event, agent=self.key, **kwargs)  
    
    def has_permission(self, obj, permission_name=None, strict=False):
        """
        Usage...
        
        user = User.get_current_user()
        
        if permission_name none return list of permissions
        
        if user.has_permission(store_key, 'store_edit') 
        
        or multiple (if any found)
        
        if user.has_permission(store_key, ['catalog_create', 'catalog_publish'])
        
        or multiple strict mode (must have all of them)
        
        if user.has_permission(store_key, ['catalog_create', 'catalog_publish'], True)
        
        this could also be done by choosing between tuple () and [] to determine if it will be strict, but thats debatable
 
         
        """
        if not isinstance(obj, ndb.Key):
           obj = obj.key
        
        # aup = agregate user permission
        k = 'aup-%s' % self.key.id()
 
        memory = get_temp_memory(k, -1)
        if memory == -1:
           memory = memcache.get(k, -1)
           if memory != -1:
              set_temp_memory(k, memory)
           else:
              memory = {}
         
        obj_id = obj.id()
              
        if not memory.has_key(obj_id):
           ag_ = AggregateUserPermission.query(AggregateUserPermission.reference==obj, ancestor=self.key).get(projection=[AggregateUserPermission.permissions])
           ag = memory[obj_id] = ag_.permissions
           set_temp_memory(k, memory)
           memcache.set(k, memory)
        else:
           ag = memory.get(obj_id)
            
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
    # key is MD5 of email + salt
    email = ndb.StringProperty('1', required=True, indexed=False)
    primary = ndb.BooleanProperty('2', default=True, indexed=False)


class UserIdentity(ndb.BaseModel):
    
    # ancestor User
    # key is MD5 of provider + identity + salt
    user_email = ndb.KeyProperty('1', kind=UserEmail, required=True, indexed=False)
    provider = ndb.StringProperty('2', required=True, indexed=False)
    identity = ndb.StringProperty('3', required=True, indexed=False)
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



    