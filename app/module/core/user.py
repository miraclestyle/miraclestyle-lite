# -*- coding: utf-8 -*-
'''
Created on Oct 11, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

class WorkflowTransitionError(Exception):
      pass
  
class WorkflowStateError(Exception):
      pass
  
class WorkflowActionError(Exception):
      pass
  
class WorkflowBadStateCodeError(Exception):
      pass

class WorkflowBadActionCodeError(Exception):
      pass
 
class Workflow():
    
      OBJECT_DEFAULT_STATE = False
      OBJECT_STATES = {}
      OBJECT_TRANSITIONS = {}
      OBJECT_ACTIONS = {}
      
      @classmethod
      def default_state(cls):
        # returns default state for this model
        return cls.resolve_state_code_by_name(cls.OBJECT_DEFAULT_STATE)[0]
  
      @classmethod
      def resolve_state_code_by_name(cls, state_code):
          """
          @return tuple (int, str)
          """
          codes = cls.OBJECT_STATES
          code = codes.get(state_code)
          if not code:
             raise WorkflowStateError('This model does not have state code %s, while available %s' % (state_code, codes))
          return code[0]
      
      @classmethod
      def resolve_action_code_by_name(cls, st):
          """
          @return str
          """
          actions = cls.OBJECT_ACTIONS
          action = actions.get(st, None)
          if action == None:
             raise WorkflowActionError('Unexisting action called %s, while available %s' % (st, actions))
          return action
      
      @classmethod
      def resolve_action_name_by_code(cls, code):
          """
          @return int
          """
          for k, v in cls.OBJECT_ACTIONS.items():
              if v == code:
                 return k
          raise WorkflowBadActionCodeError('Bad action coded provided %s, possible names %s' % (code, cls.OBJECT_ACTIONS.keys()))  
      
      @classmethod
      def resolve_state_name_by_code(cls, code):
          """
          @return str
          """
          for k, value in cls.OBJECT_STATES.items():
              if value[0] == code:
                 return k
          raise WorkflowBadStateCodeError('Bad state code provided %s, possible names %s' % (code, cls.OBJECT_STATES.keys()))  
      
      def check_transition(self, state, action):
       
          transitions = self.OBJECT_TRANSITIONS[action]
          
          if self.state not in transitions['from'] or state not in transitions['to']:
             raise WorkflowTransitionError('This object cannot go from state `%s` to state `%s`. It can only go from states `%s` to `%s`'
                                           % (self.state, state, transitions['from'], transitions['to']))
      
      def set_state(self, state):
          self.state = self.resolve_state_code_by_name(state)
          
      def new_state(self, state, action, **kwargs):
          """ Sets new state inited by some action, and returns instance of object log ready for put """
          
          self.state = self.resolve_state_code_by_name(state)
          self.check_transition(state, action)
  
          objlog = ObjectLog(state=self.resolve_state(state), action=action, parent=self.key, **kwargs)

          return objlog
  
      @property
      def logs(self):
          return ObjectLog.query(ancestor=self.key)
      
class UserIdentity(ndb.BaseModel):
    
    # StructuredProperty model
    identity = ndb.StringProperty('1', required=True)# spojen je i provider name sa id-jem
    email = ndb.StringProperty('2', required=True)
    associated = ndb.BooleanProperty('3', default=True)
    primary = ndb.BooleanProperty('4', default=True)
          
          
class User(ndb.BaseExpando):
    
    identities = ndb.StructuredProperty(UserIdentity, '1', repeated=True)# soft limit 100x
    emails = ndb.SuperStringProperty('2', repeated=True)# soft limit 100x
    state = ndb.SuperIntegerProperty('3', required=True)
    
    _default_indexed = False
 
    #Expando
    EXPANDO_FIELDS = {
      'roles' : ndb.KeyProperty('4', kind='DomainRole', repeated=True)                 
    }
    
    KIND_ID = 0
    
    OBJECT_DEFAULT_STATE = 'su_active'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'su_active' : (1, ),
        'su_suspended' : (2, ),
    }
    
    OBJECT_ACTIONS = {
       'register' : 1,
       'update' : 2,
       'login' : 3,
       'logout' : 4,
       'sudo' : 5,
    }
    
    OBJECT_TRANSITIONS = {
        'su_activate' : {
             # from where to where this transition can be accomplished?
            'from' : ('su_suspended',),
            'to' : ('su_active',),
         },
        'su_suspend' : {
           'from' : ('su_active', ),
           'to'   : ('su_suspended',),
        },
    }   
      
class ObjectLog(ndb.BaseExpando):
    
    logged = ndb.SuperDateTimeProperty('1', auto_now_add=True)
    agent = ndb.SuperKeyProperty('2', kind=User, required=True)
    action = ndb.SuperIntegerProperty('3', required=True)
    state = ndb.SuperIntegerProperty('4', required=True) # verovatno ide u expando
    
    _default_indexed = False
    
    EXPANDO_FIELDS = {
       'message' : ndb.TextProperty('5'),
       'note' : ndb.TextProperty('6'),
       'log' : ndb.PickleProperty('7')
    }
 
class UserIPAddress(ndb.BaseModel):
    
    # ancestor User
    # not logged
    # ako budemo radili per user istragu loga onda nam treba composite index: ancestor:yes - logged:desc
    logged = ndb.SuperDateTimeProperty('1', auto_now_add=True, required=True)
    ip_address = ndb.SuperStringProperty('2', required=True, indexed=False)    
    