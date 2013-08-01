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
    
      OBJECT_STATES = {}
      OBJECT_TRANSITIONS = {}
      OBJECT_ACTIONS = {}
  
      @classmethod
      def _resolve_state_code(cls, state_code):
          codes = cls.OBJECT_STATES
          code = codes.get(state_code)
          if not code:
             raise WorkflowStateError('This model does not have state code %s, while available %s' % (state_code, codes))
          return code
      
      def _resolve_state(self, new_state_code):
          code = self._resolve_state_code(new_state_code)
          state = self.state
          
          # if the state is changing
          if code != new_state_code:
             transitions = self.OBJECT_TRANSITIONS
             transition = transitions.get(new_state_code)
             if new_state_code not in transition:
                raise WorkflowTransitionError('You cannot move this object from state %s to %s according to %s transition config.' % (state, new_state_code, transitions))
             else:
                return new_state_code
          return code
      
      @classmethod
      def _get_state_code(cls, st):
          return cls.OBJECT_STATES[st]
      
      @classmethod
      def _get_action_code(cls, st):
          return cls.OBJECT_ACTIONS[st]
 
      def new_state(self, state, action, **kwargs):
          
          # if `state` is None, use the object's current state
          if state == None:
              state = self.state
               
          if not isinstance(action, int):
             action = self._get_action_code(action)
          
          log = kwargs.pop('log', None)
          message = kwargs.pop('message', None)
          note = kwargs.pop('note', None)
          async = kwargs.pop('_async', None) 
              
          objlog = ObjectLog(state=self._resolve_state(state), action=action, parent=self.key, **kwargs)
          
          if log != None:
             objlog.set_log(log)
             
          if message != None:
             objlog.set_message(message)
             
          if note != None:
             objlog.set_note(note)
          
          if not async:   
             return objlog.put()
          else:
             return objlog.put_async()
      
      @classmethod
      def _workflow_can_transition(cls):
          pass
      
      def workflow_can_transition(self):
          pass
 
      
      @property
      def logs(self):
          return ObjectLog.query(ancestor=self.key)

class User(ndb.BaseExpando, Workflow):
    
    _KIND = 0
  
    OBJECT_STATES = {
        'active' : 1,
        'suspended' : 2,
    }
 
    OBJECT_ACTIONS = {
       'register' : 1,
       'update' : 2,
       'login' : 3,
       'logout' : 4,
       'suspend' : 5,
       'activate' : 6
    }
    
    OBJECT_TRANSITIONS = {
        'activate' : (('suspended', 'active'), None),
        'suspend' : (('active', 'suspended'), ('suspend',)),
    }
     
    state = ndb.IntegerProperty('1', required=True, verbose_name=u'Account State')
    _default_indexed = False
    
    @classmethod
    def default_state(cls):
        return cls._get_state_code('active')
    
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
     
    def new_state(self, state, action, **kwargs):
        return super(User, self).new_state(state, action, agent=self.key, **kwargs)
  
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
   
class ObjectLog(ndb.BaseExpando):
    
    _KIND = 7
    # ancestor Any
    # reference i type izvlacimo iz kljuca - key.parent()
    # posible composite indexes ???
    logged = ndb.DateTimeProperty('1', auto_now_add=True)
    agent = ndb.KeyProperty('2', kind=User, required=True)
    action = ndb.IntegerProperty('3', required=True)
    state = ndb.IntegerProperty('4', required=True)
    
    #_default_indexed = False
    #message / m = ndb.TextProperty('5')# max size 64kb - to determine char count
    #note / n = ndb.TextProperty('6')# max size 64kb - to determine char count
    #log / l = ndb.TextProperty('7')
    
    def set_log(self, txt):
        self.set_virtual_field(txt, 'log', ndb.PickleProperty('7'))
        
    def set_message(self, txt):
        self.set_virtual_field(txt, 'message', ndb.TextProperty('5'))
        
    def set_note(self, txt):
        self.set_virtual_field(txt, 'note', ndb.TextProperty('6'))
         
    @property
    def get_log(self):
        if 'log' in self._properties:
           return self.log
        return None


class UserEmail(ndb.BaseModel):
    
    _KIND = 1
    
    # ancestor User
    email = ndb.StringProperty('1', required=True, verbose_name=u'Email')
    primary = ndb.BooleanProperty('2', default=True, indexed=False, verbose_name=u'Primary Email')

class UserIdentity(ndb.BaseModel):
    
    _KIND = 2
    # ancestor User
    # index identity only
    user_email = ndb.KeyProperty('1', kind=UserEmail, required=True, indexed=False, verbose_name=u'Email Reference')
    identity = ndb.StringProperty('2', required=True, verbose_name=u'Provider User ID')# spojen je i provider name sa id-jem
    associated = ndb.BooleanProperty('3', default=True, indexed=False, verbose_name=u'Associated')


class UserIPAddress(ndb.BaseModel):
    
    _KIND = 3
    # ancestor User
    ip_address = ndb.StringProperty('1', required=True, indexed=False, verbose_name=u'IP Address')
    logged = ndb.DateTimeProperty('2', auto_now_add=True, verbose_name=u'Logged On')


class Role(ndb.BaseModel):
    
    _KIND = 6
    # ancestor Store (Any)
    name = ndb.StringProperty('1', required=True, indexed=False, verbose_name=u'Role Name')
    permissions = ndb.StringProperty('2', repeated=True, indexed=False, verbose_name=u'Role Permissions')# permission_state_model - edit_unpublished_catalog
    readonly = ndb.BooleanProperty('3', default=True, indexed=False, verbose_name=u'Readonly')
    
class UserRole(ndb.Model):
    
    _KIND = 4
    # ancestor User
    role = ndb.KeyProperty('1', kind=Role, required=True, verbose_name=u'User Role')
    state = ndb.IntegerProperty('1', required=True)# invited/accepted


class AggregateUserPermission(ndb.BaseModel):
    
    _KIND = 5
    # ancestor User
    reference = ndb.KeyProperty('1',required=True, verbose_name=u'Reference')# ? ovo je referenca na Role u slucaju da user nasledjuje globalne dozvole, tj da je Role entitet root
    permissions = ndb.StringProperty('2', repeated=True, indexed=False, verbose_name=u'Permissions')# permission_state_model - edit_unpublished_catalog



class TestExpando(ndb.BaseExpando):
      pass
    