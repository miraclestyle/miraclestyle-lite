# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

from app.srv import transaction, io

class DescriptiveError(Exception):
      # executes an exception in a way that it will have its own meaning instead of just "invalid"
      pass
 
__SYSTEM_ACTIONS = {}

def get_system_action(action_key):
    global __SYSTEM_ACTIONS
    
    action_key = ndb.Key(io.Action, action_key)
    
    return __SYSTEM_ACTIONS.get(action_key.urlasfe())
 
  
def register_system_action(*args):
    global __SYSTEM_ACTIONS
    
    for action in args:
        __SYSTEM_ACTIONS[action.key.urlsafe()] = action
 
class Engine:
  
  @classmethod
  def run(cls, action_key, args):
    
    action = get_system_action(action_key)
    if not action:
      action = io.Action.get_local_action(action_key)
    
    if action:
       context = action.process(args)
      
       @ndb.transactional(xg=True)
       def transaction():
           transaction.Engine.run(context)
       try:
          transaction()
       except Exception as e:
          context.transaction_error(e)