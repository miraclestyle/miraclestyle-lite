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
  def taskqueue_run(cls, args):
      
      action = cls.get_action(args)
      
      if action:
         cls.realtime_run(action, args)
         
  @classmethod
  def realtime_run(cls, action, args):
      
      context = action.process(args)
      
      if not context.has_error():
        
        if 'action_model' in args and 'action_key' in args:
            action_model = ndb.factory('app.%s' % args.get('action_model'))
            execute = getattr(action_model, args.get('aciton_key'))
            if execute and callable(execute):
               return execute(context)
             
        else:
          service = importlib.import_module('app.srv.%s' % context.action.service)
          return service.Engine.run(context)
        
      return context

  @classmethod
  def get_action(cls, args):
    
    action_model = args.get('action_model')
    action_key = args.get('action_key')
    
    if action_model:
       action_model = ndb.factory('app.%s' % action_model)
       if hasattr(action_model, '_actions'):
          actions = getattr(action_model, '_actions')
          if action_key in actions:
             return actions[action_key]
      
       return None
      
    action = get_system_action(action_key)
    if not action:
      action = io.Action.get_local_action(action_key)
    return action
      
  @classmethod
  def run_action(cls, action, args):
    if action:
      if action.realtime:
         return cls.realtime_run(action, args)
      else:
        taskqueue.add(url='/engine_run', params=args)
        return None
    
  @classmethod
  def run(cls, args):
    
    action = cls.get_action(args)
    context = cls.run_action(action)
    
    if context and len(context.callbacks):
      for callback in context.callbacks:
          action_key, args = callback
          args['action_key'] = action_key
          taskqueue.add(url='/engine_run', params=args)

          