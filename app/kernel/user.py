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
          return code
      
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
 
      def new_state(self, state, action, **kwargs):
          
          self.check_transition(state, action)
 
          async = kwargs.pop('_async', None)
          objlog = ObjectLog(state=self.resolve_state(state), action=action, parent=self.key, **kwargs)

          if not async:   
             return objlog.put()
          else:
             return objlog.put_async()
  
      @property
      def logs(self):
          return ObjectLog.query(ancestor=self.key)
      
class ObjectLog(ndb.BaseExpando):
    pass