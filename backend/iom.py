# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import cgi
import inspect
import json
import cProfile
import pstats
import cStringIO
import time

from google.appengine.ext import blobstore
from google.appengine.ext.db import datastore_errors

import performance
import orm
import util
import settings
import mem
import errors
import threading


class InputError(Exception):
  
  def __init__(self, input_error):
    self.message = input_error


class InvalidAction(errors.BaseKeyValueError):

  KEY = 'invalid_action'


class InvalidModel(errors.BaseKeyValueError):

  KEY = 'invalid_model'


class Context():
  
  def __init__(self):
    self.input = {}
    self.output = {}
    self.model = None
    self.models = None
    self.action = None
  
  def error(self, key, value):
    if 'errors' not in self.output:
      self.output['errors'] = {}
    if key not in self.output['errors']:
      self.output['errors'][key] = []
    self.output['errors'][key].append(value)
    return self
  
  def __repr__(self):
    return 'Context of action %s' % self.action.key_id_str


class Engine:
  
  @classmethod
  def process_blob_input(cls, input):
    uploaded_blobs = []
    for key, value in input.iteritems():
      if isinstance(value, cgi.FieldStorage):
        if 'blob-key' in value.type_options:
          try:
            blob_info = blobstore.parse_blob_info(value)
            uploaded_blobs.append(blob_info.key())
          except blobstore.BlobInfoParseError as e:
            pass
    if uploaded_blobs:
      blobs = {'delete': uploaded_blobs}
      # By default, we set that all uploaded blobs must be deleted in 'finally' phase.
      # However, we use blob specialized properties to control intermediate outcome of action.
      mem.temp_set(settings.BLOBKEYMANAGER_KEY, blobs)
  
  @classmethod
  def process_blob_state(cls, state):
    blobs = mem.temp_get(settings.BLOBKEYMANAGER_KEY, None)
    if blobs is not None:
      # Process blobs to be saved.
      save_state_blobs = blobs.get('collect_%s' % state, None)
      delete_blobs = blobs.get('delete', None)
      if delete_blobs is None:
        delete_blobs = blobs['delete'] = []
      if save_state_blobs and delete_blobs is not None:
        for blob in save_state_blobs:
          if blob in delete_blobs:
            delete_blobs.remove(blob)
      # Process blobs to be deleted.
      delete_state_blobs = blobs.get('delete_%s' % state, None)
      if delete_state_blobs and delete_blobs is not None:
        for blob in delete_state_blobs:
          if blob not in delete_blobs:
            delete_blobs.append(blob)
  
  @classmethod
  def process_blob_output(cls):
    blobs = mem.temp_get(settings.BLOBKEYMANAGER_KEY, None)
    if blobs is not None:
      save_blobs = blobs.get('collect', None)
      delete_blobs = blobs.get('delete', None)
      if delete_blobs:
        if save_blobs:
          for blob in save_blobs:
            if blob in delete_blobs:
              delete_blobs.remove(blob)
        if delete_blobs:
          util.log.debug('DELETED %s BLOBS.' % len(delete_blobs))
          blobstore.delete(delete_blobs)
  
  @classmethod
  def init(cls):
    '''This function initializes all models and its properties, so it must be called before executing anything!'''
    from models import account, base, buyer, catalog, collection, location, order, seller, unit
    from plugins import account, base, buyer, catalog, location, order, seller, unit
    util.log.debug('Initialize models...')
    kinds = []
    util.log.debug('Kind map %s has classes.' % len(orm.Model._kind_map))
    for model_kind, model in orm.Model._kind_map.iteritems():
      if hasattr(model, 'initialize'):
        if model.initialize.__self__ is model:
          model.initialize()
          kinds.append(model_kind)
    util.log.debug('Completed Initializing %s classes.' % len(kinds))
  
  @classmethod
  def get_schema(cls):
    return orm.Model._kind_map
  
  @classmethod
  def get_models(cls, context):
    context.models = orm.Model._kind_map
  
  @classmethod
  def get_model(cls, context, input):
    model_key = input.get('action_model')
    model = orm.Model._kind_map.get(model_key)
    context.model = model
    if not context.model:
      raise InvalidModel(model_key)
  
  @classmethod
  def get_action(cls, context, input):
    action_id = input.get('action_id')
    model_kind = context.model.get_kind()
    if hasattr(context.model, 'get_action') and callable(context.model.get_action):
      context.action = context.model.get_action(action_id)
    if not context.action:
      raise InvalidAction(context.action)
  
  @classmethod
  def process_action_input(cls, context, input):
    input_error = {}
    for key, argument in context.action.arguments.items():
      if argument._code_name is None:
        argument._code_name = key
      value = input.get(key, util.Nonexistent)
      if argument and hasattr(argument, 'value_format'):
        try:
          value = argument.value_format(value)
          if value is util.Nonexistent:
            continue  # If the formatter returns util.Nonexistent, that means we have to skip setting context.input[key] = value.
          if hasattr(argument, '_validator') and argument._validator:  # _validator is a custom function that is available by orm.
            argument._validator(argument, value)
          context.input[key] = value
        except orm.FormatError as e:
          if isinstance(e.message, dict):
            for key, value in e.message.iteritems():
              if key not in input_error:
                input_error[key] = []
              if isinstance(value, (list, tuple)):
                input_error[key].extend(value)
              else:
                input_error[key].append(value)
          else:
            if e.message not in input_error:
              input_error[e.message] = []
            input_error[e.message].append(key)  # We group argument exceptions based on exception messages.
        except Exception as e:
          # If this is not defined it throws an error.
          if 'non_property_error' not in input_error:
            input_error['non_property_error'] = []
          input_error['non_property_error'].append(key)  # Or perhaps, 'non_specific_error', or something simmilar.
          util.log.debug(e)
          raise
    if len(input_error):
      raise InputError(input_error)
  
  @classmethod
  def execute_action(cls, context, input):
    action_time = performance.Profile()
    util.log.debug('Action: %s.%s' % (context.model.__name__, context.action.key_id_str))
    def execute_plugins(plugins):
      for plugin in plugins:
        util.log.debug('Plugin: %s.%s' % (plugin.__module__, plugin.__class__.__name__))
        plugin_time = performance.Profile()
        plugin.run(context)
        util.log.debug('Executed in %sms' % plugin_time.miliseconds)
    if hasattr(context.model, 'get_plugin_groups') and callable(context.model.get_plugin_groups):
      try:
        plugin_groups = context.model.get_plugin_groups(context.action)
        if len(plugin_groups):
          for group in plugin_groups:
            if len(group.plugins):
              if group.transactional:
                orm.transaction(lambda: execute_plugins(group.plugins), xg=True)
              else:
                execute_plugins(group.plugins)
      except orm.TerminateAction as e:
        util.log.debug('Action terminated with: %s' % e.message)
      except Exception as e:
        raise
      finally:
        util.log.debug('Completed action in %sms' % action_time.miliseconds)
  
  @classmethod
  def run(cls, input):
    if settings.PROFILING:
      pr = cProfile.Profile()
      pr.enable()
    context = Context()
    cls.process_blob_input(input)  # This is the most efficient strategy to handle blobs we can think of!
    try:
      cls.get_models(context)
      cls.get_model(context, input)
      cls.get_action(context, input)
      cls.process_action_input(context, input)
      cls.execute_action(context, input)
      cls.process_blob_state('success')  # Delete and/or save all blobs that have to be deleted and/or saved on success.
      util.log.debug('Action Completed')
    except Exception as e:
      cls.process_blob_state('error')  # Delete and/or save all blobs that have to be deleted and/or saved or error.
      throw = True
      if isinstance(e.message, dict):
        # Here we handle our exceptions.
        for key, value in e.message.iteritems():
          if isinstance(value, (list, tuple)):
            for v in value:
              context.error(key, v)
          else:
            context.error(key, value)
          throw = False
      if isinstance(e, datastore_errors.Timeout):
        context.error('transaction', 'timeout')
        throw = False
      if isinstance(e, datastore_errors.TransactionFailedError):
        context.error('transaction', 'failed')
        throw = False
      if throw:
        util.log.exception(e)
        if settings.DEBUG:
          raise  # Here we raise all other unhandled exceptions!
        else:
          context.error('internal_server_error', 'error')
    finally:
      util.log.debug('Process Blob Output')
      cls.process_blob_output()  # Delete all blobs that are marked to be deleted no matter what happens!
      if settings.PROFILING:
        pr.disable()
        s = cStringIO.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats(*settings.PROFILING_SORT)
        ps.print_stats()
        util.log.debug(s.getvalue())
    return context.output


Engine.init()