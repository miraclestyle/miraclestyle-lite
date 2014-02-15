# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import importlib
from google.appengine.api import taskqueue
from google.appengine.ext.db import datastore_errors
from app import ndb
from app.srv import event


class ArgumentError(Exception):
  
  def __init__(self, argument_error):
    self.message = argument_error


class Context():
  
  def __init__(self):
    from app.srv import auth, log, rule, transaction # We do imports here to avoid import collision!
    self.input = {}
    self.output = {}
    self.action = None
    self.callbacks = []
    self.auth = auth.Context()
    self.rule = rule.Context()
    self.log = log.Context()
    self.transaction = transaction.Context()
  
  def new_callback(self, action_key, input):
    self.callbacks.append((action_key, input))
  
  def error(self, key, value):
    if 'errors' not in self.output:
      self.output['errors'] = {}
    if key not in self.output['errors']:
      self.output['errors'][key] = []
    self.output['errors'][key].append(value)
    return self # Do we need this line?


class Engine:
  
  @classmethod
  def get_action(cls, input):
    action_model = input.get('action_model')
    action_key = input.get('action_key')
    
    if action_model:
      action_model = ndb.factory('app.%s' % action_model)
      if hasattr(action_model, '_actions'):
        actions = getattr(action_model, '_actions')
        if action_key in actions:
          return actions[action_key]
      return None
    
    action = event.get_system_action(action_key)
    if not action:
      action = event.Action.get_local_action(action_key)
    return action
  
  @classmethod
  def process(cls, context, input):
    
    input_required = []
    input_invalid = []
    input_error = []
    argument_error = {'input_required': [], 'input_invalid': [], 'input_error': []}
 
    for key, argument in context.action.arguments.items():
      value = input.get(key)
 
      if argument and hasattr(argument, 'format'):
        if value is None:
          continue # If value is not set at all, shall we always consider it none?
        try:
          value = argument.format(value)
          
          if hasattr(argument, '_validator') and argument._validator: # this validator is a custom function that is available by ndb
             argument._validator(argument, value)
             
          context.input[key] = value
        except ndb.FormatError as e:
          input_error.append(key)
        except ndb.FormatErrorRequired as e:
          input_required.append(key)
        except Exception as e:
          input_invalid.append(e)
    
    if len(input_required):
      argument_error['input_required'] = input_required
    
    if len(input_invalid):
      argument_error['input_invalid'] = input_invalid
    
    if len(input_error):
      argument_error['input_error'] = input_error
    
    if len(input_required) or len(input_invalid) or len(input_error):
      raise ArgumentError(argument_error)
  
  @classmethod
  def realtime_run(cls, action, input):
    context = Context()
    context.action = action
    
    try:
      cls.process(context, input)
      if 'action_model' in input and 'action_key' in input:
        action_model = ndb.factory('app.%s' % input.get('action_model'))
        execute = getattr(action_model, input.get('action_key'))
        if execute and callable(execute):
          execute(context)
      else:
        service = importlib.import_module('app.srv.%s' % context.action.service)
        service.Engine.run(context)
        
        
      if context.rule.entity:    
        context.output['entity'] = context.rule.entity.__todict__()
        context.output['entity']['_action_permissions'] = context.rule.entity._action_permissions
        context.output['entity']['_field_permissions'] = context.rule.entity._field_permissions
        context.output['entity']['_actions'] = context.rule.entity._actions
          
    except Exception as e:
      throw = True
      if isinstance(e.message, dict):
        # Here we handle our exceptions.
        for key, value in e.message.items():
          context.error(key, value)
          throw = False
      
      if isinstance(e, datastore_errors.Timeout):
        context.error('transaction', 'timeout')
        throw = False
      
      if isinstance(e, datastore_errors.TransactionFailedError):
        context.error('transaction', 'failed')
        throw = False
      
      if throw:
        raise # Here we raise all other unhandled exceptions!
    
    # We need callback service to be available to taskqueue_run as well as to run methods!
    if context and len(context.callbacks):
      for callback in context.callbacks:
        action_key, input = callback
        input['action_key'] = action_key
        taskqueue.add(url='/engine_run', params=input)
 
    return context
  
  @classmethod
  def taskqueue_run(cls, input):
    action = cls.get_action(input)
    if action:
      context = cls.realtime_run(action, input)
      return context.output
    else:
      output = {'errors': {'invalid_action': input.get('action_key')}}
      return output
  
  @classmethod
  def run(cls, input):
    action = cls.get_action(input)
    if action:
      if action.realtime:
        context = cls.realtime_run(action, input)
        return context.output
      else:
        taskqueue.add(url='/engine_run', params=input)
        return None # Perhaps, here we should return a signal that task queue is running the task.
    else:
      output = {'errors': {'invalid_action': input.get('action_key')}}
      return output
