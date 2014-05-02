# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import importlib

from google.appengine.api import taskqueue
from google.appengine.ext.db import datastore_errors

from app import ndb, util


class InputError(Exception):
  
  def __init__(self, input_error):
    self.message = input_error


class InvalidAction(Exception):
  
  def __init__(self, action_key):
    self.message = {'invalid_action': action_key}


class InvalidModel(Exception):
  
  def __init__(self, model_key):
    self.message = {'invalid_model': model_key}


class Context():
  
  def __init__(self):
    self.input = {}
    self.output = {}
    self.model = None
    self.action = None
    # @todo Perhaps here we should put also self.user and retreave current session user?
  
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
    from app import etc, opt
    from app.srv import auth, blob, callback, event, log, nav, notify, rule, setup, marketing, business, product
    kinds = ndb.Model._kind_map
    return kinds
  
  @classmethod
  def get_model(cls, context, input):
    model_key = input.get('action_model')
    context.model = ndb.Model._kind_map.get(model_key)
    if not context.model:
      context.model = ndb.Key(urlsafe=model_key).get()  # @todo We can not do this. We must use special input parameter which will be included in the model instance (example: context.model = transaction.Entry(journal=input.action_model_journal)).
    if not context.model:
      raise InvalidModel(model_key)
  
  @classmethod
  def get_action(cls, context, input):
    action_id = input.get('action_id')
    model_kind = context.model.get_kind()
    if hasattr(context.model, 'get_actions') and callable(context.model.get_actions):
      actions = context.model.get_actions()
      action_key = ndb.Key(model_kind, 'action', '56', action_id).urlsafe()
      if action_key in actions:
        context.action = actions[action_key]
    if not context.action:
      raise InvalidAction(action_key)
  
  @classmethod
  def process_action_input(cls, context, input):
    input_error = {}
    for key, argument in context.action.arguments.items():
      value_provided = key in input
      if not value_provided and argument._default is not None:
        # this must be here because the default value will be ignored, see line 99
        value_provided = True
        value = argument._default
      else:
        value = input.get(key)
      if argument and hasattr(argument, 'format'):
        try:
          if not value_provided and not argument._required:
            continue # skip the .format only if the value was not provided, and if the argument is not required
          value = argument.format(value)
          if hasattr(argument, '_validator') and argument._validator:  # _validator is a custom function that is available by ndb.
            argument._validator(argument, value)
          context.input[key] = value
        except ndb.PropertyError as e:
          if e.message not in input_error:
            input_error[e.message] = []
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
  def execute_action(cls, context, input):
    def execute_plugins(plugins):
      for plugin in plugins:
        plugin.run(context)
    if hasattr(context.model, 'get_plugins') and callable(context.model.get_plugins):
      try:
        plugins = context.model.get_plugins(context.action.key)
        pre_transactional_plugins = []
        transactional_plugins = []
        post_transactional_plugins = []
        pre_transactional = True
        if len(plugins):
          for plugin in plugins:
            if plugin.transactional:
              transactional_plugins.append(plugin)
              pre_transactional = False
            else:
              if pre_transactional:
                pre_transactional_plugins.append(plugin)
              else:
                post_transactional_plugins.append(plugin)
        if len(pre_transactional_plugins):
          execute_plugins(pre_transactional_plugins)
        if len(transactional_plugins):
          ndb.transaction(lambda: execute_plugins(transactional_plugins), xg=True)
        if len(post_transactional_plugins):
          execute_plugins(post_transactional_plugins)
      except Exception as e:
        raise
  
  @classmethod
  def run(cls, input):
    context = Context()
    try:
      cls.get_model(context, input)
      cls.get_action(context, input)
      cls.process_action_input(context, input)
      cls.execute_action(context, input)
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
    return context.output
