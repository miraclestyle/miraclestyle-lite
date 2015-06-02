# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import math
import decimal
import datetime
import json
import copy
import collections
import string
import time
import re
import sys
import uuid
import inspect

import cProfile
import cStringIO
import pstats

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.ndb import *
from google.appengine.ext.ndb import polymodel
from google.appengine.ext.ndb.model import _BaseValue
from google.appengine.ext import blobstore
from google.appengine.api import search, datastore_errors

import performance
import mem
import util
import settings
import errors

sys.setrecursionlimit(2147483647)

# We always put double underscore for our private functions in order to avoid collision between our code and ndb library.
# For details see: https://groups.google.com/d/msg/appengine-ndb-discuss/iSVBG29MAbY/a54rawIy5DUJ

# We set memory policy for google app engine ndb calls to False, and decide whether to use memcache or not per 'get' call.
ctx = get_context()
ctx.set_memcache_policy(False)


#############################################
########## System wide exceptions. ##########
#############################################


class ActionDenied(errors.BaseKeyValueError):

  KEY = 'action_denied'
  
  def __init__(self, action):
    self.message = {'action_denied': action}


class TerminateAction(Exception):
  pass


class FormatError(Exception):
  pass


#############################################
########## Monkeypatch of ndb.Key! ##########
#############################################


def _get_id(self):
  return self.id()

def _get_id_str(self):
  return str(self.id())

def _get_id_int(self):
  return long(self.id())

def _get_namespace(self):
  return self.namespace()

def _get_kind(self):
  return self.kind()

def _get_parent(self):
  return self.parent()

def _get_urlsafe(self):
  return self.urlsafe()

def _get_root(self):
  pairs = self.pairs()
  return Key(*pairs[0], namespace=self.namespace())

def _get_search_index(self):
  pairs = self.pairs()
  return '%s_search_document_write' % Key(*pairs[0], namespace=self.namespace()).urlsafe()

def _get_search_unindex(self):
  pairs = self.pairs()
  return '%s_search_document_delete' % Key(*pairs[0], namespace=self.namespace()).urlsafe()

def _get_entity(self):
  return self.get()

def _get_namespace_entity(self):
  if self.namespace():
    return Key(urlsafe=self.namespace()).get()
  else:
    return None

def _get_parent_entity(self):
  if self.parent():
    return self.parent().get()
  else:
    return None

def _get_key_structure(self):
  dic = {}
  dic['key'] = self.urlsafe()
  dic['id'] = self.id()
  dic['kind'] = self.kind()
  dic['namespace'] = self.namespace()
  dic['parent'] = {}
  if self.parent():
    parent = self.parent()
    parent_dic = dic['parent']
    while True:
      if not parent:
        break
      parent_dic['kind'] = parent.kind()
      parent_dic['key'] = parent.urlsafe()
      parent_dic['id'] = parent.id()
      parent_dic['namespace'] = parent.namespace()
      parent = parent.parent()
      parent_dic['parent'] = {}
      parent_dic = parent_dic['parent']
  return dic


Key._id = property(_get_id)
Key._id_str = property(_get_id_str)
Key._id_int = property(_get_id_int)
Key._namespace = property(_get_namespace)
Key._kind = property(_get_kind)
Key._parent = property(_get_parent)
Key._urlsafe = property(_get_urlsafe)
Key._root = property(_get_root)
Key._search_index = property(_get_search_index)
Key._search_unindex = property(_get_search_unindex)
Key.entity = property(_get_entity)
Key.namespace_entity = property(_get_namespace_entity)
Key.parent_entity = property(_get_parent_entity)
Key.structure = _get_key_structure
Key._structure = property(_get_key_structure)


#############################################
############ Helpers for orm   ##############
#############################################


class TailRecurseException:
  def __init__(self, args, kwargs):
    self.args = args
    self.kwargs = kwargs

def tail_call_optimized(g):
  """
  This function decorates a function with tail call
  optimization. It does this by throwing an exception
  if it is it's own grandparent, and catching such
  exceptions to fake the tail call optimization.
  
  This function fails if the decorated
  function recurses in a non-tail context.
  """
  def func(*args, **kwargs):
    f = sys._getframe()
    if f.f_back and f.f_back.f_back \
        and f.f_back.f_back.f_code == f.f_code:
      raise TailRecurseException(args, kwargs)
    else:
      while 1:
        try:
          return g(*args, **kwargs)
        except TailRecurseException, e:
          args = e.args
          kwargs = e.kwargs
  func.__doc__ = g.__doc__
  return func

def get_multi_combined(*args, **kwargs):
  async = kwargs.pop('async', None)
  combinations = []
  keys = []
  for arg in args:
    combinations.append(len(arg))
    keys.extend(arg)
  if not async:
    entities = get_multi(keys, **kwargs)
  else:
    entities = get_multi(keys, **kwargs)
  separations = []
  start = 0
  for combination in combinations:
    separations.append(entities[start:combination+start])
    start += combination
  return separations


def get_multi_async_combined(*args, **kwargs):
  kwargs['async'] = True
  return get_multi_combined(*args, **kwargs)


def get_multi_combined_clean(*args, **kwargs):
  separations = get_multi_combined(*args, **kwargs)
  for separation in separations:
    util.remove_value(separation)
  return separations


def get_multi_clean(*args, **kwargs):
  '''This function will retrieve clean list of entities.
  This is because get_multi can return None if key is not found.
  This is mainly used for retriving data that does not need consistency of actual values.
  
  '''
  entities = get_multi(*args, **kwargs)
  util.remove_value(entities)
  return entities


def get_async_results(*args, **kwargs):
  '''It will mutate futures list into results after its done retrieving data.
  This is mainly for making shorthands.
  instead of
  async_entities1 = get_multi_async(..)
  entities1 = [future.get_result() for future in async_entities1]
  async_entities2 = get_multi_async(..)
  entities2 = [future.get_result() for future in async_entities2]
  you write
  entities1 = get_multi_async(..)
  entities2 = get_multi_async(..)
  get_async_results(entities1, entities2)
  for entity in entities1:
  ..
  for entity in entities2:
  ..
  
  '''
  if len(args) > 1:
    for set_of_futures in args:
      get_async_results(set_of_futures, **kwargs)
  elif not isinstance(args[0], list):
    raise ValueError('Futures must be a list, got %s' % args[0])
  futures = args[0]
  Future.wait_all([future for future in futures if isinstance(future, Future) and not future.done()])
  entities = []
  for future in futures:
    if isinstance(future, Future):
      entities.append(future.get_result())
    else:
      entities.append(future)
  if kwargs.get('remove', True):
    util.remove_value(entities)  # empty out the Nones
  del futures[:]  # this empties the list
  for entity in entities:
    futures.append(entity)  # and now we modify back the futures list


def _perform_multi_transactions(entities, write=None, transaction_callack=None, sleep=None):
  '''
  *_multi_transactions functions are used to perform multiple transactions based on number of
  entities provided for writing.
  Entities provided should always be entities which do not have parent, that is, they are not
  originating from the same entity group
  '''
  if transaction_callack is None:
    def run(group, write):
      if write is not None:
        for ent in group:
          ent.write(write)
      else:
        put_multi(group)
  else:
    run = transaction_callack
  for group in util.partition_list(entities, 5):
    transaction(lambda: run(group, write), xg=True)
    if sleep is not None:  # If sleep is specified, the for loop will block before issuing another transaction.
      time.sleep(sleep)


def write_multi_transactions(entities, write_config=None, transaction_callack=None, sleep=None):
  if write_config is None:
    write_config = {}
  _perform_multi_transactions(entities, write_config, transaction_callack, sleep)


def put_multi_transactions(entities, transaction_callack=None, sleep=None):
  _perform_multi_transactions(entities, transaction_callack, sleep)


def write_multi(entities, record_arguments=None):
  if record_arguments is None:
    record_arguments = {}
  is_listed = isinstance(record_arguments, (list, tuple))
  for i, entity in enumerate(entities):
    if is_listed:
      record_arguments_config = record_arguments[i]
    else:
      record_arguments_config = record_arguments
    entity._record_arguments = record_arguments_config
  put_multi(entities)
  for entity in entities:
    entity.index_search_documents()
    entity.unindex_search_documents()

def allowed_state(_state):
  if _state not in [None, 'deleted', 'added']:
    return None
  return _state


################################################################
########## Base extension classes for all ndb models! ##########
################################################################


class _BaseModel(object):
  '''This is base class for all model types in the application.
  Every ndb model will always evaluate True on isinstance(entity, Model).
  
  the following attribute names are reserved by the Model class in our ORM + ndb api.
  
  __get_arg
  __class__
  __deepcopy__
  __delattr__
  __dict__
  __doc__
  __eq__
  __format__
  __getattr__
  __getattribute__
  __getstate__
  __hash__
  __init__
  __metaclass__
  __module__
  __ne__
  __new__
  __reduce__
  __reduce_ex__
  __repr__
  __setattr__
  __setstate__
  __sizeof__
  __str__
  __subclasshook__
  __weakref__
  _allocate_ids
  _allocate_ids_async
  _check_initialized
  _check_properties
  _class_name
  _clone_properties
  _default_filters
  _default_post_allocate_ids_hook
  _default_post_delete_hook
  _default_post_get_hook
  _default_post_put_hook
  _default_pre_allocate_ids_hook
  _default_pre_delete_hook
  _default_pre_get_hook
  _default_pre_put_hook
  _delete_custom_indexes
  _entity_key
  _equivalent
  _fake_property
  _find_uninitialized
  _fix_up_properties
  _from_pb
  _get_by_id
  _get_by_id_async
  _get_kind
  _get_or_insert
  _get_or_insert_async
  _get_property_for
  _gql
  _has_complete_key
  _has_repeated
  _is_default_hook
  _key
  _key_to_pb
  _kind_map
  _lookup_model
  _make_async_calls
  _output
  _parent
  _populate
  _post_allocate_ids_hook
  _post_delete_hook
  _post_get_hook
  _post_put_hook
  _pre_allocate_ids_hook
  _pre_delete_hook
  _pre_get_hook
  _pre_put_hook
  _prepare_for_put
  _projection
  _properties
  _put
  _put_async
  _query
  _read_arguments
  _reset_kind_map
  _root
  _rule_compile
  _rule_compile_global_permissions
  _rule_complement_local_permissions
  _rule_decide
  _rule_override_local_permissions
  _rule_read
  _rule_reset
  _rule_reset_actions
  _rule_reset_fields
  _rule_write
  _search_documents_delete
  _search_documents_write
  _sequence
  _set_attributes
  _set_next_read_arguments
  _set_projection
  _state
  _subentity_counter
  _to_dict
  _to_pb
  _unknown_property
  _update_kind_map
  _use_cache
  _use_memcache
  _use_record_engine
  _use_rule_engine
  _use_search_engine
  _validate_key
  _values
  _write_custom_indexes
  add_output
  allocate_ids
  allocate_ids_async
  build_key
  delete
  delete_search_document
  duplicate
  duplicate_key_id
  generate_unique_key
  get_actions
  get_by_id
  get_by_id_async
  get_fields
  get_kind
  get_meta
  get_or_insert
  get_or_insert_async
  get_output
  get_plugin_groups
  get_search_document
  get_virtual_fields
  gql
  has_complete_key
  index_search_documents
  key
  key_id
  key_id_int
  key_id_str
  key_kind
  key_namespace
  key_parent
  key_root
  key_urlsafe
  make_original
  namespace_entity
  parent_entity
  populate
  put
  put_async
  query
  read
  record
  remove_output
  rule_prepare
  rule_read
  rule_write
  search
  search_document_to_dict
  search_document_to_entity
  set_key
  tests1
  tests2
  to_dict
  unindex_search_documents
  update_search_index
  write
  write_search_document
  
  On top of the previous list, the following attribute names are reserved:
  _expando_fields
  _virtual_fields
  _global_role
  _actions
  executable
  writable
  visible
  searchable
  config --- this is for read_records dict
  _record_arguments
  _read_arguments
  _field_permissions
  store_key -- used by structured properties
  ........ to be continued...
  
  '''
  _initialized = False # flag if this model was initialized by iom
  _state = None  # This field is used by rule engine!
  _sequence = None # Internally used for repeated properties
  _use_record_engine = True  # All models are by default recorded!
  _use_rule_engine = True  # All models by default respect rule engine! @todo This control property doen't respect Action control!!
  _use_search_engine = False  # Models can utilize google search services along with datastore search services.
  _parent = None
  _write_custom_indexes = None
  _delete_custom_indexes = None
 
  def __init__(self, *args, **kwargs):
    self._state = kwargs.pop('_state', None)
    self._sequence = kwargs.pop('_sequence', None)
    super(_BaseModel, self).__init__(*args, **kwargs)
    self._output = []
    self._search_documents_write = []
    self._search_documents_delete = []
    for key in self.get_fields():
        self.add_output(key)

  @classmethod
  def initialize(cls):
    '''
      Initilization method for model. It must be called by iom upon loading all models into memory
    '''
    cls._initialized = True
    fields = cls.get_fields()
    got = []
    for field_key, field in fields.iteritems():
      if hasattr(field, 'initialized') and not field.initialized: # initialize() can only be called once
        field.initialized = True
        field.initialize()
    return True
  
  def __repr__(self):
    if self._projection:
      return super(_BaseModel, self).__repr__()
    original = 'No, '
    if hasattr(self, '_original') and self._original is not None:
      original = '%s, ' % self._original
    out = super(_BaseModel, self).__repr__()
    out = out.replace('%s(' % self.__class__.__name__, '%s(_original=%s_state=%s, ' % (self.__class__.__name__, original, self._state))
    virtual_fields = self.get_virtual_fields()
    if virtual_fields:
      out = out[:-1]
      reprout = []
      for field_key, field in virtual_fields.iteritems():
        val = getattr(self, field_key, None)
        reprout.append('%s=%s' % (field._code_name, val))
      out += ', %s)' % ', '.join(reprout)
    return out
  
  @classmethod
  def _get_kind(cls):
    '''Return the kind name for this class.
    Return value defaults to cls.__name__.
    Users may override this method to give a class different on-disk name than its class name.
    We overide this method in order to numerise kinds and conserve datastore space.
    
    '''
    if hasattr(cls, '_kind'):
      if cls._kind < 0:
        raise TypeError('Invalid _kind %s, for %s.' % (cls._kind, cls.__name__))
      return str(cls._kind)
    return cls.__name__
  
  def _check_initialized(self):
    '''Internal helper to check for uninitialized properties.
    Raises:
    BadValueError if it finds any.
    
    '''
    baddies = self._find_uninitialized()
    if baddies:
      baddies_translated = []
      for baddie in baddies:
        prop = self._properties.get(baddie)
        if prop._code_name:
          baddies_translated.append(prop._code_name)
        else:
          baddies_translated.append(prop._name)
      raise datastore_errors.BadValueError('Uninitialized properties %s. found on %s' % (', '.join(baddies_translated), self))
  
  @classmethod
  def get_kind(cls):
    return cls._get_kind()
  
  @classmethod
  def get_actions(cls):
    return getattr(cls, '_actions', [])
  
  @classmethod
  def get_action(cls, action):
    if isinstance(action, Key):
      action_key = action
    else:
      try:
        action_key = Key(urlsafe=action)
      except:
        action_key = Key(cls.get_kind(), 'action', '1', action)
    class_actions = cls.get_actions()
    for class_action in class_actions:
      if action_key == class_action.key:
        return class_action
    return None
  
  @classmethod
  def get_plugin_groups(cls, action):
    return getattr(action, '_plugin_groups', [])
  
  @classmethod
  def get_fields(cls):
    fields = {}
    for prop_key, prop in cls._properties.iteritems():
      fields[prop._code_name] = prop
    virtual_fields = cls.get_virtual_fields()
    if virtual_fields:
      fields.update(virtual_fields)
    return fields
  
  @classmethod
  def get_virtual_fields(cls):
    if hasattr(cls, '_virtual_fields'):
      for prop_key, prop in cls._virtual_fields.iteritems():
        if not prop._code_name:
          prop._code_name = prop_key
        if not prop._name:
          prop._name = prop_key
      return cls._virtual_fields
    else:
      return False
  
  @classmethod
  def get_meta(cls):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    dic = {}
    dic['_actions'] = getattr(cls, '_actions', [])
    dic['__name__'] = cls.__name__
    dic.update(cls.get_fields())
    return dic
  
  def _make_async_calls(self):
    '''This function is reserved only for SuperReferenceProperty, because it will call its .read_async() method while
    entity is being loaded by from_pb or _post_get_hook.
    
    '''
    if self._projection:
      return # do not attempt anything if entity is projection
    entity = self
    if entity.key and entity.key.id():
      for field, field_instance in entity.get_fields().iteritems():
        if hasattr(field_instance, '_async') and field_instance._autoload:
          value_instance = field_instance._get_value(entity, internal=True)
          value_instance.read_async()
  
  @classmethod
  def _post_get_hook(cls, key, future):
    entity = future.get_result()
    if entity is not None and entity.key:
      entity._make_async_calls()
  
  @classmethod
  def _from_pb(cls, pb, set_key=True, ent=None, key=None):
    entity = super(_BaseModel, cls)._from_pb(pb, set_key, ent, key)
    if entity.key: # make async calls only if the key is present, meaning that the entity is loaded from datastore and not in preparation mode
      entity._make_async_calls()
    return entity
  
  def _pre_put_hook(self):
    self.rule_write()
    for field_key, field in self.get_fields().iteritems():
      if hasattr(field, 'is_structured') and field.is_structured:
        value = getattr(self, field_key, None)
        if hasattr(value, 'pre_update'):
          value.pre_update()
  
  def _post_put_hook(self, future):
    entity = self
    entity.record()
    for field_key, field in entity.get_fields().iteritems():
      if hasattr(field, 'is_structured') and field.is_structured:
        value = getattr(entity, field_key, None)
        if hasattr(value, 'post_update'):
          value.post_update()
    entity.write_search_document()
    if self._root is self: # make_original will only be called on root entity, because make_original logic will handle substructures
      entity.make_original() # in post put hook we override the instance of original with the self, because the entity is now saved and passed the rule engine
    # @todo problem with documents is that they are not transactional, and upon failure of transaction
    # they might end up being stored anyway.
  
  @classmethod
  def _pre_delete_hook(cls, key):
    if key:
      entity = key.get()
      if entity is None:
        return  # Already deleted, nothing we can do about it.
      entity.record()
      for field_key, field in entity.get_fields().iteritems():
        # We have to check here if it has struct.
        if hasattr(field, 'is_structured') and field.is_structured:
          value = getattr(entity, field_key, None)
          if hasattr(value, 'delete'):
            value.delete()
  
  @classmethod
  def _post_delete_hook(cls, key, future):
    # Here we can no longer retrieve the deleted entity, so in this case we just delete the document.
    # Problem with deleting the search index in pre_delete_hook is that if the transaciton fails, the
    # index will be deleted anyway, so that's why we use _post_delete_hook
    cls.delete_search_document(key)
  
  def _set_attributes(self, kwds):
    '''Internal helper to set attributes from keyword arguments.
    Expando overrides this.
    Problem with this method was that it couldn't set virtual properties in constructor. So that's why we override it.
    
    '''
    cls = self.__class__
    for name, value in kwds.iteritems():
      try:
        prop = getattr(cls, name)  # Raises AttributeError for unknown properties.
      except AttributeError as e:
        props = self.get_fields()
        prop = props.get(name)
      if not isinstance(prop, Property):
        if not isinstance(self, Expando):
          raise TypeError('Cannot set non-property %s' % name)
        else:
          setattr(self, name, value)
      else:
        setattr(self, name, value)
  
  def __getattr__(self, name):
    virtual_fields = self.get_virtual_fields()
    if virtual_fields:
      prop = virtual_fields.get(name)
      if prop:
        return prop._get_value(self)
    try:
      return super(_BaseModel, self).__getattr__(name)
    except AttributeError as e:
      # Here is expected Attribute error, not Exception. This fixes some internal python problems.
      raise AttributeError('No attribute "%s" found in instance of "%s". Error was: %s' % (name, self.__class__.__name__, e))
  
  def __setattr__(self, name, value):
    virtual_fields = self.get_virtual_fields()
    if virtual_fields:
      prop = virtual_fields.get(name)
      if prop:
        prop._set_value(self, value)
        return prop
    return super(_BaseModel, self).__setattr__(name, value)
  
  def __delattr__(self, name):
    virtual_fields = self.get_virtual_fields()
    if virtual_fields:
      prop = virtual_fields.get(name)
      if prop:
        prop._delete_value(self)
    try:
      return super(_BaseModel, self).__delattr__(name)
    except:
      pass
  
  def __deepcopy__(self, memo):
    '''This hook for deepcopy will only instance a new entity that has the same properties
    as the one that is being copied. Manually added _foo, _bar and other python properties will not be copied.
    This function can be overriden by models who need to include additional fields that should also be copied.
    e.g.
    entity = super(Entity, self).__deepcopy__()
    entity._my_unexisting_field = self._my_unexisting_field
    return entity
    We cannot copy self.__dict__ because it does not contain all values that are available later
    
    '''
    model = self.__class__
    new_entity = model()
    new_entity.key = copy.deepcopy(self.key, memo)
    new_entity._state = self._state
    new_entity._sequence = self._sequence
    for field_key, field in self.get_fields().iteritems():
      has_can_be_copied = hasattr(field, 'can_be_copied')
      if (not has_can_be_copied or (has_can_be_copied and field.can_be_copied)):
        value = getattr(self, field_key, None)
        is_property_value_type = (hasattr(field, 'is_structured') and field.is_structured)
        if is_property_value_type:
          if not value.has_value():
            continue # if there's no value to copy skip it
          value = value.value
        try:
          value = copy.deepcopy(value, memo)
        except Exception as e:
          print 'Failed copying %s.%s: %s, tried copying: %s' % (field_key, self.__class__.__name__, e, value)
          continue
        if is_property_value_type:
          new_entity_value = getattr(new_entity, field_key)
          new_entity_value.set(value)
        if value is None and (hasattr(field, 'can_be_none') and not field.can_be_none):
          continue
        try:
          setattr(new_entity, field_key, value)
        except (ComputedPropertyError, TypeError) as e:
          pass  # This is intentional
    return new_entity
  
  @property
  def _root(self):
    '''Retrieves top level entity from hierarchy. If parent is none it retrieves self.
    
    '''
    if self._parent is None:
      return self
    parent = self._parent
    last_parent = self._parent
    while True:
      parent = parent._parent
      if parent is None:
        break
      else:
        last_parent = parent
    return last_parent
  
  @classmethod
  def build_key(cls, *args, **kwargs):
    # shorthand for Key(ModelClass.get_kind()...)
    new_args = [cls._get_kind()]
    new_args.extend(args)
    return Key(*new_args, **kwargs)
  
  def set_key(self, *args, **kwargs):
    self.key = self.build_key(*args, **kwargs)
    return self.key
  
  @property
  def key_id(self):
    if self.key is None:
      return None
    return self.key.id()
  
  @property
  def key_id_str(self):
    if self.key is None:
      return None
    return str(self.key.id())
  
  @property
  def key_id_int(self):
    if self.key is None:
      return None
    return long(self.key.id())
  
  @property
  def key_namespace(self):
    if self.key is None:
      return None
    return self.key.namespace()
  
  @property
  def key_kind(self):
    if self.key is None:
      return None
    return self.key.kind()
  
  @property
  def key_parent(self):
    if self.key is None:
      return None
    return self.key.parent()
  
  @property
  def key_urlsafe(self):
    if self.key is None:
      return None
    return self.key.urlsafe()
  
  @property
  def key_root(self):
    if self.key is None:
      return None
    pairs = self.key.pairs()
    return Key(*pairs[0], namespace=self.key.namespace())
  
  @property
  def namespace_entity(self):
    if self.key is None:
      return None
    if self.key.namespace():
      return Key(urlsafe=self.key.namespace()).get()
    else:
      return None
  
  @property
  def parent_entity(self):
    if self.key is None:
      return None
    if self.key_parent:
      return self.key_parent.get()
    else:
      return None
  
  @property
  def root_entity(self):
    if self.key is None:
      return None
    if self.key_root:
      return self.key_root.get()
    else:
      return None
  
  @classmethod
  def _rule_read(cls, permissions, entity, field_key, field):  # @todo Not sure if this should be class method, but it seamed natural that way!?
    '''If the field is invisible, ignore substructure permissions and remove field along with entire substructure.
    Otherwise go one level down and check again.
    
    '''
    if (not field_key in permissions) or (not permissions[field_key]['visible']):
      entity.remove_output(field_key)
    else:
      if hasattr(field, 'is_structured') and field.is_structured:
        child_entity = getattr(entity, field_key)
        child_entity = child_entity.value
        if field._repeated:
          if child_entity is not None:  # @todo We'll see how this behaves for def write as well, because None is sometimes here when they are expando properties.
            for child_entity_item in child_entity:
              child_fields = child_entity_item.get_fields()
              child_fields.update(dict([(p._code_name, p) for _, p in child_entity_item._properties.iteritems()]))
              for child_field_key, child_field in child_fields.iteritems():
                cls._rule_read(permissions[field_key], child_entity_item, child_field_key, child_field)
        else:
          child_entity = getattr(entity, field_key)
          child_entity = child_entity.value
          if child_entity is not None:  # @todo We'll see how this behaves for def write as well, because None is sometimes here when they are expando properties.
            child_fields = child_entity.get_fields()
            child_fields.update(dict([(p._code_name, p) for _, p in child_entity._properties.iteritems()]))
            for child_field_key, child_field in child_fields.iteritems():
              cls._rule_read(permissions[field_key], child_entity, child_field_key, child_field)
  
  def rule_read(self):
    if self._use_rule_engine and hasattr(self, '_field_permissions'):
      entity_fields = self.get_fields()
      for field_key, field in entity_fields.iteritems():
        self._rule_read(self._field_permissions, self, field_key, field)
  
  @classmethod
  def _rule_write(cls, permissions, entity, field_key, field, field_value):
    '''Old principle was: If the field is writable, ignore substructure permissions and override field fith new values.
    Otherwise go one level down and check again.
    
    '''
    if (field_value is None and not field.can_be_none) or (hasattr(field, '_updateable') and (not field._updateable and not field._deleteable)):
      return
    if (field_key in permissions):
      # For simple (non-structured) fields, if writting is denied, try to roll back to their original value!
      if not hasattr(field, 'is_structured') or not field.is_structured:
        if not permissions[field_key]['writable']:
          try:
            setattr(entity, field_key, field_value)
          except TypeError as e:
            util.log.debug('--RuleWrite: setattr error: %s' % e)
          except (ComputedPropertyError, TypeError) as e:
            pass
      else:
        child_entity = getattr(entity, field_key) # child entity can also be none, same destiny awaits it as with field_value
        child_entity = child_entity.value
        if hasattr(field_value, 'has_value'):
          field_value = field_value.value
        field_value_mapping = {}  # Here we hold references of every key from original state.
        if child_entity is None and not field._required:
          # if supplied value from user was none, and this field was not required and if user does not have permission
          # to override it into None, we must revert it completely
          # this is because if we put None on properties that are not required
          if not permissions[field_key]['writable']:
            setattr(entity, field_key, field_value) # revert entire structure
          return
        if field._repeated:
          # field_value can be none, and below we iterate it
          # @note field_value can be None. In that case field_value_mapping will remain empty dict
          if field_value is not None:
            for field_value_item in field_value:
              '''Most of the time, dict keys are int, string an immutable. But generally a key can be anything
              http://stackoverflow.com/questions/7560172/class-as-dictionary-key-in-python
              So using dict[entity.key] = entity.key maybe?
              I'm not sure what's the overhead in using .urlsafe(), but this is something that we can look at.
              Most of the information leads to conclusion that its recommended using immutable objects e.g. int, str
              so anyways all the current code is fine, its just that we can take more simplification in consideration.
              '''
              if field_value_item.key:
                field_value_mapping[field_value_item.key.urlsafe()] = field_value_item
        if not permissions[field_key]['writable']:
          # if user has no permission on top level, and attempts to append new items that do not exist in
          # original values, those values will be removed completely.
          if field._repeated:
            to_delete = []
            for current_value in child_entity:
              if not current_value.key or current_value.key.urlsafe() not in field_value_mapping:
                to_delete.append(current_value)
            for delete in to_delete:
              child_entity.remove(delete)
        if not permissions[field_key]['writable']:
          # If we do not have permission and this is not a local structure,
          # all items that got marked with ._state == 'delete' must have their items removed from the list
          # because they won't even get chance to be deleted/updated and sent to datastore again.
          # That is all good, but the problem with that is when the items get returned to the client, it will
          # "seem" that they are deleted, because we removed them from the entity.
          # So in that case we must preserve them in memory, and switch their _state into modified.
          if field._repeated:
            for current_value in child_entity:
              if current_value._state == 'deleted':
                current_value._state = 'modified'
          else:
            # If its not repeated, child_entities state will be set to modified
            child_entity._state = 'modified'
        # Here we begin the process of field drill.
        for child_field_key, child_field in field.get_model_fields().iteritems():
          if field._repeated:
            # They are bound dict[key_urlsafe]Â = item
            for i, child_entity_item in enumerate(child_entity):
              if child_entity_item._state != 'deleted': 
                '''No need to process deleted entity, since user already has permission to delete it.
                This is mainly because of paradox:
                  catalog._images = writable
                    catalog._images.size = not writable
                    .... and every other field is not writable
                  So generally loop does not need to loop to substructure because user is deleteing entire branch.
                '''
                # If the item has the built key, it is obviously the item that needs update, so in that case fetch it from the
                # field_value_mapping.
                # If it does not exist, the key is bogus, key does not exist, therefore this would not exist in the original state.
                if child_entity_item.key:
                  child_field_value = field_value_mapping.get(child_entity_item.key.urlsafe())  # Always get by key in order to match the editing sequence.
                  child_field_value = getattr(child_field_value, child_field_key, None)
                else:
                  child_field_value = None
                cls._rule_write(permissions[field_key], child_entity_item, child_field_key, child_field, child_field_value)
          else:
            if child_entity._state != 'deleted':
              cls._rule_write(permissions[field_key], child_entity, child_field_key, child_field, getattr(field_value, child_field_key, None))
  
  def rule_write(self):
    if self._use_rule_engine:
      if not hasattr(self, '_field_permissions'):
        raise ValueError('Working without RulePrepare on %r' % self)
      if not hasattr(self, '_original'):
        raise ValueError('Working on entity (%r) without _original. entity.make_original() needs to be called.' % self)
      entity_fields = self.get_fields()
      for field_key, field in entity_fields.iteritems():
        field_value = getattr(self._original, field_key)
        self._rule_write(self._field_permissions, self, field_key, field, field_value)
  
  @classmethod
  def _rule_reset_actions(cls, action_permissions, actions):
    for action in actions:
      action_permissions[action.key.urlsafe()] = {'executable': []}
  
  @classmethod
  def _rule_reset_fields(cls, field_permissions, fields):
    current_fields = fields
    current_fields_iter = fields.iteritems()
    current_field_permissions = field_permissions
    next_args = []
    next_arg = None
    while True:
      try:
        field_key, field = current_fields_iter.next()
      except StopIteration as e:
        if len(next_args):
          next_arg = next_args.pop()
          current_fields = next_arg['current_fields']
          current_fields_iter = next_arg['current_fields_iter']
          current_field_permissions = next_arg['current_field_permissions']
          continue
        else:
          break
      if field_key not in current_field_permissions:
          current_field_permissions[field_key] = collections.OrderedDict([('writable', []), ('visible', [])])
      if hasattr(field, 'is_structured') and field.is_structured:
        model_fields = field.get_model_fields()
        if field._code_name in model_fields:
          model_fields.pop(field._code_name)
        next_arg = {'current_fields': model_fields,
                    'current_fields_iter': model_fields.iteritems(),
                    'current_field_permissions': current_field_permissions[field_key]}
        next_args.append(next_arg)
  
  @classmethod
  def _rule_reset(cls, entity):
    '''This method builds dictionaries that will hold permissions inside
    entity object.
    
    '''
    entity._action_permissions = {}
    entity._field_permissions = {}
    actions = entity.get_actions()
    fields = entity.get_fields()
    cls._rule_reset_actions(entity._action_permissions, actions)
    cls._rule_reset_fields(entity._field_permissions, fields)
  
  @classmethod
  def _rule_decide(cls, permissions, strict, root=True, parent_permissions=None):
    current_permissions = permissions
    current_permissions_iter = current_permissions.iteritems()
    current_root = root
    current_parent_permissions = parent_permissions
    next_args = []
    next_arg = None
    while True:
      try:
        key, value = current_permissions_iter.next()
      except StopIteration as e:
        if len(next_args):
          next_arg = next_args.pop()
          current_permissions = next_arg['current_permissions']
          current_parent_permissions = next_arg['current_parent_permissions']
          current_permissions_iter = next_arg['current_permissions_iter']
          current_root = next_arg['current_root']
          continue
        else:
          break
      if isinstance(value, dict):
        next_arg = {'current_root': False if current_parent_permissions else True,
                    'current_parent_permissions': current_permissions,
                    'current_permissions': value,
                    'current_permissions_iter': value.iteritems()}
        next_args.append(next_arg)
      else:
        if isinstance(value, list) and len(value):
          if (strict):
            if all(value):
              current_permissions[key] = True
            else:
              current_permissions[key] = False
          elif any(value):
            current_permissions[key] = True
          else:
            current_permissions[key] = False
        else:
          current_permissions[key] = False
          if not current_root and not len(value):
            current_permissions[key] = current_parent_permissions[key]
  
  def rule_prepare(self, permissions, strict=False, **kwargs):
    '''This method generates permissions situation for the entity object,
    at the time of execution.
    
    '''
    self._rule_reset(self)
    for permission in permissions:
      if hasattr(permission, 'run'):
        permission.run(self, **kwargs)
    self._rule_decide(self._action_permissions, strict)
    self._rule_decide(self._field_permissions, strict)
    self.add_output('_action_permissions')
    self.add_output('_field_permissions')
  
  def record(self):
    if not (self.gete_kind() == '0') and self._use_record_engine and self.key and self.key_id:
      record_arguments = getattr(self._root, '_record_arguments', None)
      if record_arguments and record_arguments.get('agent') and record_arguments.get('action'):
        log_entity = record_arguments.pop('log_entity', True)
        # @todo We have no control over argument permissions! (if entity._field_permissions['_records'][argument_key]['writable']:)
        record = Record(parent=self.key, **record_arguments)
        if log_entity is True:
          record.log_entity(self)
        return record.put_async()  # @todo How do we implement put_multi in this situation!?
        # We should also test put_async behaviour in transacitons however, they will probably work fine since,
        # general handler failure will result in transaction rollback!
  
  @classmethod
  def search(cls, search_arguments):
    if search_arguments.get('keys'):
      return get_multi_clean(search_arguments.get('keys'))
    if cls._use_search_engine:
      query = search_arguments['property'].build_search_query(search_arguments)
      index = search.Index(name=search_arguments.get('kind'), namespace=search_arguments.get('namespace'))
      return index.search(query)
    else:
      options = search_arguments['property'].build_datastore_query_options(search_arguments)
      query = search_arguments['property'].build_datastore_query(search_arguments)
      return query.fetch_page(options.limit, options=options)
  
  def read(self, read_arguments=None):  # @todo Find a way to minimize synchronous reads here!
    '''This method loads all sub-entities in async-mode, based on input details.
    It's behaviour is controlled by 'read_arguments' dictioary argument!
    'read_arguments' follows this pattern:
    {'_some_field':
       {'config': {'cursor': 0, 'some_other_config': [....]}, '_some_child_field': {''}},
     '_another_field':
       {'config': {'cursor': 0, 'some_other_config': [....]}, '_some_child_field': {''}}
     }
    'config' keyword be revised once we map all protected fields used in _BaseModel.
    
    '''
    if read_arguments is None:
      read_arguments = {}
    self._read_arguments = read_arguments
    futures = []
    for field_key, field in self.get_fields().iteritems():
      has_arguments = field_key in read_arguments
      if has_arguments or (hasattr(field, '_autoload') and field._autoload):
        if not has_arguments:
          read_arguments[field_key] = {'config': {}}
        # we only read what we're told to or if its a local storage or if its marked for autoload
        field_read_arguments = read_arguments.get(field_key, {})
        if hasattr(field, 'is_structured') and field.is_structured:
          value = getattr(self, field_key)
          value.read_async(field_read_arguments)
          futures.append((value, field_read_arguments)) # we have to pack them all for .read()
    for future, field_read_arguments in futures:
      future.read(field_read_arguments)  # Enforce get_result call now because if we don't the .value will be instances of Future.
      # this could be avoided by implementing custom plugin which will do the same thing we do here and after calling .make_original again.
    self.make_original()  # Finalize original before touching anything.
  
  def write(self, record_arguments=None):
    if record_arguments is None:
      record_arguments = {}
    self._record_arguments = record_arguments
    self.put()
    self.index_search_documents()
    self.unindex_search_documents()
  
  def delete(self, record_arguments=None):
    if hasattr(self, 'key') and isinstance(self.key, Key):
      if record_arguments is None:
        record_arguments = {}
      self._record_arguments = record_arguments
      self.key.delete()
      self.unindex_search_documents()
  
  @classmethod
  def generate_duplicated_string(cls, value):
    results = re.match(r'(.*)_duplicate_(.*)', value)
    duplicate = '%s_duplicate_%s'
    uid = str(uuid.uuid4())
    if not results:
      return duplicate % (value, uid)
    results = results.groups()
    return duplicate % (results[0], uid)
  
  def duplicate_key_id(self, key=None):
    '''If key is provided, it will use its id for construction'''
    if key is None:
      the_id = self.key_id_str
    else:
      the_id = key._id_str
    the_id = self.generate_duplicated_string(the_id)
    return the_id
  
  def duplicate(self):
    '''Duplicate this entity.
    Based on entire model configuration and hierarchy, the .duplicate() methods will be called
    on its structured children as well.
    Structured children are any properties that subclass _BaseStructuredProperty.
    Take a look at this example:
    class CatalogImage(Image):
    _virtual_fields = {
    '_descriptions': ndb.SuperRemoteStructuredProperty(Descriptions, repeated=True),
    }
    class Catalog(ndb.BaseModel):
    _virtual_fields = {
    '_images': ndb.SuperRemoteStructuredProperty(CatalogImage, repeated=True),
    }
    .....
    catalog = catalog_key.get()
    duplicated_catalog = catalog.duplicate()
    # remember, calling duplicate() will never perform .put() you must call .put() after you retreive duplicated entity
    duplicated_catalog.put()
    # by performing put, the duplicated catalog will put all entities it prepared in drill stage
    Drill stage looks something like this:
    catalog => duplicate()
       for field in catalog.fields:
         if field is structured:
          _images => duplicate()
             for image in images:
                image => duplicate()
                  for field in image.fields:
                     if field is structured:
                       _descriptions => duplicate()
                          ......... and so on and so on
    Duplicate should always be called from taskqueue because of intensity of queries.
    It is designed to drill without any limits, so having huge entity structure that consists
    of thousands of entities might be problematic mainly because of ram memory usage, not time.
    That could be solved by making the duplicate function more flexible by implementing ability to just
    fetch keys (that need to be copied) who would be sent to other tasks that could carry out the
    duplication on per-entity basis, and signaling complete when the last entity gets copied.
    So in this case, example above would only duplicate data that is on the root entity itself, while the
    multi and single entity will be resolved by only retrieving keys and sending them to
    multiple tasks that could duplicate them in paralel.
    That fragmentation could be achieved via existing cron infrastructure or by implementing something with setup engine.
    
    '''
    new_entity = copy.deepcopy(self)
    new_entity._use_rule_engine = False # we skip the rule engine here because if we dont
    new_entity._parent = self._parent
    the_id = new_entity.duplicate_key_id()
    # user with insufficient permissions on fields might not be in able to write complete copy of entity
    # basically everything that got loaded inb4
    for field_key, field in new_entity.get_fields().iteritems():
      if hasattr(field, 'is_structured') and field.is_structured:
        value = getattr(new_entity, field_key, None)
        value.duplicate() # call duplicate for every structured field
    if new_entity.key:
      new_entity.set_key(the_id, parent=self.key_parent, namespace=self.key_namespace)
      # we append _duplicate to the key, this we could change the behaviour of this by implementing something like
      # prepare_duplicate_key()
      # we always set the key last, because if we dont, then ancestor queries wont work because we placed a new key that
      # does not exist yet
    new_entity._state = 'duplicated'
    return new_entity
  
  def make_original(self):
    '''This function will make a copy of the current state of the entity
    and put that data into _original. Again note that only get_fields() key, _state will be copied.
    
    '''
    if self._use_rule_engine and not self._projection:
      self._original = None
      original = copy.deepcopy(self)
      self._original = original
      def can_copy(field):
        has_can_be_copied = hasattr(field, 'can_be_copied')
        if not has_can_be_copied:
          return True
        else:
          return field.can_be_copied
      # recursevely set original for all structured properties.
      # this is because we have huge depency on _original, so we need to have it on its children as well
      @tail_call_optimized
      def scan(value, field_key, field, original):
        if hasattr(field, 'is_structured') and field.is_structured and hasattr(value, 'has_value') and value.has_value():
          scan(value.value, field_key, field, original.value)
        elif isinstance(value, list):
          for i, val in enumerate(value):
            if not isinstance(val, Model):
              break
            find = filter(lambda x: x.key == val.key, original)
            try:
              find = find[0]
            except IndexError:
              find = None
            scan(val, field_key, field, find)
        elif value is not None and isinstance(value, Model):
          value._original = original
          for field_key, field in value.get_fields().iteritems():
            if can_copy(field):
              scan(getattr(value, field_key, None), field_key, field, getattr(value._original, field_key, None))

      for field_key, field in self.get_fields().iteritems():
        if can_copy(field):
          scan(getattr(self, field_key, None), field_key, field, getattr(self._original, field_key, None))
  
  def get_search_document(self, fields=None):
    '''Returns search document representation of the entity, based on property configurations.
    
    '''
    if self and hasattr(self, 'key') and isinstance(self.key, Key):
      doc_id = self.key_urlsafe
      doc_fields = []
      doc_fields.append(search.AtomField(name='key', value=self.key_urlsafe))
      doc_fields.append(search.AtomField(name='kind', value=self.key_kind))
      doc_fields.append(search.AtomField(name='id', value=self.key_id_str))
      if self.key_namespace is not None:
        doc_fields.append(search.AtomField(name='namespace', value=self.key_namespace))
      if self.key_parent is not None:
        doc_fields.append(search.AtomField(name='ancestor', value=self.key_parent.urlsafe()))
      for field_key, field in self.get_fields().iteritems():
        if field._searchable:
          doc_fields.append(field.get_search_document_field(util.get_attr(self, field_key, None)))
      if fields is not None:
        for field_key, field in fields.iteritems():
          doc_fields.append(field.get_search_document_field(util.get_attr(self, field_key, None)))
      if (doc_id is not None) and len(doc_fields):
        return search.Document(doc_id=doc_id, fields=doc_fields)
  
  def write_search_document(self):
    if self._use_search_engine:
      documents = mem.temp_get(self.key._search_index, [])
      documents.append(self.get_search_document())
      mem.temp_set(self.key._search_index, documents)
  
  @classmethod
  def delete_search_document(cls, key):
    if cls._use_search_engine:
      documents = mem.temp_get(key._search_unindex, [])
      documents.append(key.urlsafe())
      mem.temp_set(key._search_unindex, documents)
  
  @classmethod
  def update_search_index(cls, operation, documents, name, namespace=None):
    if len(documents):
      documents_per_index = 200  # documents_per_index can be replaced with settings variable, or can be fixed to 200!
      index = search.Index(name=name, namespace=namespace)
      for documents_partition in util.partition_list(documents, 200):
        if len(documents_partition):
          # @todo try/except block was removed in order to fail wraping transactions in case of index operation failure!
          if operation == 'index':
            index.put(documents_partition)
          elif operation == 'unindex':
            index.delete(documents_partition)
  
  def index_search_documents(self):
    documents = mem.temp_get(self.key._search_index, [])
    self.update_search_index('index', documents, self._root.key_kind, self._root.key_namespace)
    mem.temp_delete(self.key._search_index)
    if self._write_custom_indexes:
      for index_name, index_documents in self._write_custom_indexes.iteritems():
        self.update_search_index('index', index_documents, index_name)
      self._write_custom_indexes = {}
  
  def unindex_search_documents(self):
    documents = mem.temp_get(self.key._search_unindex, [])
    self.update_search_index('unindex', documents, self._root.key_kind, self._root.key_namespace)
    mem.temp_delete(self.key._search_unindex)
    if self._delete_custom_indexes:
      for index_name, index_documents in self._delete_custom_indexes.iteritems():
        self.update_search_index('unindex', index_documents, index_name)
      self._delete_custom_indexes = {}
  
  @classmethod
  def search_document_to_dict(cls, document):
    # so far we use callbacks to map the retrieved documents, lets keep that practice like that then.
    if document and isinstance(document, search.Document):
      dic = {}
      dic['doc_id'] = document.doc_id
      dic['language'] = document.language
      dic['rank'] = document.rank
      fields = document.fields
      for field in fields:
        dic[field.name] = field.value
    return dic
  
  @classmethod
  def search_document_to_entity(cls, document):
    # @todo We need function to fetch entities from documents as well! get_multi([document.doc_id for document in documents])
    # @answer you mean live active with get multi or this function was to solve that?
    if document and isinstance(document, search.Document):
      entity = cls(key=Key(urlsafe=document.doc_id))
      # util.set_attr(entity, 'language', document.language)
      # util.set_attr(entity, 'rank', document.rank)
      fields = document.fields
      entitiy_fields = entity.get_fields()
      for field in fields:
        entity_field = util.get_attr(entitiy_fields, field.name)
        if entity_field:
          value = entity_field.resolve_search_document_field(field.value)
          if value is util.Nonexistent:
            continue
          util.set_attr(entity, field.name, value)
      return entity
    else:
      raise ValueError('Expected instance of Document, got %s' % document)
  
  def generate_unique_key(self):
    random_uuid4 = str(uuid.uuid4())
    if self.key:
      self.key = self.build_key(random_uuid4, parent=self.key.parent(), namespace=self.key.namespace())
    else:
      self.key = self.build_key(random_uuid4)

  def _set_next_read_arguments(self):
    # this function sets next_read_arguments for the entity that was read
    # purpose of inner function scan is to completely iterate all structured properties which have value and options
    if self is self._root and self.get_kind() != '1':
      if hasattr(self, '_read_arguments'): # if read_args are present, use them as base dict
        value_options = copy.deepcopy(self._read_arguments)
      else:
        value_options = {}
      initial_value_options = value_options
      def scan(value, field_key, field, value_options):
        if hasattr(value, 'has_value') and hasattr(value, 'value_options') and value.has_value():
          options = {'config': value.value_options}
          value_options[field_key] = options
          if value.has_value():
            return (value.value, field_key, field, options)
          else:
            return False
        elif isinstance(value, list):
          factory = []
          for val in value:
            factory.append((val, field_key, field, value_options))
          return factory
        elif value is not None and isinstance(value, Model):
          factory = []
          for field_key, field in value.get_fields().iteritems():
            if hasattr(field, 'is_structured') and field.is_structured:
              val = getattr(value, field_key, None)
              factory.append((val, field_key, field, value_options))
          return factory
        return False
      value = self
      field_key = None
      field = None
      later = []
      sets = None
      force_maybe_false = False
      while True:
        if sets:
          guess = scan(*sets)
          sets = None
          if guess is not False:
            if isinstance(guess, list):
              for g in guess:
                later.append(g)
            else:
              later.append(guess)
          force_maybe_false = True
          continue
        if not force_maybe_false:
          maybe = scan(value, field_key, field, value_options)
        else:
          maybe = False
        if maybe is False:
          if len(later) == 0:
            break
          else:
            try:
              sets = later.pop()
            except IndexError as e:
              break
          continue
        if isinstance(maybe, list):
          for m in maybe:
            later.append(m)
          force_maybe_false = True
        else:
          value = maybe[0]
          field_key = maybe[1]
          field = maybe[2]
          value_options = maybe[3]
          force_maybe_false = False
      self._next_read_arguments = initial_value_options
      return self._next_read_arguments


  def populate_from(self, other):
    '''
    Sets data from other entity to self
    '''
    if self is other:
      return # its the same object
    if self.get_kind() != other.get_kind():
      raise ValueError('Only entities of same kind can be used for populating, got kind %s instead of %s.' % (self.get_kind(), other.get_kind()))
    for field_key, field in self.get_fields().iteritems():
      value = getattr(other, field_key, None)
      if hasattr(field, 'is_structured') and field.is_structured:
        value = value.value
      if value is None and not field.can_be_none:
        continue
      try:
        setattr(self, field_key, value)
      except (ComputedPropertyError, TypeError) as e:
        pass
    self._state = other._state
    self._sequence = other._sequence
  
  def add_output(self, names):
    if not isinstance(names, (list, tuple)):
      names = [names]
    for name in names:
      if name not in self._output:
        self._output.append(name)
  
  def remove_output(self, names):
    if not isinstance(names, (list, tuple)):
      names = [names]
    for name in names:
      if name in self._output:
        self._output.remove(name)
  
  def get_output(self):
    '''This function returns dictionary of stored or dynamically generated data (but not meta data) of the model.
    The returned dictionary can be transalted into other understandable representation to clients (e.g. JSON).
    
    '''
    self.rule_read()  # Apply rule read before output.
    dic = {}
    dic['kind'] = self.get_kind()
    dic['_state'] = self._state
    dic['_sequence'] = self._sequence
    if self.key:
      dic.update(self.key.structure())
    names = self._output
    try:
      for name in names:
        value = getattr(self, name, None)
        dic[name] = value
    except Exception as e:
      util.log.exception(e)
    self._set_next_read_arguments()
    if hasattr(self, '_next_read_arguments'):
      dic['_next_read_arguments'] = self._next_read_arguments
    if hasattr(self, '_read_arguments'):
      dic['_read_arguments'] = self._read_arguments
    return dic


class BaseModel(_BaseModel, Model):
  '''Base class for all 'ndb.Model' entities.'''


class BasePoly(_BaseModel, polymodel.PolyModel):
  '''Base class for all 'polymodel.PolyModel' entities.'''
  
  @classmethod
  def _class_name(cls):
    if hasattr(cls, '_kind'):
      if cls._kind < 0:
        raise TypeError('Invalid _kind %s, for %s.' % (cls._kind, cls.__name__))
      return str(cls._kind)
    return cls.__name__
  
  @classmethod
  def _get_hierarchy(cls):
    '''Internal helper method to return the list of polymorphic base classes.
    This returns a list of class objects, e.g. [Animal, Feline, Cat].
    
    '''
    bases = []
    for base in cls.mro():  # pragma: no branch
      if hasattr(base, '_get_hierarchy') and base.__name__ not in ('BasePoly', 'BasePolyExpando'):
        bases.append(base)
    del bases[-1]  # Delete PolyModel itself.
    bases.reverse()
    return bases
  
  @classmethod
  def _get_kind(cls):
    '''Override.
    Make sure that the kind returned is the root class of the
    polymorphic hierarchy.
    
    '''
    bases = cls._get_hierarchy()
    if not bases:
      # We have to jump through some hoops to call the superclass'
      # _get_kind() method.  First, this is called by the metaclass
      # before the PolyModel name is defined, so it can't use
      # super(PolyModel, cls)._get_kind(). Second, we can't just call
      # Model._get_kind() because that always returns 'Model'. Hence
      # the 'im_func' hack.
      return Model._get_kind.im_func(cls)
    else:
      return bases[0]._class_name()
  
  @classmethod
  def get_kind(cls):
    return cls._class_name()


class BaseExpando(_BaseModel, Expando):
  '''Base class for all 'ndb.Expando' entities.'''
  
  @classmethod
  def get_fields(cls):
    fields = super(BaseExpando, cls).get_fields()
    expando_fields = cls.get_expando_fields()
    if expando_fields:
      fields.update(expando_fields)
    return fields
  
  @classmethod
  def get_expando_fields(cls):
    if hasattr(cls, '_expando_fields'):
      for prop_key, prop in cls._expando_fields.iteritems():
        if not prop._code_name:
          prop._code_name = prop_key
      return cls._expando_fields
    else:
      return False
  
  def __getattr__(self, name):
    expando_fields = self.get_expando_fields()
    if expando_fields:
      prop = expando_fields.get(name)
      if prop:
        return prop._get_value(self)
    return super(BaseExpando, self).__getattr__(name)
  
  def __setattr__(self, name, value):
    expando_fields = self.get_expando_fields()
    if expando_fields:
      prop = expando_fields.get(name)
      if prop:
        if value is None:
          self._clone_properties()
          # @todo setattr invokes del keyword here which deletes the entity
          # that is fine in some cases, but here it isnt since it will delete any entity bypassing the _state = 'deleted'
          # meaning that if user sends _images = [] for the catalog product, this setattr will delete those
          # images without user specifying _state = 'deleted' on them
          # the prop._delete_value triggers proper logic, but still the behaviour should not be like that
          # either change the behaviour of the argument logic or this
          if prop._name in self._properties:
            #prop._delete_value(self)
            #del self._properties[prop._name]
            pass
          return
        self._properties[prop._name] = prop
        prop._set_value(self, value)
        return prop
    return super(BaseExpando, self).__setattr__(name, value)
  
  def __delattr__(self, name):
    expando_fields = self.get_expando_fields()
    if expando_fields:
      prop = expando_fields.get(name)
      if prop:
        self._clone_properties()
        prop._delete_value(self)
        prop_name = prop._name
        if prop in self.__class__._properties:
          raise RuntimeError('Property %s still in the list of properties for the base class.' % name)
        del self._properties[prop_name]
    return super(BaseExpando, self).__delattr__(name)
  
  def _get_property_for(self, p, indexed=True, depth=0):
    '''Internal helper method to get the Property for a protobuf-level property.'''
    name = p.name()
    parts = name.split('.')
    if len(parts) <= depth:
      # Apparently there's an unstructured value here.
      # Assume it is a None written for a missing value.
      # (It could also be that a schema change turned an unstructured
      # value into a structured one. In that case, too, it seems
      # better to return None than to return an unstructured value,
      # since the latter doesn't match the current schema.)
      return None
    next = parts[depth]
    prop = self._properties.get(next)
    if prop is None:
      expando_fields = self.get_expando_fields()
      if expando_fields:
        for expando_prop_key, expando_prop in expando_fields.iteritems():
          if expando_prop._name == next:
            prop = expando_prop
            self._properties[expando_prop._name] = expando_prop
            break
    if prop is None:
      prop = self._fake_property(p, next, indexed)
    return prop


class BasePolyExpando(BasePoly, BaseExpando):
  '''Base class for all 'polymodel.PolyModelExpando' entities.'''