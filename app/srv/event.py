# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

from app import ndb
 
  
__SYSTEM_ACTIONS = {}

def get_system_action(action_key):
  
    global __SYSTEM_ACTIONS
    
    action_key = ndb.Key(Action, action_key)
    
    return __SYSTEM_ACTIONS.get(action_key.urlasfe())
 
  
def register_system_action(*args):
  
    global __SYSTEM_ACTIONS
    
    for action in args:
        __SYSTEM_ACTIONS[action.key.urlsafe()] = action
        
        
class Action(ndb.BaseExpando):
  
  _kind = 56
  
  # root (namespace Domain)
  # key.id() = code.code
  
  name = ndb.SuperStringProperty('1', required=True)
  arguments = ndb.SuperPickleProperty('2') # dict
  active = ndb.SuperBooleanProperty('3', default=True)
  service = ndb.SuperStringProperty('4') # transaction, notify, log....
  operation = ndb.SuperStringProperty('5') # read/write
  realtime = ndb.SuperBooleanProperty('6', default=True) # if False, execute in task queue
 
  
  @classmethod
  def get_local_action(cls, action_key):
      action = ndb.Key(urlsafe=action_key).get()
      if action.active:
         return action
      else:
         return None
          