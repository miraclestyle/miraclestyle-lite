# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import importlib

from google.appengine.api import taskqueue
from google.appengine.ext.db import datastore_errors

from app import ndb, util
from app.srv import event


class InputError(Exception):
  
  def __init__(self, input_error):
    self.message = input_error


class Context():
  
  def __init__(self):
    from app.srv import callback, auth, log, rule, notify, cruds  # We do imports here to avoid import collision!
    self.input = {}
    self.output = {}
    self.action = None
    self.callback = callback.Context()
    self.auth = auth.Context()
    self.rule = rule.Context()
    self.log = log.Context()
    self.cruds = cruds.Context()
  
  def error(self, key, value):
    if 'errors' not in self.output:
      self.output['errors'] = {}
    if key not in self.output['errors']:
      self.output['errors'][key] = []
    self.output['errors'][key].append(value)
    return self  # @todo Do we need this line?


class Engine:
  
  @classmethod
  def get_schema(cls):
    from app import domain, etc, opt
    from app.srv import auth, blob, callback, event, log, nav, notify, rule, setup
    kinds = ndb.Model._kind_map
    return kinds
  
  @classmethod
  def get_action(cls, input):
    action_model = input.get('action_model')
    action_key = input.get('action_key')
    
    if action_model:
      action_model = ndb.Model._kind_map.get(action_model)
      if action_model and hasattr(action_model, '_actions'):
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
    
    input_error = {}
    
    for key, argument in context.action.arguments.items():
      value = input.get(key)
      
      if argument and hasattr(argument, 'format'):
        if value is None:
          continue  # If value is not set at all, shall we always consider it none?
        try:
          value = argument.format(value)
          
          if hasattr(argument, '_validator') and argument._validator:  # _validator is a custom function that is available by ndb.
            argument._validator(argument, value)
          
          context.input[key] = value
        except ndb.PropertyError as e:
          if e.message not in input_error:
            input_error[e.message] = []  # If the e.message is not set, set it otherwise KeyError.
          input_error[e.message].append(key)  # We group argument exceptions based on exception messages.
        except Exception as e:
          # If this is not defined it throws an error.
          if 'non_property_error' not in input_error:
            input_error['non_property_error'] = []
          input_error['non_property_error'].append(key)  # Or perhaps, 'non_specific_error', or something simmilar.
          util.logger(e, 'exception')
    
    if len(input_error):
      raise InputError(input_error)
  
  @classmethod
  def realtime_run(cls, action, input):
    context = Context()
    context.action = action
    
    try:
      cls.process(context, input)
      if 'action_model' in input and 'action_key' in input:
        action_model = ndb.Model._kind_map.get(input.get('action_model'))
        execute = getattr(action_model, input.get('action_key'))
        if execute and callable(execute):
          execute(context)
      else:
        service = importlib.import_module('app.srv.%s' % context.action.service)
        service.Engine.run(context)
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
        raise  # Here we raise all other unhandled exceptions!
    
    return context
  
  @classmethod
  def run(cls, input):
    action = cls.get_action(input)
    if action:
      context = cls.realtime_run(action, input)
      return context.output
    else:
      output = {'errors': {'invalid_action': input.get('action_key')}}
      return output
