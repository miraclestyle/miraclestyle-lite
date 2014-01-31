# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import importlib

from google.appengine.api import taskqueue
from google.appengine.ext.db import datastore_errors

from app import ndb
from app.srv import event
 
class RequiredError(Exception):
      
     def __init__(self, required):
       self.message = {'required' : required}
    
class InvalidError(Exception):

     def __init__(self, invalid):
       self.message = {'invalid' : invalid}
    
class ArgumentError(Exception):
  
     def __init__(self, argument_error):
       self.message = {'argument_error' : argument_error}  
    
class Context():
  
  def __init__(self):
    
    from app.srv import auth, log, rule, transaction # circular imports @auth
  
    self.action = None
    self.transaction = transaction.Context()
    self.rule = rule.Context()
  
    self.log = log.Context()
    self.auth = auth.Context()
    self.response = {}
    self.args = {}
    self.callbacks = []
 
  def new_callback(self, action_key, args):
    self.callbacks.append((action_key, args))
    
  def transaction_error(self, e):
     """
     This function needs to be used in fashion:
     
     @ndb.transacitonal
     def transaction():
         user.put()
         ...
         
     try:
        transaction()
     except Exception as e:
        response.transaction_error(e)
        
     It will automatically set if the transaction failed because of google network.
     
     """
     if isinstance(e, datastore_errors.Timeout):
        return self.transaction_timeout()
     if isinstance(e, datastore_errors.TransactionFailedError):
        return self.transaction_failed()
     
     raise
 
  def not_implemented(self):
     return self.error('system', 'not_implemented')

  def transaction_timeout(self):
     # sets error in the response that the transaction that was taking place has timed out
     return self.error('transaction_error', 'timeout')
 
  def transaction_failed(self):
     # sets error in the response that the transaction that was taking place has failed
     return self.error('transaction_error', 'failed')
 
  def required(self, k):
     # sets error that the field is required with name `k`
     return self.error(k, 'required')
     
  def invalid(self, k):
     # sets error that the field is not in proper format with name `k`
     return self.error(k, 'invalid_input')
 
  def status(self, m):
     self.response['status'] = m
     return self
 
  def not_found(self):
     # shorthand for informing the response that the entity, object, thing or other cannot be found with the provided params
     self.error('status', 'not_found')
     return self
 
  def not_authorized(self):
     # shorthand for informing the response that the user is not authorize to perform the operation
     return self.error('user', 'not_authorized')
     
  def not_logged_in(self):
     # shorthand for informing the response that the user needs to login in order to perform the operation
     return self.error('user', 'not_logged_in')
 
  def has_error(self, k=None):
     
     if 'errors' not in self.response:
        return False
     
     if k is None:
        return len(self.response['errors'].keys())
     else:
        return len(self.response['errors'][k])
 
  def error(self, f, m):
     
     if 'errors' not in self.response:
        self.response['errors'] = {}
        
     if f not in self.response['errors']:
         self.response['errors'][f] = list()
         
     self.response['errors'][f].append(m)
     return self

 
class Engine:
  
  @classmethod
  def process(cls, context, args):
   
    required = []
    invalid = []
    argument_error = []
 
    for key, argument in context.action.arguments.items():
      
      value = args.get(key)
     
      if argument._required:
         if key not in args:
            required.append(key)
            continue 
          
      if key not in args and not argument._required: 
         if argument._default is not None:
            value = argument._default
          
      if argument and hasattr(argument, 'format'):
         if value is None:
            continue # if value is not set at all, always consider it none?
         try:
            value = argument.format(value)
            context.args[key] = value
         except ndb.FormatError as e:
            argument_error.append(key)
         except Exception as e:
            invalid.append(e)
              
      
    if len(required):
       raise RequiredError(required)
     
    if len(invalid):
       raise InvalidError(invalid)
     
    if len(argument_error):
       raise ArgumentError(argument_error)
  
  @classmethod
  def taskqueue_run(cls, args):
      
      action = cls.get_action(args)
      
      if action:
         cls.realtime_run(action, args)
         
  @classmethod
  def realtime_run(cls, action, args):
      
      context = Context()
      context.action = action
      context.args = {}
       
      try:
        
        cls.process(context, args)
        
        if not context.has_error():
          
          if 'action_model' in args and 'action_key' in args:
             action_model = ndb.factory('app.%s' % args.get('action_model'))
             execute = getattr(action_model, args.get('action_key'))
             if execute and callable(execute):
                return execute(context)
               
          else:
             service = importlib.import_module('app.srv.%s' % context.action.service)
             return service.Engine.run(context)
      except Exception as e:
          if isinstance(e.message, dict):
             pass
             # handle our exceptions
          
          raise # raise all other unhandled exceptions
          
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
      
    action = event.get_system_action(action_key)
    if not action:
      action = event.Action.get_local_action(action_key)
    return action
    
  @classmethod
  def run(cls, args):
    
    action = cls.get_action(args)
    if action:
      if action.realtime:
        context = cls.realtime_run(action, args)
        if context and len(context.callbacks):
          for callback in context.callbacks:
            action_key, args = callback
            args['action_key'] = action_key
            taskqueue.add(url='/engine_run', params=args)
      else:
        taskqueue.add(url='/engine_run', params=args)
        return None
        
    return context