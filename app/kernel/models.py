# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import pickle
from webapp2_extras.i18n import _
from webapp2_extras import sessions

from app import settings
from app import ndb
from app.memcache import get_temp_memory, set_temp_memory
from app.core import logger

class WorkflowTransitionError(Exception):
      pass
  
class WorkflowStateError(Exception):
      pass
  
class WorkflowActionError(Exception):
      pass
  
class WorkflowBadStateCode(Exception):
      pass

class WorkflowBadActionCode(Exception):
      pass
  
class PermissionError(Exception):
      pass
  
class PermissionDenied(Exception):
      pass

class PermissionBadValue(Exception):
      pass 
 
class Workflow():
    
      OBJECT_STATES = {}
      OBJECT_TRANSITIONS = {}
      OBJECT_ACTIONS = {}
  
      @classmethod
      def _resolve_state_code_by_name(cls, state_code):
          """
          @return tuple (int, str)
          """
          codes = cls.OBJECT_STATES
          code = codes.get(state_code)
          if not code:
             raise WorkflowStateError('This model does not have state code %s, while available %s' % (state_code, codes))
          return code
      
      @classmethod
      def _resolve_action_code_by_name(cls, st):
          """
          @return str
          """
          action = cls.OBJECT_ACTIONS.get(st, None)
          if action == None:
             raise WorkflowActionError('Unexisting action called %s' % st)
          return action
      
      @classmethod
      def _resolve_action_name_by_code(cls, code):
          """
          @return int
          """
          for k, v in cls.OBJECT_ACTIONS.items():
              if v == code:
                 return k
          raise WorkflowBadActionCode('Bad action coded provided %s, possible names %s' % (code, cls.OBJECT_ACTIONS.keys()))  
      
      @classmethod
      def _resolve_state_name_by_code(cls, code):
          """
          @return str
          """
          for k, value in cls.OBJECT_STATES.items():
              if value[0] == code:
                 return k
          raise WorkflowBadStateCode('Bad state code provided %s, possible names %s' % (code, cls.OBJECT_STATES.keys()))  
      
      def resolve_state(self, new_state_code):
          code, transition_name = self._resolve_state_code_by_name(new_state_code)
          state = self.state
          
          # if the state is changing
          if code != state:
             transitions = self.OBJECT_TRANSITIONS
             transition = transitions.get(transition_name)
             
             if (self._resolve_state_name_by_code(state) not in transition['from']) or (new_state_code not in transition['to']):
                raise WorkflowTransitionError('You cannot move this object from state %s to %s according to %s transition config.' % (state, new_state_code, transitions))
             else:
                return new_state_code
          return code
 
      def new_state(self, state, action, **kwargs):
          
          # if `state` is None, use the object's current state
          if state == None:
              state = self._resolve_state_name_by_code(self.state)
               
          if not isinstance(action, int):
             action = self._resolve_action_code_by_name(action)
          
          log = kwargs.pop('log', None)
          message = kwargs.pop('message', None)
          note = kwargs.pop('note', None)
          async = kwargs.pop('_async', None) 
              
          objlog = ObjectLog(state=self.resolve_state(state), action=action, parent=self.key, **kwargs)
          
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
 
      def format_permission(self, permission):
          # generator for permissions based on Entity provided
          # it is required that permission is action defined in `self.OBJECT_ACTIONS`
          if not isinstance(permission, (tuple, list)):
             permission = (permission, )
             
          permission = list(permission)
          
          actions = self.OBJECT_ACTIONS.keys()
          
          for p in permission:
              if p not in actions:
                 raise PermissionBadValue('Provided permission `%s` not common with object `%s`, possible permissions are `%s`' % (p, self.__class__.__name__, actions))
          
          repack = []
          for p in permission:
              # permission (action)_state_model
              repack.append('%s_%s_%s' % (p, self._resolve_state_name_by_code(self.state), self.__class__.__name__.lower()))
              
          return tuple(repack)
          
      @property
      def logs(self):
          return ObjectLog.query(ancestor=self.key)

class User(ndb.BaseExpando, Workflow):
    
    _KIND = 0
  
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)         
        'active' : (1, 'activate'),
        'suspended' : (2, 'suspend'),
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
        'activate' : {
             # from where to where this transition can be accomplished?
            'from' : ('suspend',),
            'to' : ('active',)
         },
        'suspend' : {
            # suspend can go from active to suspend
           'from' : ('active', ),
           'to'   : ('suspend',)
        },
    }
     
    state = ndb.IntegerProperty('1', required=True, verbose_name=u'Account State')
    _default_indexed = False
    
    def aggregate_user_permissions(self):
        return self._aggregate_user_permissions(self)
 
    @classmethod
    def _aggregate_user_permissions(cls, user):
        # aggregates user permissions based on `user`, accepts user.key or user as param
        if not isinstance(user, ndb.Key):
           user = user.key
           
        roles_ = UserRole.query(UserRole.state==UserRole._resolve_state_code_by_name('accepted'), ancestor=user)
        
        @ndb.tasklet
        def callback(user_role):
          role_perms = yield user_role.role.get_async()
          raise ndb.Return((user_role, role_perms))
      
        roles = roles_.map(callback)
        
        permission_makeup = {}
        for r in roles:
            role = r[1]
            reference_key = role.key.parent().urlsafe()
            perms = role.permissions
            aperms = permission_makeup.get(reference_key)
            if aperms:
               perms = perms + aperms 
            
            permission_makeup[reference_key] = set(perms)
                
        fs = AggregateUserPermission.query(ancestor=user).fetch()
        
        keys = permission_makeup.keys()
        to_delete = list()
        puts_fs = []
        
        for f in fs:
            reference_key = f.reference.urlsafe()
            if reference_key not in keys:
               to_delete.append(f.key)
            else:
               xp = permission_makeup.get(reference_key)
               if xp:
                   f.permissions = xp
                   puts_fs.append(f)
                   del permission_makeup[reference_key]
  
        puts = []
        for k, v in permission_makeup.items():
            puts.append(AggregateUserPermission(parent=user, permissions=v, reference=ndb.Key(urlsafe=k)))
            
        puts = puts_fs + puts
        
        @ndb.transactional
        def puts_all(puts, to_delete):
            if len(puts):
               ndb.put_multi(puts)
            
            if len(to_delete):
               ndb.delete_multi(to_delete)
               
        puts_all(puts, to_delete)
              
    @classmethod
    def default_state(cls):
        # returns default state for this model
        return cls._resolve_state_code_by_name('active')[0]
    
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
    
    
    # some shorthand aliases
    is_logged = current_user_is_logged
    is_guest = current_user_is_guest

    # but can use all other methods
         
    @staticmethod
    def get_current_user():
        """
        @return `User`
        """
        u = get_temp_memory('user', None)
        if u == None:
            logger('get_current_user')
            sess = sessions.get_store().get_session(backend=settings.SESSION_STORAGE)
            if sess.has_key(settings.USER_SESSION_KEY):
               u = sess[settings.USER_SESSION_KEY].get()
               if not u:
                  u = 0
            else:
               u = 0
            set_temp_memory('user', u)
             
        return u
    
    current = get_current_user
     
    def new_state(self, state, action, **kwargs):
        return super(User, self).new_state(state, action, agent=self.key, **kwargs)
  
    def has_permission(self, obj, permission_name=None, strict=False, _raise=False):
        return self._has_permission(self, obj, permission_name, strict, _raise)
    
    @classmethod
    def _has_permission(cls, user, obj, permission_name=None, strict=False, _raise=False):
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
        
        if not isinstance(user, ndb.Key):
           user = user.key
        
        if hasattr(obj, 'format_permission'):
           permission_name = obj.format_permission(permission_name)
        else:
           raise PermissionError('obj `%s` provided, is not instance of `Workflow`' % obj)
       
        ex = PermissionDenied('Not allowed, because you do not have permissions: `%s`' % permission_name)
        obj = obj.key
 
        logger('checking if user %s has permissions %s' %  (user.id(), permission_name))
   
        memory = User._get_from_memory(user.id())
  
        if memory == None:
           memory = {}
         
        obj_id = obj.id()
        
        if not memory.has_key('permissions'):
           memory['permissions'] = {}
              
        if not memory['permissions'].has_key(obj_id):
           ag_ = AggregateUserPermission.query(AggregateUserPermission.reference==obj, ancestor=user).get()
           if not ag_:
              perms = []
           else:
              perms = ag_.permissions
           ag = memory['permissions'][obj_id] = perms
           User._make_memory(user, memory)
        else:
           ag = memory['permissions'].get(obj_id)
           
        # free variable
        del memory
            
        if not ag:
           if _raise:
              raise ex
           return False
       
        if ag:
           if permission_name == None:
              return ag
           else: 
              for p in permission_name:
                  if strict:
                      if p not in ag:
                         if _raise:
                            raise ex
                         return False
                  else:
                      if p in ag:
                         return True
              if strict:
                 return True
              else:
                 if _raise:
                    raise ex
                 return False
        else:
           if _raise:
              raise ex
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
    
    # We use this define user-specific expando properties
    # @see meth `BaseExpando.get_field`
    _VIRTUAL_FIELDS = {
       'message' : '5',
       'note' : '6',
       'log' : '7',
    }
  
    def set_log(self, txt):
        self.set_virtual_field(txt, 'log', ndb.PickleProperty(self._VIRTUAL_FIELDS['log']))
        
    def set_message(self, txt):
        self.set_virtual_field(txt, 'message', ndb.TextProperty(self._VIRTUAL_FIELDS['message']))
        
    def set_note(self, txt):
        self.set_virtual_field(txt, 'note', ndb.TextProperty(self._VIRTUAL_FIELDS['note']))
         
    @property
    def get_log(self):
        # returns unpickled log from object log if there's any otherwise `None`
        try:
            return pickle.loads(self.get_field('log'))
        except:
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
    
class UserRole(ndb.Model, Workflow):
    
    _KIND = 4
    # ancestor User

    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)         
        'invited' : (3, 'accept'),
        'accepted' : (4, 'accept'),
        'declined' : (5, 'decline'),
    }
 
    OBJECT_ACTIONS = {
       'invite' : 7,
       'accept' : 8,
       'decline' : 9,
       'remove' : 10,
    }
 
    OBJECT_TRANSITIONS = {
        'accept' : {
             # from where to where this transition can be accomplished?
            'from' : ('invited',),
            'to' : ('accepted',)
         },
        'decline' : {
            # suspend can go from active to suspend
           'from' : ('invited', ),
           'to'   : ('declined',)
        },
    }    
    
    role = ndb.KeyProperty('1', kind=Role, required=True, verbose_name=u'User Role')
    state = ndb.IntegerProperty('1', required=True)# invited/accepted
    
    @classmethod
    def default_state(cls):
        # returns default state for this model
        return cls._resolve_state_code_by_name('invited')[0]

class AggregateUserPermission(ndb.BaseModel):
    
    _KIND = 5
    # ancestor User
    reference = ndb.KeyProperty('1',required=True, verbose_name=u'Reference')# ? ovo je referenca na Role u slucaju da user nasledjuje globalne dozvole, tj da je Role entitet root
    permissions = ndb.StringProperty('2', repeated=True, indexed=False, verbose_name=u'Permissions')# permission_state_model - edit_unpublished_catalog

class TestExpando(ndb.BaseExpando):
      pass
    