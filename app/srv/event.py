# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import importlib
from google.appengine.api import taskqueue

from app import ndb

from app.srv import io

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
  def get_action(cls, action_key):
    action = get_system_action(action_key)
    if not action:
      action = io.Action.get_local_action(action_key)
    return action
      
  @classmethod
  def run_action(cls, action, args):
    if action:
      if action.realtime:
        context = action.process(args)
        
        service = importlib.import_module('app.srv.%s' % context.action.service)
        service.Engine.run(context)
        return context
      else:
        args['action'] = action_key.urlsafe()
        taskqueue.add(url='/engine-run', params=args);
    
  @classmethod
  def run(cls, action_key, args):
    
    action = get_action(action_key)
    context = run_action(action)
    
    if context and len(context.callbacks):
      for callback in context.callbacks:
          action_key, args = callback
          action = get_action(action_key)
          run_action(action)

          