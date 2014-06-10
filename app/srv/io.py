# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import cgi
import importlib

from google.appengine.ext import blobstore
from google.appengine.ext.db import datastore_errors

from app import ndb, util
from app.srv import event


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
    self.tmp = {}
    self.model = None
    self.models = None
    self.action = None
    self.blob_unused = []
    # @todo Perhaps here we should put also self.user and retreave current session user?
  
  def error(self, key, value):
    if 'errors' not in self.output:
      self.output['errors'] = {}
    if key not in self.output['errors']:
      self.output['errors'][key] = []
    self.output['errors'][key].append(value)
    return self  # @todo Do we need this line?
  
  def __repr__(self):
    return self.action.key_id_str


class Engine:
  
  @classmethod
  def init(cls):
    '''This function initializes all models, so it must be called before executing anything!'''
    from app.opt import buyer
    from app.srv import auth, blob, event, log, nav, notify, rule, setup, marketing, product, uom, location, cron
  
  @classmethod
  def get_schema(cls):
    cls.init()
    return ndb.Model._kind_map
  
  @classmethod
  def process_blob_input(cls, context, input):
    for key, value in input.items():
      if isinstance(value, cgi.FieldStorage):
        if 'blob-key' in value.type_options:
          try:
            blob_info = blobstore.parse_blob_info(value)
            context.blob_unused.append(blob_info.key())
          except blobstore.BlobInfoParseError as e:
            pass
  
  @classmethod
  def process_blob_output(cls, context):
    if len(context.blob_unused):
      blobstore.delete(context.blob_unused)
      context.blob_unused = []
  
  @classmethod
  def get_models(cls, context):
    context.models = ndb.Model._kind_map
  
  @classmethod
  def get_model(cls, context, input):
    model_key = input.get('action_model')
    action_model_schema = input.get('action_model_schema')
    model = ndb.Model._kind_map.get(model_key)
    if not action_model_schema:
      context.model = model
    else:
      context.model = model(_model_schema=action_model_schema)
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
    util.logger('Execute action: %s.%s' % (context.model.__name__, context))
    def execute_plugins(plugins):
      for plugin in plugins:
        util.logger('Running plugin: %s.%s' % (plugin.__module__, plugin.__class__.__name__))
        plugin.run(context)
    if hasattr(context.model, 'get_plugin_groups') and callable(context.model.get_plugin_groups):
      try:
        plugin_groups = context.model.get_plugin_groups(context.action)
        if len(plugin_groups):
          for group in plugin_groups:
            if len(group.plugins):
              if group.transactional:
                ndb.transaction(lambda: execute_plugins(group.plugins), xg=True)
              else:
                execute_plugins(group.plugins)
      except event.TerminateAction as e:
        pass
      except Exception as e:
        raise
  
  @classmethod
  def run(cls, input):
    context = Context()
    cls.process_blob_input(context, input)  # This is the most efficient strategy to handle blobs we can think of!
    try:
      cls.init()
      cls.get_models(context)
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
    finally:
      cls.process_blob_output(context)  # This is the most efficient strategy to handle blobs we can think of!
    return context.output
