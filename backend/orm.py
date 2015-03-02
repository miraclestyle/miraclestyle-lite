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

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.ndb import *
from google.appengine.ext.ndb import polymodel
from google.appengine.ext.ndb.model import _BaseValue
from google.appengine.ext import blobstore
from google.appengine.api import search, datastore_errors

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
########## Helper classes of orm   ##########
#############################################


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
    _deepcopied = '_deepcopy' in kwargs
    if _deepcopied:
      kwargs.pop('_deepcopy')
    self._state = kwargs.pop('_state', None)
    self._sequence = kwargs.pop('_sequence', None)
    super(_BaseModel, self).__init__(*args, **kwargs)
    if not _deepcopied:
      self.make_original()
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
    fields = cls.get_fields()
    for field_key, field in fields.iteritems():
      if hasattr(field, 'initialized') and not field.initialized: # initialize() can only be called once
        field.initialize()
        field.initialized = True
    cls._initialized = True
    if cls._initialized:
       return False
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
        if isinstance(field_instance, SuperReferenceProperty) and field_instance._autoload:
          value_instance = field_instance._get_value(entity, internal=True)
          value_instance.read_async()
  
  @classmethod
  def _post_get_hook(cls, key, future):
    entity = future.get_result()
    if entity is not None and entity.key:
      entity.make_original()
      entity._make_async_calls()
  
  @classmethod
  def _from_pb(cls, pb, set_key=True, ent=None, key=None):
    entity = super(_BaseModel, cls)._from_pb(pb, set_key, ent, key)
    entity.make_original()
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
    new_entity = model(_deepcopy=True)
    new_entity.key = copy.deepcopy(self.key)
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
        value = copy.deepcopy(value)
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
  def _rule_write(cls, permissions, entity, field_key, field, field_value):  # @todo Not sure if this should be class method, but it seamed natural that way!?
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
        if isinstance(field_value, PropertyValue):
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
            # They are bound dict[key_urlsafe] = item
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
        raise ValueError('Working without RulePrepare on %s' % self)
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
    for field_key, field in fields.iteritems():
      if field_key not in field_permissions:
        field_permissions[field_key] = collections.OrderedDict([('writable', []), ('visible', [])])
      if hasattr(field, 'is_structured') and field.is_structured:
        model_fields = field.get_model_fields()
        if field._code_name in model_fields:
          model_fields.pop(field._code_name)  # @todo Test this behavior!
        cls._rule_reset_fields(field_permissions[field_key], model_fields)
  
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
    for key, value in permissions.iteritems():
      if isinstance(value, dict):
        if parent_permissions:
          root = False
        cls._rule_decide(permissions[key], strict, root, permissions)
      else:
        if isinstance(value, list) and len(value):
          if (strict):
            if all(value):
              permissions[key] = True
            else:
              permissions[key] = False
          elif any(value):
            permissions[key] = True
          else:
            permissions[key] = False
        else:
          permissions[key] = False
          if not root and not len(value):
            permissions[key] = parent_permissions[key]
  
  def rule_prepare(self, permissions, strict=False, **kwargs):
    '''This method generates permissions situation for the entity object,
    at the time of execution.
    
    '''
    self._rule_reset(self)
    for permission in permissions:
      if isinstance(permission, Permission):
        permission.run(self, **kwargs)
    self._rule_decide(self._action_permissions, strict)
    self._rule_decide(self._field_permissions, strict)
    self.add_output('_action_permissions')
    self.add_output('_field_permissions')
  
  def record(self):
    if not isinstance(self, Record) and self._use_record_engine and self.key and self.key_id:
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
      def scan(value, field_key, field, original):
        if hasattr(field, 'is_structured') and field.is_structured and isinstance(value, PropertyValue) and value.has_value():
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
    if self is self._root:
      def scan(value, field_key, field, value_options):
        if isinstance(value, PropertyValue) and hasattr(value, 'value_options') and value.has_value():
          options = {'config': value.value_options}
          value_options[field_key] = options
          if value.has_value():
            scan(value.value, field_key, field, options)
        elif isinstance(value, list):
          for val in value:
            scan(val, field_key, field, value_options)
        elif value is not None and isinstance(value, Model):
          for field_key, field in value.get_fields().iteritems():
            val = getattr(value, field_key, None)
            scan(val, field_key, field, value_options)
      if hasattr(self, '_read_arguments'): # if read_args are present, use them as base dict
        value_options = copy.deepcopy(self._read_arguments)
      else:
        value_options = {}
      for field_key, field in self.get_fields().iteritems():
        scan(self, field_key, field, value_options)
      self._next_read_arguments = value_options
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
          if prop._name in self._properties:
            prop._delete_value(self)
            del self._properties[prop._name]
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


#########################################################
########## Superior properties implementation! ##########
#########################################################


PROPERTY_VALUES = []


class PropertyValue(object):
  
  def __init__(self, property_instance, entity, **kwds):
    self._property = property_instance
    self._entity = entity
    self._kwds = kwds
    self._property_value_options = {}
  
  def __repr__(self):
    return '%s(entity=instance of %s, property=%s, property_value=%s, kwds=%s)' % (self.__class__.__name__,
                                                                                   self._entity.__class__.__name__,
                                                                                   self._property.__class__.__name__,
                                                                                   self.value, self._kwds)
  
  @property
  def property_name(self):
    # Retrieves code name of the field for setattr usage. If _code_name is not available it will use _name
    name = self._property._code_name
    if not name:
      name = self._property._name
    return name
  
  @property
  def value_options(self):
    ''''_property_value_options' is used for storing and returning information that
    is related to property value(s). For exmaple: 'more' or 'cursor' parameter in querying.
    '''
    return self._property_value_options
  
  def has_value(self):
    return hasattr(self, '_property_value')
  
  @property
  def value(self):
    return getattr(self, '_property_value', None)

  @property
  def read_value(self):
    # read value is used mainly for def get_output() because it will output whatever the client instructed it to read
    # by default the read_value will return self.value, which in most of the cases is the case
    return self.value
  
  def get_output(self):
    return self.read_value


class StructuredPropertyValue(PropertyValue):
  
  def _set_parent(self, entities=None):
    '''This function should be called whenever a new entity is instanced / retrieved inside a root entity.
    It either accepts entities, or it will use self.value to iterate.
    Its purpose is to maintain hierarchy like so:
    catalog._parent = None # its root
     product._parent = catalog
       product_instance._parent = product
         product_instance.contents[0]._parent = product_instance
         ....
    So based on that, you can always reach for the top by simply finding which ._parent is None.
    '''
    as_list = False
    if entities is None:
      entities = self.value
      as_list = self._property._repeated
    else:
      as_list = isinstance(entities, list)
    if entities is not None:
      if as_list:
        for entity in entities:
          if entity._parent is None:
            entity._parent = self._entity
          else:
            continue
      else:
        if entities._parent is None:
          entities._parent = self._entity
    return entities
  
  def set(self, property_value):
    '''We always verify that the property_value is instance
    of the model that is specified in the property configuration.
    
    Set will always iterate the property_value to individually set values on existing set of values, or 
    append new value if its new. This is to solve problem with seting stuctured value
    '''
    if property_value is not None:
      property_value_copy = property_value
      if not self._property._repeated:
        property_value_copy = [property_value_copy]
      for property_value_item in property_value_copy:
        if not isinstance(property_value_item, self._property.get_modelclass()):
          raise ValueError('Expected %s, got %s' % (self._property.get_modelclass().get_kind(), property_value_item.get_kind()))
      if not self._property._repeated:
        if self.has_value() and self._property_value is not None:
          self._property_value.populate_from(property_value)
        else:
          if property_value._state is None:
            property_value._state = 'created'
          self._property_value = property_value
      else:
        if self.has_value() and self._property_value is not None:
          existing = dict((ent.key.urlsafe(), ent) for ent in self._property_value if ent.key)
          new_list = []
          for ent in property_value:
            # this is to support proper setting of data for existing instances
            exists = ent.key
            if exists is not None:
              exists = existing.get(ent.key.urlsafe())
            if exists is not None:
              exists.populate_from(ent)
              new_list.append(exists)
            else:
              '''
              if ent._state is None:
                ent._state = 'created'
              '''
              new_list.append(ent)
          del property_value[:] 
          property_value.extend(new_list)
        self._property_value = property_value
      self._set_parent()
  
  def _deep_read(self, read_arguments=None):  # @todo Just as entity.read(), this function fails it's purpose by calling both read_async() and read()!!!!!!!!
    '''This function will keep calling .read() on its sub-entity-like-properties until it no longer has structured properties.
    This solves the problem of loading data in hierarchy.
    '''
    if self.has_value():
      entities = self.read_value # @todo this should be .value, but for locally structured .read_value
      if not self._property._repeated:
        if not entities:
          entities = []
        else:
          entities = [entities]
      futures = []
      for entity in entities:
        for field_key, field in entity.get_fields().iteritems():
          if hasattr(field, 'is_structured') and field.is_structured:
            has_arguments = field_key in read_arguments
            if has_arguments or (hasattr(field, '_autoload') and field._autoload):
              if not has_arguments:
                read_arguments[field_key] = {'config': {}}
              value = getattr(entity, field_key)
              field_read_arguments = read_arguments.get(field_key, {})
              value.read_async(field_read_arguments)
              futures.append((value, field_read_arguments))
      for future, field_read_arguments in futures:
        future.read(field_read_arguments)  # Again, enforce read and re-loop if any.
  
  def _read_sync(self, read_arguments):
    '''Read sync should never be called directly, its primary use is for .read()
    the self._property_value in this method will always be list of futures, or a future.
    '''
  
  def _read(self, read_arguments):
    '''Purpose of _read is to perform proper logic which will populate _property_value with futures or real values
    depending on the nature of the property.
    '''
  
  def read_async(self, read_arguments=None):
    '''Prepares read arguments for _read function. This function is called internaly trough ORM when possible,
    however, it can be called publicly as well. Beware however, it will only perform the call if no value is present
    or if force_read in config is True.
    '''
    if read_arguments is None:
      read_arguments = {}
    if self._property._read_arguments is not None and isinstance(self._property._read_arguments, dict):
      util.merge_dicts(read_arguments, self._property._read_arguments)
    config = read_arguments.get('config', {})
    if self._property._readable:
      if (not self.has_value()) or config.get('force_read'): # it will not attempt to start rpcs if there's already something set in _property_value
        self._read(read_arguments)
  
  def read(self, read_arguments=None):
    '''Reads the property values in sync mode. Calls read_async and _read_sync to complete full read.
    Also calls _format_callback on the results, sets hierarchy and starts read recursion if possible.
    This function should always be called publicly if data is needed right away from the desired property.
    '''
    if read_arguments is None:
      read_arguments = {}
    if self._property._readable:
      self.read_async(read_arguments) # first perform all in async mode
      self._read_sync(read_arguments) # then immidiately perform in sync mode
      format_callback = self._property._format_callback
      if callable(format_callback):
        self._property_value = format_callback(self._entity, self._property_value)
      self._set_parent()
      self._deep_read(read_arguments)
      return self.value
   

class LocalStructuredPropertyValue(StructuredPropertyValue):

  def __init__(self, *args, **kwargs):
    super(LocalStructuredPropertyValue, self).__init__(*args, **kwargs)
    self._structured_values = []
    self._property_value_by_read_arguments = None

  @property
  def read_value(self):
    # property used for fetching values that were retrived using read_arguments
    value = self.value # trigger value's logic
    if self._property_value_by_read_arguments is None:
      return value
    return self._property_value_by_read_arguments
  
  @property
  def value(self):
    # overrides base value to solve unwrapping problem that appears when entity is about to be saved to datastore
    # _BaseValue is used to wrap data by ndb
    if self.has_value():
      wrapped = False
      if self._property._repeated:
        if self._property_value:
          if isinstance(self._property_value[0], _BaseValue):
            wrapped = True
      else:
        if isinstance(self._property_value, _BaseValue):
          wrapped = True
      if wrapped:
        self._property._get_user_value(self._entity) # _get_user_value will unwrap values from _BaseValue when possible
    return super(LocalStructuredPropertyValue, self).value

  def post_update(self):
    for structured in self._structured_values:
      if hasattr(structured, 'post_update'):
        structured.post_update()
    if self.has_value() and self._property._repeated:
      if self._property._repeated:
        values = self.value
        if self._property_value_by_read_arguments is not None:
          for i,val in enumerate(self._property_value_by_read_arguments):
            matches = filter(lambda x: x.key == val.key, values)
            if matches:
              self._property_value_by_read_arguments[i] = matches[0]
          new_entities = [v for v in values if v._state == 'created']
          self._property_value_by_read_arguments.extend(new_entities)
          self._property_value_by_read_arguments.sort(key=lambda x: x._sequence, reverse=True)

  def _read(self, read_arguments):
    property_value = self._property._get_user_value(self._entity)
    property_value_as_list = property_value
    if read_arguments is None:
      read_arguments = {}
    config = read_arguments.get('config', {})
    if property_value_as_list is not None:
      if not self._property._repeated:
        property_value_as_list = [property_value_as_list]
      total = len(property_value_as_list) - 1
      if self._property._repeated:
        supplied_keys = config.get('keys', [])
        supplied_keys = SuperVirtualKeyProperty(kind=self._property.get_modelclass().get_kind(), repeated=True).value_format(supplied_keys)
        if self._property_value_by_read_arguments is not None:
          self._property_value_by_read_arguments = []
      self._property_value_options.update(config)
      for i, value in enumerate(property_value_as_list):
        value._sequence = total - i
        if self._property._repeated and supplied_keys is not None:
          if value.key in supplied_keys:
            if self._property_value_by_read_arguments is None:
              self._property_value_by_read_arguments = []
            self._property_value_by_read_arguments.append(value)
      self._property_value = property_value
    else:
      if self._property._repeated:
        self._property_value = []
  
  def pre_update(self):
    if self.has_value():
      fields = self._property.get_modelclass().get_fields()
      delete_states = ['removed', 'deleted']
      def collect_structured(value):
        for field_key, field in fields.iteritems():
          if hasattr(field, 'is_structured') and field.is_structured:
            property_value = getattr(value, field_key)
            self._structured_values.append(property_value)

      def delete_structured(entity):
        for structured in self._structured_values:
          repeated = structured._property._repeated
          structured = structured.read() # read and mark for delete
          if structured is not None:
            if not repeated:
              structured = [structured]
            for structure in structured:
              if entity.key == structure.key.parent():
                structure._state = 'deleted'

      if self._property._repeated:
        delete_entities = []
        for entity in self._property_value:
          if hasattr(entity, 'prepare'):
            entity.prepare(parent=self._entity.key)
          collect_structured(entity)
          if (entity._state in delete_states and self._property._deleteable) \
            or (not self._property._addable and not hasattr(entity, '_original')):
            # if the property is deleted and deleteable
            # or if property is not addable and it does not exist in originals, remove it.
            delete_entities.append(entity)
            if entity._state == 'deleted':
              delete_structured(entity)

        for delete_entity in delete_entities:
          self._property_value.remove(delete_entity)

        if not self._property._updateable: # if the property is not updatable we must revert all data to original
          for i,ent in enumerate(self._property_value):
            if hasattr(ent, '_original'):
              self._property_value[i] = copy.deepcopy(ent._original)
      else:
        if hasattr(self._property_value, 'prepare'):
          self._property_value.prepare(parent=self._entity.key)
        collect_structured(self._property_value)
        if self._property_value._state in delete_states and self._property._deleteable:
          if self._property_value._state == 'deleted':
            delete_structured(self._property_value)
          self._property_value = None  # Comply with expando and virtual fields.
      self._property._set_value(self._entity, self._property_value, True)
      
  def delete(self):
    if self._property._deleteable:
      self.read()
      if self.has_value():
        property_value = self._property_value
        if not self._property._repeated:
          property_value = [self._property_value]
        fields = self._property.get_modelclass().get_fields()
        for value in property_value:
          for field_key, field in fields.iteritems():
            if hasattr(field, 'is_structured') and field.is_structured:
              val = getattr(value, field_key)
              val.delete()
          value._state = 'deleted'
  
  def duplicate(self):
    if not self._property._duplicable:
      return
    self.read()
    values = self.value
    if self._property._repeated:
      entities = []
      for entity in values:
        entities.append(entity.duplicate())
    else:
      entities = values.duplicate()
    self._property_value = entities
    self._set_parent()
    self._property._set_value(self._entity, entities, True) # this is because using other method would cause duplicate results via duplicate process.
    return self._property_value

  def add(self, entities):
    '''Primarly used to extend values repeated property
    '''
    if self._property._repeated:
      if self.has_value():
        if self._property_value:
          try:
            last = self._property_value[0]._sequence
            if last is None:
              last = 0
          except IndexError:
            last = 0
          last_sequence = last + 1
          for ent in entities:
            ent._sequence += last_sequence
    else:
      util.log.warn('cannot use .add() on non repeated property')
    # Always trigger setattr on the property itself
    setattr(self._entity, self.property_name, entities)

class RemoteStructuredPropertyValue(StructuredPropertyValue):
  
  def has_future(self):
    value = self.value
    if isinstance(value, list):
      if len(value):
        value = value[0]
    return isinstance(value, Future)
  
  def _read_single(self, read_arguments):
    model = self._property.get_modelclass()
    if not hasattr(model, 'prepare_key'):
      property_value_key = Key(self._property.get_modelclass().get_kind(), self._entity.key_id_str, parent=self._entity.key)
    else:
      property_value_key = model.prepare_key(parent=self._entity.key)
    self._property_value = property_value_key.get_async()
  
  def _read_repeated(self, read_arguments):
    config = read_arguments.get('config', {})
    search = config.get('search', {})
    supplied_keys = config.get('keys')
    if supplied_keys:
      model = self._property.get_modelclass()
      supplied_keys = SuperVirtualKeyProperty(kind=model.get_kind(), repeated=True).value_format(supplied_keys)
      for supplied_key in supplied_keys:
        if supplied_key.parent() != self._entity.key:
          raise ValueError('invalid_parent_for_key_%s' % supplied_key.urlsafe())
      entities = get_multi_async(supplied_keys)
      self._property_value_options.update(config)
    else:
      if 'search' not in config:
        config['search'] = search
      search['ancestor'] = self._entity.key.urlsafe()
      if 'options' not in search:
        search['options'] = {'limit': 10}
      limit = search['options']['limit']
      search_property = self._property.search
      search_property._cfg.update({'ancestor_kind': self._entity.get_kind()})
      search_arguments = search_property.value_format(search)
      if search_arguments.get('keys'):
        entities = get_multi_async(search_arguments.get('keys'))
      else:
        options = search_property.build_datastore_query_options(search_arguments)
        query = search_property.build_datastore_query(search_arguments)
        if limit == 0:
          entities = query.fetch_async(options=options)
        else:
          entities = query.fetch_page_async(options.limit, options=options)
      if 'property' in search:
        del search['property']
      search['options']['limit'] = limit
      self._property_value_options['search'] = search
    self._property_value = entities


  def _read(self, read_arguments):
    if self._property._repeated:
      self._read_repeated(read_arguments)
    else:
      self._read_single(read_arguments)
  
  def _read_sync(self, read_arguments):
    '''Will perform all needed operations on how to retrieve all values from Future(s).
    '''
    if self.has_future():
      if self._property._repeated:
        property_value = []
        if isinstance(self._property_value, list): # this is for get_multi_async, fetch_async()
          get_async_results(self._property_value)
        elif isinstance(self._property_value, Future): # this is for .fetch_page_async()
          property_value = self._property_value.get_result()
          if isinstance(property_value, tuple):
            cursor = property_value[1]
            if cursor:
              cursor = cursor.urlsafe()
            util.remove_value(property_value[0])
            self._property_value = property_value[0]
            self._property_value_options['search']['options']['start_cursor'] = cursor
            self._property_value_options['more'] = property_value[2]
          else:
            self._property_value = property_value
      else: # this is for key.get_async()
        result = self._property_value.get_result()
        if result is None:
          model = self._property.get_modelclass()
          if not hasattr(model, 'prepare_key'):
            remote_single_key = Key(model.get_kind(), self._entity.key_id_str, parent=self._entity.key)
          else:
            remote_single_key = model.prepare_key(parent=self._entity.key)
          result = self._property.get_modelclass()(key=remote_single_key)
        self._property_value = result
  
  def _post_update_single(self):
    if not hasattr(self._property_value, 'prepare'):
      if self._property_value.key_parent != self._entity.key:
        self._property_value.set_key(self._entity.key_id_str, parent=self._entity.key)
    else:
      self._property_value.prepare(parent=self._entity.key)
    if self._property_value._state == 'deleted' and self._property._deleteable:
      self._property_value.key.delete()
    elif self._property._updateable or (not getattr(self._property_value, '_original', None) \
                                         and self._property._addable):
      # put only if the property is updateable, or if its not set and its addable, do the put.
      self._property_value.put()
  
  def _post_update_repeated(self):
    delete_entities = []
    for entity in self._property_value:
      if not hasattr(entity, 'prepare'):
        if entity.key_parent != self._entity.key:
          key_id = entity.key_id
          entity.set_key(key_id, parent=self._entity.key)
      else:
        entity.prepare(parent=self._entity.key)
      if entity._state == 'deleted' and self._property._deleteable:
        delete_entities.append(entity)
    for delete_entity in delete_entities:
      self._property_value.remove(delete_entity)
    for i, entity in enumerate(self._property_value[:]):
      is_new = entity._state == 'created'
      if not self._property._addable and is_new:
        # if property does not allow new values remove it from put queue
        self._property_value.remove(entity)
      elif not self._property._updateable and not is_new:
        # if updates are not permitted, then always revert to original value
        # note that if addable is true, then user will be in able to add new items no matter what
        self._property_value[i] = copy.deepcopy(entity._original)
    delete_multi([entity.key for entity in delete_entities])
    put_multi(self._property_value)
  
  def post_update(self):
    if self.has_value():
      if not self._property._repeated:
        self._post_update_single()
      else:
        self._post_update_repeated()
    else:
      pass
  
  def _delete_single(self):
    self.read()
    self._property_value.key.delete()
  
  def _delete_repeated(self):
    cursor = Cursor()
    limit = 200
    while True:
      _entities, cursor, more = self._property.get_modelclass().query(ancestor=self._entity.key).fetch_page(limit, start_cursor=cursor, use_cache=False, use_memcache=False)
      if len(_entities):
        self._set_parent(_entities)
        delete_multi([entity.key for entity in _entities])
        if not cursor or not more:
          break
      else:
        break
  
  def delete(self):
    if self._property._deleteable:
      if not self._property._repeated:
        self._delete_single()
      else:
        self._delete_repeated()
  
  def _duplicate_single(self):
    self.read()
    duplicated = self._property_value.duplicate()
    self._property_value = duplicated
  
  def _duplicate_repeated(self):
    '''Fetch ALL entities that belong to this entity.
    On every entity called, .duplicate() function will be called in order to ensure complete recursion.
    '''
    entities = []
    _entities = self._property.get_modelclass().query(ancestor=self._entity.key).fetch()
    if len(_entities):
      for entity in _entities:
        entity.read()
        self._set_parent(entity)
        entities.append(entity.duplicate())
    self._property_value = entities
  
  def duplicate(self):
    if not self._property._duplicable:
      return
    if not self._property._repeated:
      self._duplicate_single()
    else:
      self._duplicate_repeated()
    self._set_parent()

  def add(self, entities):
    '''Primarly used to extend values list of the property, or override change it if its used on non repeated property.
    '''
    if self._property._repeated:
      if self.has_value():
        entities.extend(self._property_value)
    # Always trigger setattr on the property itself
    setattr(self._entity, self.property_name, entities)


class ReferenceStructuredPropertyValue(StructuredPropertyValue):
  
  def has_future(self):
    value = self.value
    if isinstance(value, list):
      if len(value):
        value = value[0]
    return isinstance(value, Future)
  
  def _read(self, read_arguments):
    target_field = self._property._target_field
    callback = self._property._callback
    if not target_field and not callback:
      target_field = self.property_name
    if callback:
      self._property_value = callback(self._entity)
    elif target_field:
      field = getattr(self._entity, target_field)
      if field is None:  # If value is none the key was not set, therefore value must be null.
        self._property_value = None
        return
      if not isinstance(field, Key):
        raise ValueError('Targeted field value must be instance of Key. Got %s' % field)
      if self._property.get_modelclass().get_kind() != field.kind():
        raise ValueError('Kind must be %s, got %s' % (self._property.get_modelclass().get_kind(), field.kind()))
      self._property_value = field.get_async()
  
  def _read_sync(self, read_arguments):
    if self.has_future():
      if isinstance(self._property_value, list):
        self._property_value = map(lambda x: x.get_result(), self._property_value)
      else:
        self._property_value = self._property_value.get_result()
  
  def delete(self):
    self._property_value = None
  
  def duplicate(self):
    pass


class ReferencePropertyValue(PropertyValue):
  
  def has_future(self):
    value = self.value
    if isinstance(value, list):
      if len(value):
        value = value[0]
    return isinstance(value, Future)
  
  def set(self, value):
    if isinstance(value, Key):
      self._property_value = value.get_async()
    else:
      self._property_value = value
  
  def _read(self):
    target_field = self._property._target_field
    if not target_field and not self._property._callback:
      target_field = self.property_name
    if self._property._callback:
      self._property_value = self._property._callback(self._entity)
    elif target_field:
      field = getattr(self._entity, target_field)
      if field is None:  # If value is none the key was not set, therefore value must be null.
        self._property_value = None
        return self.value
      if not isinstance(field, Key):
        raise ValueError('Targeted field value must be instance of Key. Got %s' % field)
      if self._property._kind != None and field.kind() != self._property._kind:
        raise ValueError('Kind must be %s, got %s' % (self._property._kind, field.kind()))
      self._property_value = field.get_async()
  
  def read_async(self):
    if not self.has_value():
      self._read()
  
  def read(self):
    self.read_async()
    if self.has_future():
      if isinstance(self._property_value, list):
        self._property_value = map(lambda x: x.get_result(), self._property_value)
      else:
        self._property_value = self._property_value.get_result()
      if self._property._format_callback:
        if isinstance(self._property_value, list):
          self._property_value = map(lambda x: self._property._format_callback(self._entity, x), self._property_value)
        else:
          self._property_value = self._property._format_callback(self._entity, self._property_value)
    return self.value
  
  def delete(self):
    self._property_value = None


PROPERTY_VALUES.extend((LocalStructuredPropertyValue, RemoteStructuredPropertyValue, ReferencePropertyValue))


class _BaseProperty(object):
  '''Base property class for all superior properties.
  '''
  _max_size = None
  _value_filters = None
  _searchable = None
  _search_document_field_name = None
  initialized = False
  
  def __init__(self, *args, **kwargs):
    self._max_size = kwargs.pop('max_size', self._max_size)
    self._value_filters = kwargs.pop('value_filters', self._value_filters)
    self._searchable = kwargs.pop('searchable', self._searchable)
    self._search_document_field_name = kwargs.pop('search_document_field_name', self._search_document_field_name)
    super(_BaseProperty, self).__init__(*args, **kwargs)
   
  @property 
  def can_be_none(self): # checks if the property can be set to None
    return True
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    '''
    choices = self._choices
    if choices:
      choices = list(self._choices)
    dic = {'verbose_name': self._verbose_name,
           'indexed': self._indexed,
           'name': self._name,
           'code_name': self._code_name,
           'required': self._required,
           'max_size': self._max_size,
           'choices': choices,
           'default': self._default,
           'repeated': self._repeated,
           'is_structured': self.is_structured,
           'searchable': self._searchable,
           'search_document_field_name': self._search_document_field_name,
           'type': self.__class__.__name__}
    if hasattr(self, '_compressed'):
      dic['compressed'] = self._compressed
    return dic
  
  def property_keywords_format(self, kwds, skip_kwds):
    limits = {'name': 20, 'code_name': 20, 'verbose_name': 50, 'search_document_field_name': 20}
    for k, v in kwds.items():
      if k in skip_kwds:
        v = getattr(self, k, None)
      else:
        if k in ('name', 'verbose_name', 'search_document_field_name'):
          v = unicode(v)
          if len(v) > limits[k]:
            raise FormatError('property_%s_too_long' % k)
        elif k in ('indexed', 'required', 'repeated', 'searchable'):
          v = bool(v)
        elif k == 'choices':
          if v is not None:
            if not isinstance(v, list):
              raise FormatError('expected_list_for_choices')
        elif k == 'default':
          if v is not None:
            v = self.value_format(v) # default value must be acceptable by property value format standards
        elif k == 'max_size':
          if v is not None:
            v = int(v)
      kwds[k] = v
  
  def _property_value_validate(self, value):
    if self._max_size:
      if len(value) > self._max_size:
        raise FormatError('max_size_exceeded')
    if value is None and self._required:
      raise FormatError('required')
    if hasattr(self, '_choices') and self._choices:
      if value not in self._choices:
        raise FormatError('not_in_specified_choices')
  
  def _property_value_filter(self, value):
    if self._value_filters:
      if isinstance(self._value_filters, (list, tuple)):
        for value_filter in self._value_filters:
          value = value_filter(self, value)
      else:
        value = self._value_filters(self, value)
    return value
  
  def _property_value_format(self, value):
    if value is util.Nonexistent:
      if self._default is not None:
        value = copy.deepcopy(self._default)
      elif self._required:
        raise FormatError('required')
      else:
        return value  # Returns util.Nonexistent
    if self._repeated:
      out = []
      if not isinstance(value, (list, tuple)):
        value = [value]
      for v in value:
        self._property_value_validate(v)
        out.append(v)
      return self._property_value_filter(out)
    else:
      self._property_value_validate(value)
      return self._property_value_filter(value)
  
  @property
  def search_document_field_name(self):
    if self._search_document_field_name is not None:
      return self._search_document_field_name
    return self._code_name if self._code_name is not None else self._name
  
  def get_search_document_field(self, value):
    raise NotImplemented('Search representation of property %s not available.' % self)
  
  def resolve_search_document_field(self, value):
    if self._repeated:
      return self.value_format(value.split(' '))
    else:
      return self.value_format(value)
  
  @property
  def is_structured(self):
    return False
  
  def initialize(self):
    '''This function is called by io def init() in io.py to prepare the field for work.
    This is mostly because of get_modelclass lazy-loading of modelclass.
    In order to allow proper loading of modelclass for structured properties for example, we must wait for all python
    classes to initilize into _kind_map.
    Only then we will be in able to pick out the model by its kind from _kind_map registry.
    '''
    pass


class _BaseStructuredProperty(_BaseProperty):
  '''Base class for structured property.
  '''
  _readable = True
  _updateable = True
  _addable = True
  _deleteable = True
  _autoload = True
  _duplicable = True
  _format_callback = None
  _value_class = LocalStructuredPropertyValue
  
  def __init__(self, *args, **kwargs):
    args = list(args)
    self._readable = kwargs.pop('readable', self._readable)
    self._updateable = kwargs.pop('updateable', self._updateable)
    self._deleteable = kwargs.pop('deleteable', self._deleteable)
    self._autoload = kwargs.pop('autoload', self._autoload)
    self._addable = kwargs.pop('addable', self._addable)
    self._format_callback = kwargs.pop('format_callback', self._format_callback)
    self._read_arguments = kwargs.pop('read_arguments', {})
    self._duplicable = kwargs.pop('duplicable', self._duplicable)
    if not kwargs.pop('generic', None): # this is because storage structured property does not need the logic below
      if isinstance(args[0], basestring):
        set_arg = Model._kind_map.get(args[0])
        if set_arg is not None: # if model is not scanned yet, do not set it to none
          args[0] = set_arg
    super(_BaseStructuredProperty, self).__init__(*args, **kwargs)
  
  def get_modelclass(self, **kwargs):
    '''Function that will attempt to lazy-set model if its kind id was specified.
    If model could not be found it will raise an error. This function is used instead of directly accessing
    self._modelclass in our code.
    This function was mainly invented for purpose of structured and multi structured property. See its usage
    trough the code for reference.
    '''
    if isinstance(self._modelclass, basestring):
      # model must be scanned when it reaches this call
      find = Model._kind_map.get(self._modelclass)
      if find is None:
        raise ValueError('Could not locate model with kind %s' % self._modelclass)
      else:
        self._modelclass = find
    return self._modelclass
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    '''
    dic = super(_BaseStructuredProperty, self).get_meta()
    dic['modelclass'] = self.get_modelclass().get_fields()
    dic['modelclass_kind'] = self.get_modelclass().get_kind()
    dic['value_class'] = self._value_class.__name__
    other = ['_autoload', '_readable', '_updateable', '_deleteable', '_read_arguments']
    for o in other:
      dic[o[1:]] = getattr(self, o)
    return dic
  
  def property_keywords_format(self, kwds, skip_kwds):
    super(_BaseStructuredProperty, self).property_keywords_format(kwds, skip_kwds)
    if 'modelclass' not in skip_kwds:
      model = Model._kind_map.get(kwds['modelclass_kind'])
      if model is None:
        raise FormatError('invalid_kind')
      kwds['modelclass'] = model
    '''
    What to do with this?
    if 'managerclass' not in skip_kwds:
      possible_managers = dict((manager.__name__, manager) for manager in PROPERTY_MANAGERS)
      if kwds['managerclass'] not in possible_managers:
        raise FormatError('invalid_manager_supplied')
      else:
        kwds['managerclass'] = possible_managers.get(kwds['managerclass'])
    '''
  
  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()
  
  def value_format(self, value, path=None):
    if path is None:
      path = self._code_name
    source_value = value
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    out = []
    if not self._repeated:
      if not isinstance(value, dict) and not self._required:
        return util.Nonexistent
      value = [value]
    elif source_value is None:
      return util.Nonexistent
    for v in value:
      ent = self._structured_property_format(v, path)
      out.append(ent)
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out
  
  def _set_value(self, entity, value, override=False):
    # __set__
    if override:
      return super(_BaseStructuredProperty, self)._set_value(entity, value)
    value_instance = self._get_value(entity)
    if self._repeated:
      if value_instance.has_value():
        if value_instance.value:
          current_values = value_instance.value
        else:
          current_values = []
        if value:
          for val in value:
            generate = True
            if val.key:
              for i,current_value in enumerate(current_values):
                if current_value.key == val.key:
                  current_value.populate_from(val)
                  generate = False
                  break
            if generate:
              if not val.key:
                val.generate_unique_key()
                if val._state is None:
                  val._state = 'created'
              current_values.append(val)
          current_values.sort(key=lambda x: x._sequence, reverse=True)
      else:
        current_values = value
        if current_values is None:
          current_values = []
        else:
          for val in current_values:
            if not val.key:
              val.generate_unique_key()
              if val._state is None:
                val._state = 'created'
    elif not self._repeated:
      if value is not None:
        current_values = value_instance.value
        if current_values is not None:
          current_values.populate_from(value)
        else:
          current_values = value
          if not current_values.key:
            current_values.generate_unique_key()
      else:
        current_values = value
    value_instance.set(current_values)
    return super(_BaseStructuredProperty, self)._set_value(entity, current_values)
  
  def _delete_value(self, entity):
    # __delete__
    value_instance = self._get_value(entity)
    value_instance.delete()
  
  def _get_value(self, entity):
    # __get__
    super(_BaseStructuredProperty, self)._get_value(entity)
    value_name = '%s_value' % self._name
    if value_name in entity._values:
      value_instance = entity._values[value_name]
    else:
      value_instance = self._value_class(property_instance=self, entity=entity)
      entity._values[value_name] = value_instance
    return value_instance
  
  def _structured_property_field_format(self, fields, values, path):
    _state = allowed_state(values.get('_state'))
    _sequence = values.get('_sequence')
    key = values.get('key')
    kind = values.get('kind')
    errors = {}
    for value_key, value in values.items():
      field = fields.get(value_key)
      if field:
        if hasattr(field, 'value_format'):
          new_path = '%s.%s' % (path, field._code_name)
          try:
            if hasattr(field, '_structured_property_field_format'):
              val = field.value_format(value, new_path)
            else:
              val = field.value_format(value)
          except FormatError as e:
            if isinstance(e.message, dict):
              for k, v in e.message.iteritems():
                if k not in errors:
                  errors[k] = []
                if isinstance(v, (list, tuple)):
                  errors[k].extend(v)
                else:
                  errors[k].append(v)
            else:
              if e.message not in errors:
                errors[e.message] = []
              errors[e.message].append(new_path)
            continue
          if val is util.Nonexistent:
            del values[value_key]
          else:
            values[value_key] = val
        else:
          del values[value_key]
      else:
        del values[value_key]
    if len(errors):
      raise FormatError(errors)
    if key:
      values['key'] = SuperVirtualKeyProperty(kind=kind, required=True).value_format(key)
    values['_state'] = _state  # Always keep track of _state for rule engine!
    if _sequence is not None:
      values['_sequence'] = _sequence
  
  def _structured_property_format(self, entity_as_dict, path):
    provided_kind_id = entity_as_dict.get('kind')
    fields = self.get_model_fields(kind=provided_kind_id)
    entity_as_dict.pop('class_', None)  # Never allow class_ or any read-only property to be set for that matter.
    try:
      self._structured_property_field_format(fields, entity_as_dict, path)
    except FormatError as e:
      raise FormatError(e.message)
    modelclass = self.get_modelclass(kind=provided_kind_id)
    return modelclass(**entity_as_dict)
  
  @property
  def is_structured(self):
    return True
  
  def initialize(self):
    self.get_modelclass()  # Enforce premature loading of lazy-set model logic to prevent errors.

  def _prepare_for_put(self, entity):
    value_instance = self._get_value(entity)  # For its side effects.
    if value_instance.value is None and self._repeated:
      value_instance.set([])
    super(_BaseStructuredProperty, self)._prepare_for_put(entity)


class BaseProperty(_BaseProperty, Property):
  '''Base property class for all properties capable of having _max_size option.'''


class SuperComputedProperty(_BaseProperty, ComputedProperty):
  pass


class SuperLocalStructuredProperty(_BaseStructuredProperty, LocalStructuredProperty):
  
  _autoload = True # always automatically load structured props since they dont take any io
  
  def __init__(self, *args, **kwargs):
    super(SuperLocalStructuredProperty, self).__init__(*args, **kwargs)
    self._keep_keys = True # all keys must be stored by default


class SuperStructuredProperty(_BaseStructuredProperty, StructuredProperty):
  
  _autoload = True # always automatically load structured props since they dont take any io
  
  def _serialize(self, entity, pb, prefix='', parent_repeated=False, projection=None):
    '''Internal helper to serialize this property to a protocol buffer.
    Subclasses may override this method.
    Args:
      entity: The entity, a Model (subclass) instance.
      pb: The protocol buffer, an EntityProto instance.
      prefix: Optional name prefix used for StructuredProperty
        (if present, must end in '.').
      parent_repeated: True if the parent (or an earlier ancestor)
        is a repeated Property.
      projection: A list or tuple of strings representing the projection for
        the model instance, or None if the instance is not a projection.
    '''
    values = self._get_base_value_unwrapped_as_list(entity)
    for value in values:
      if value is not None:
        name = prefix + self._name + '.' + 'stored_key'
        p = pb.add_raw_property()
        p.set_name(name)
        p.set_multiple(self._repeated or parent_repeated)
        v = p.mutable_value()
        ref = value.key.reference()
        rv = v.mutable_referencevalue()  # A Reference
        rv.set_app(ref.app())
        if ref.has_name_space():
          rv.set_name_space(ref.name_space())
        for elem in ref.path().element_list():
          rv.add_pathelement().CopyFrom(elem)
    return super(SuperStructuredProperty, self)._serialize(
        entity, pb, prefix=prefix, parent_repeated=parent_repeated,
        projection=projection)
  
  def _deserialize(self, entity, p, depth=1):
    stored_key = 'stored_key'
    super(SuperStructuredProperty, self)._deserialize(entity, p, depth)
    basevalues = self._retrieve_value(entity)
    if not self._repeated:
      basevalues = [basevalues]
    for basevalue in basevalues:
      if isinstance(basevalue, _BaseValue):
        # NOTE: It may not be a _BaseValue when we're deserializing a
        # repeated structured property.
        subentity = basevalue.b_val
      if hasattr(subentity, stored_key):
        subentity.key = subentity.store_key
        delattr(subentity, stored_key)
      elif stored_key in subentity._properties:
        subentity.key = subentity._properties[stored_key]._get_value(subentity)
        del subentity._properties[stored_key]


class SuperMultiLocalStructuredProperty(_BaseStructuredProperty, LocalStructuredProperty):
  
  _kinds = None
  
  def __init__(self, *args, **kwargs):
    '''So basically:
    argument: SuperMultiLocalStructuredProperty(('3' or ModelItself, '21' or ModelItself))
    will allow instancing of both 51 and 21 that is provided from the input.
    This property should not be used for datastore. Its specifically used for arguments.
    Currently we do not have the code that would allow this to be saved in datastore:
    Entity.images
    => Image
    => OtherTypeOfEntity
    => OtherTypeOfEntityA
 
    In order to support different instances in the repeated list we would also need to store KIND and implement
    additional logic that will load proper model based on protobuff.
    '''
    args = list(args)
    if isinstance(args[0], (tuple, list)):
      self._kinds = args[0]
      set_model1 = Model._kind_map.get(args[0][0]) # by default just pass the first one
      if set_model1 is not None:
        args[0] = set_model1
    if isinstance(args[0], basestring):
      set_model1 = Model._kind_map.get(args[0]) # by default just pass the first one
      if set_model1 is not None: # do not set it if it wasnt scanned yet
        args[0] = set_model1
    super(SuperMultiLocalStructuredProperty, self).__init__(*args, **kwargs)
  
  def get_modelclass(self, kind=None, **kwds):
    if self._kinds and kind:
      if kind:
        _kinds = []
        for other in self._kinds:
          if isinstance(other, Model):
            _the_kind = other.get_kind()
          else:
            _the_kind = other
          _kinds.append(_the_kind)
        if kind not in _kinds:
          raise ValueError('Expected Kind to be one of %s, got %s' % (_kinds, kind))
        model = Model._kind_map.get(kind)
        return model
    return super(SuperMultiLocalStructuredProperty, self).get_modelclass()
  
  def get_meta(self):
    out = super(SuperMultiLocalStructuredProperty, self).get_meta()
    out['kinds'] = self._kinds
    return out
  
  def property_keywords_format(self, kwds, skip_kwds):
    super(SuperMultiLocalStructuredProperty, self).property_keywords_format(kwds, skip_kwds)
    if 'kinds' not in skip_kwds:
      kwds['kinds'] = map(lambda x: unicode(x), kwds['kinds'])


class SuperRemoteStructuredProperty(_BaseStructuredProperty, Property):
  '''This property is not meant to be used as property storage. It should be always defined as virtual property.
  E.g. the property that never gets saved to the datastore.
  '''
  _indexed = False
  _repeated = False
  _readable = True
  _updateable = True
  _deleteable = True
  _autoload = False
  _value_class = RemoteStructuredPropertyValue
  search = None
  
  def __init__(self, modelclass, name=None, compressed=False, keep_keys=True, **kwds):
    if isinstance(modelclass, basestring):
      set_modelclass = Model._kind_map.get(modelclass)
      if set_modelclass is not None:
        modelclass = set_modelclass
    kwds['generic'] = True
    self.search = kwds.pop('search', None)
    if self.search is None:
      self.search = {'cfg':{
              'filters': {},
              'indexes': [{'ancestor': True, 'filters': [], 'orders': []}],
            }}
    super(SuperRemoteStructuredProperty, self).__init__(name, **kwds)
    self._modelclass = modelclass
  
  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()
  
  def _set_value(self, entity, value):
    # __set__
    value_instance = self._get_value(entity)
    value_instance.set(value)
  
  def _prepare_for_put(self, entity):
    self._get_value(entity)  # For its side effects.

  def initialize(self):
    super(SuperRemoteStructuredProperty, self).initialize()
    default_search_cfg = {'cfg': {'search_arguments': {'kind': self._modelclass.get_kind()},
                          'search_by_keys': False,
                          'filters': {},
                          'indexes': [{'ancestor': True, 'filters': [], 'orders': []}]}}
    util.merge_dicts(self.search, default_search_cfg)
    self.search = SuperSearchProperty(**self.search)

  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    '''
    dic = super(SuperRemoteStructuredProperty, self).get_meta()
    dic['search'] = self.search
    return dic

class SuperReferenceStructuredProperty(SuperRemoteStructuredProperty):
  '''Reference structured is the same as remote, except it uses different default value class and its default flags for
  updating, deleting are always false.
  
  '''
  _value_class = ReferenceStructuredPropertyValue
  _updateable = False
  _deleteable = False
  _addable = False
  
  def __init__(self, *args, **kwargs):
    self._callback = kwargs.pop('callback', None)
    self._target_field = kwargs.pop('target_field', None)
    super(SuperReferenceStructuredProperty, self).__init__(*args, **kwargs)
    self._updateable = False
    self._deleteable = False

  def value_format(self, value, path=None):
    # reference type properties can never be updated by the client
    return util.Nonexistent



class SuperPickleProperty(_BaseProperty, PickleProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    return value


class SuperDateTimeProperty(_BaseProperty, DateTimeProperty):
 
  @property
  def can_be_none(self):
    field = self
    if ((field._auto_now or field._auto_now_add) and field._required):
      return False
    return True
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    out = []
    if not self._repeated:
      value = [value]
    for v in value:
      out.append(datetime.datetime.strptime(v, settings.DATETIME_FORMAT))
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      return search.DateField(name=self.search_document_field_name, value=value)
  
  def resolve_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return value
    else:
      return value
  
  def get_meta(self):
    dic = super(SuperDateTimeProperty, self).get_meta()
    dic['auto_now'] = self._auto_now
    dic['auto_now_add'] = self._auto_now_add
    return dic
  
  def property_keywords_format(self, kwds, skip_kwds):
    super(SuperDateTimeProperty, self).property_keywords_format(kwds, skip_kwds)
    for kwd in ('auto_now', 'auto_now_add'):
      if kwd not in skip_kwds:
        kwds[kwd] = bool(kwds[kwd])


class SuperJsonProperty(_BaseProperty, JsonProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if isinstance(value, basestring):
      return json.loads(value)
    else:
      return value
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: json.dumps(v), value))
    else:
      value = json.dumps(value)
    return search.TextField(name=self.search_document_field_name, value=value)


class SuperTextProperty(_BaseProperty, TextProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if value is None:
      return value
    if self._repeated:
      return [unicode(v) for v in value]
    else:
      return unicode(value)
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(value)
    return search.HtmlField(name=self.search_document_field_name, value=value)


class SuperStringProperty(_BaseProperty, StringProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if self._repeated:
      values = []
      for v in value:
        if v is not None:
          v = unicode(v)
          values.append(v)
      return values
    else:
      if value is not None:
        value = unicode(value)
      return value
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = unicode(' ').join(value)
    return search.TextField(name=self.search_document_field_name, value=unicode(value))


class SuperFloatProperty(_BaseProperty, FloatProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if self._repeated:
      return [float(v) for v in value]
    else:
      return float(value)
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    return search.NumberField(name=self.search_document_field_name, value=value)


class SuperIntegerProperty(_BaseProperty, IntegerProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if self._repeated:
      return [long(v) for v in value]
    else:
      if not self._required and value is None:
        return value
      return long(value)
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    return search.NumberField(name=self.search_document_field_name, value=value)


class SuperKeyProperty(_BaseProperty, KeyProperty):
  '''This property is used on models to reference ndb.Key property.
  Its format function will convert urlsafe string into a ndb.Key and check if the key
  exists in the datastore. If the key does not exist, it will throw an error.
  If key existence feature isn't required, SuperVirtualKeyProperty() can be used in exchange.
  
  '''
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if not self._repeated and not self._required and (value is None or len(value) < 1):
      # if key is not required, and value is either none or length is not larger than 1, its considered as none
      return None
    try:
      if self._repeated:
        out = [Key(urlsafe=v) for v in value]
      else:
        out = [Key(urlsafe=value)]
    except ValueError:
      raise FormatError('malformed_key')
    for key in out:
      if self._kind and key.kind() != self._kind:
        raise FormatError('invalid_kind')
    entities = get_multi(out)
    for i, entity in enumerate(entities):
      if entity is None:
        raise FormatError('not_found')
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: v.urlsafe(), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      try:
        value = value.urlsafe()
      except:
        value = str(value)
      return search.AtomField(name=self.search_document_field_name, value=value)

  def resolve_search_document_field(self, value):
    if value == 'None':
      value = None
    return super(SuperKeyProperty, self).resolve_search_document_field(value)
    
  def get_meta(self):
    dic = super(SuperKeyProperty, self).get_meta()
    dic['kind'] = self._kind
    return dic


class SuperVirtualKeyProperty(SuperKeyProperty):
  '''This property is exact as SuperKeyProperty, except its format function is not making any calls
  to the datastore to check the existence of the provided urlsafe key. It will simply format the
  provided urlsafe key into a ndb.Key.
  
  '''
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if self._repeated:
      if not isinstance(value, (tuple, list)):
        value = [value]
      out = [Key(urlsafe=v) for v in value]
    else:
      if not self._required and value is None:
        return value
      out = [Key(urlsafe=value)]
    for key in out:
      if self._kind and key.kind() != self._kind:
        raise FormatError('invalid_kind')
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out


class SuperKeyFromPathProperty(SuperKeyProperty):
  
  def value_format(self, value):
    try:
      # First it attempts to construct the key from urlsafe
      return super(SuperKeyProperty, self).value_format(value)
    except:
      # Failed to build from urlsafe, proceed with KeyFromPath.
      value = self._property_value_format(value)
      if value is util.Nonexistent:
        return value
      out = []
      if self._repeated:
        for v in value:
          for key_path in v:
            kwds = {}
            try:
              kwds = key_path[1]
            except IndexError:
              pass
            key = Key(*key_path[0], **kwds)
            if self._kind and key.kind() != self._kind:
              raise FormatError('invalid_kind')
            out.append(key)
          entities = get_multi(out)
          for i, entity in enumerate(entities):
            if entity is None:
              raise FormatError('not_found')
      else:
        try:
          kwds = value[1]
        except IndexError:
          pass
        out = Key(*value[0], **kwds)
        if self._kind and out.kind() != self._kind:
          raise FormatError('invalid_kind')
        entity = out.get()
        if entity is None:
          raise FormatError('not_found')
      return out


class SuperBooleanProperty(_BaseProperty, BooleanProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if self._repeated:
      return [bool(long(v)) for v in value]
    else:
      return bool(long(value))
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      value = str(value)
      return search.AtomField(name=self.search_document_field_name, value=value)
  
  def resolve_search_document_field(self, value):
    if self._repeated:
      out = []
      for v in value.split(' '):
        if v == 'True':
          out.append(True)
        else:
          out.append(False)
    else:
      return value == 'True'


class SuperBlobKeyProperty(_BaseProperty, BlobKeyProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    out = []
    if not self._repeated:
      value = [value]
    for v in value:
      # This alone will raise error if the upload is malformed.
      try:
        blob = blobstore.parse_blob_info(v).key()
      except:
        blob = blobstore.BlobKey(v)
      out.append(blob)
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      value = str(value)
      return search.AtomField(name=self.search_document_field_name, value=value)


class SuperDecimalProperty(SuperStringProperty):
  '''Decimal property that accepts only decimal.Decimal.'''
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if (value is None or (isinstance(value, basestring) and not len(value))) and not self._required:
      return util.Nonexistent
    if self._repeated:
      i = 0
      try:
        out = []
        for i, v in enumerate(value):
          out.append(decimal.Decimal(v))
        value = out
      except:
        raise FormatError('invalid_number_on_sequence_%s' % i)
    else:
      try:
        value = decimal.Decimal(value)
      except:
        raise FormatError('invalid_number')
    if value is None:
      raise FormatError('invalid_number')
    return value
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      value = str(value)
      # Specifying this as a number field will either convert it to INT or FLOAT.
      return search.NumberField(name=self.search_document_field_name, value=value)
  
  def _validate(self, value):
    if not isinstance(value, decimal.Decimal):
      raise ValueError('expected_decimal')
  
  def _to_base_type(self, value):
    return str(value)
  
  def _from_base_type(self, value):
    return decimal.Decimal(value)


class SuperSearchProperty(SuperJsonProperty):
  
  def __init__(self, *args, **kwargs):
    '''Filters work like this:
    First you configure SuperSearchProperty with search_arguments, filters and indexes parameters.
    This configuration takes place at the property definition place.
    cfg = {
      'use_search_engine': True,
      'search_arguments': {'kind': '35'...},
      'ancestor_kind': '35',
      'filters': {'field1': SuperStringProperty(required=True)}},  # With this config you define expected filter value property.
      'orders': {'created': {'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}}},  # This parameter is used for search engine default values!
      'indexes': [{'ancestor': True, 'filters': [('field1', [op1, op2]), ('field2', [op1]), ('field3', [op2])], 'orders': [('field1', ['asc', 'desc'])]},
                  {'ancestor': False, 'filters': [('field1', [op1]), ('field2', [op1])], 'orders': [('field1', ['asc', 'desc'])]}]
    }
    search = SuperSearchProperty(cfg=cfg)
    
    Search values that are provided with input will be validated trough SuperSearchProperty().value_format() function.
    Example of search values that are provided in input after processing:
    context.input['search'] = {'kind': '37',
                               'ancestor': 'fjdkahsekuarg4wi784wnvsxiu487',
                               'namespace': 'wjbryj4gr4y57jtgnfj5959',
                               'projection': ['name'],
                               'group_by': ['name'],
                               'options': {'limit': 10000, cursor: '34987hgehevbjeriy3478dsbkjbdskhrsgkugsrkbsg'},
                               'default_options': {'limit': 10000, cursor: '34987hgehevbjeriy3478dsbkjbdskhrsgkugsrkbsg'},
                               'filters': [{'field': 'name', 'operator': '==', 'value': 'Test'}],
                               'orders': [{'field': 'name', 'operator': 'asc'}],
                               'keys': [key1, key2, key3]}
    
    '''
    self._cfg = kwargs.pop('cfg', {})
    super(SuperSearchProperty, self).__init__(*args, **kwargs)
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    dic = super(SuperSearchProperty, self).get_meta()
    dic['cfg'] = self._cfg
    return dic
  
  def _clean_format(self, values):
    allowed_arguments = ['kind', 'ancestor', 'projection',
                         'group_by', 'options', 'default_options',
                         'filters', 'orders', 'keys', 'query_string']
    for value_key, value in values.items():
      if value_key not in allowed_arguments:
        del values[value_key]
  
  def _kind_format(self, values):
    kind = values.get('kind')
    model = Model._kind_map.get(kind)
    if not model:
      raise FormatError('invalid_model_kind')
  
  def _ancestor_format(self, values):
    ancestor = values.get('ancestor')
    if ancestor is not None:
      ancestor_kind = self._cfg.get('ancestor_kind')
      if ancestor_kind is not None:
        # sometimes the parent is not stored in database, so just shallow validation should suffice
        values['ancestor'] = SuperVirtualKeyProperty(kind=ancestor_kind, required=True).value_format(ancestor)
      else:
        del values['ancestor']
  
  def _keys_format(self, values):
    keys = values.get('keys')
    ancestor = values.get('ancestor')
    if keys is not None:
      if self._cfg.get('search_by_keys'):
        values['keys'] = SuperKeyProperty(kind=values['kind'], repeated=True).value_format(keys)
      else:
        del values['keys']
  
  def _projection_group_by_format(self, values):
    def list_format(list_values):
      if not isinstance(list_values, (tuple, list)):
        raise FormatError('not_list')
      remove_list_values = []
      for value in list_values:
        if not isinstance(value, str):
          remove_list_values.append(value)
      for value in remove_list_values:
        list_values.remove(value)
    
    projection = values.get('projection')
    if projection is not None:
      list_format(projection)
    group_by = values.get('group_by')
    if group_by is not None:
      list_format(group_by)
  
  def _filters_orders_format(self, values):
    ''''filters': [{'field': 'name', 'operator': '==', 'value': 'Test'}]
       'orders': [{'field': 'name', 'operator': 'asc'}]
    
    '''
    def _validate(cfg_values, input_values, method):
      # cfg_filters = [('name', ['==', '!=']), ('age', ['>=', '<=']), ('sex', ['=='])]
      # input_filters = [{'field': 'name', 'operator': '==', 'value': 'Mia'}]
      # cfg_orders = [('name', ['asc'])]
      # input_orders = [{'field': 'name', 'operator': 'asc'}]
      if len(cfg_values) != len(input_values):
        raise FormatError('%s_values_mismatch' % method)  # @todo Write this error correctly!
      for i, input_value in enumerate(input_values):  # @todo If input_values length is 0, and above validation passes, than there should not be any errors!?
        cfg_value = cfg_values[i]
        if input_value['field'] != cfg_value[0]:
          raise FormatError('expected_%s_field_%s_at_%s' % (method, cfg_value[0], i))
        if input_value['operator'] not in cfg_value[1]:
          raise FormatError('expected_%s_operator_%s_at_%s' % (method, cfg_value[1], i))
    
    if self._cfg.get('search_by_keys') and 'keys' in values:
      return values
    defaults = self._default
    # if defaults are defined then load them if the user did not supply them
    if not defaults:
      defaults = {}
    ancestor = values.get('ancestor')
    if 'filters' not in values:
      values['filters'] = defaults.get('filters', [])
    if 'orders' not in values:
      values['orders'] = defaults.get('orders', [])
    filters = values.get('filters')
    orders = values.get('orders')
    cfg_filters = self._cfg.get('filters', {})
    cfg_indexes = self._cfg['indexes']
    success = False
    e = 'unknown'
    for cfg_index in cfg_indexes:
      try:
        cfg_index_ancestor = cfg_index.get('ancestor')
        cfg_index_filters = cfg_index.get('filters', [])
        cfg_index_orders = cfg_index.get('orders', [])
        if ancestor is not None:
          if not cfg_index_ancestor:  # @todo Not sure if we have to enforce ancestor if index_cfg.get('ancestor') is True!?
            raise FormatError('ancestor_not_allowed')
        _validate(cfg_index_filters, filters, 'filter')
        _validate(cfg_index_orders, orders, 'order')
        for input_filter in filters:
          input_field = input_filter['field']
          input_value = input_filter['value']
          cfg_field = cfg_filters[input_field]
          input_filter['value'] = cfg_field.value_format(input_value)
        success = True
        break
      except Exception as e:
        pass
    if success is not True:
      if isinstance(e, Exception):
        e = e.message
      raise FormatError(e)
  
  def _datastore_query_options_format(self, values):
    def options_format(options_values):
      for value_key, value in options_values.items():
        if value_key in ['keys_only', 'produce_cursors']:
          if not isinstance(value, bool):
            del options_values[value_key]
        elif value_key == 'limit':
          if not isinstance(value, (int, long)):
            raise FormatError('limit_value_incorrect')
          if value == 0:
            del options_values[value_key]
        elif value_key in ['batch_size', 'prefetch_size', 'deadline']:
          if not isinstance(value, (int, long)):
            del options_values[value_key]
        elif value_key in ['start_cursor', 'end_cursor']:
          try:
            options_values[value_key] = Cursor(urlsafe=value)
          except:
            del options_values[value_key]
        elif value_key == 'read_policy':
          if not isinstance(value, EVENTUAL_CONSISTENCY):  # @todo Not sure if this is ok!? -- @reply i need to check this
            del options_values[value_key]
        else:
          del options_values[value_key]
    
    default_options = values.get('default_options')
    if default_options is not None:
      options_format(default_options)
    options = values.get('options', {})
    if 'limit' not in options.keys():
      raise FormatError('limit_value_missing')
    options_format(options)
  
  def _search_query_orders_format(self, values):
    orders = values.get('orders')
    cfg_orders = self._cfg.get('orders', {})
    if orders is not None:
      for _order in orders:
        cfg_order = cfg_orders.get(_order['field'], {})
        _order['default_value'] = cfg_order.get('default_value', {})
  
  def _search_query_options_format(self, values):
    options = values.get('options', {})
    if 'limit' not in options.keys():
      raise FormatError('limit_value_missing')
    for value_key, value in options.items():
      if value_key == 'limit':
        if not isinstance(value, (int, long)):
          raise FormatError('limit_value_incorrect')
      elif value_key in ['cursor']:
        try:
          options[value_key] = search.Cursor(web_safe_string=value)
        except:
          del options[value_key]
      else:
        del options[value_key]
  
  def value_format(self, values):
    values = super(SuperSearchProperty, self).value_format(values)
    override = self._cfg.get('search_arguments', {})
    util.override_dict(values, override)
    self._clean_format(values)
    self._kind_format(values)
    self._ancestor_format(values)
    self._keys_format(values)
    self._projection_group_by_format(values)
    self._filters_orders_format(values)
    if self._cfg.get('use_search_engine', False):
      self._search_query_orders_format(values)
      self._search_query_options_format(values)
    else:
      self._datastore_query_options_format(values)
    values['property'] = self
    return values
  
  def build_datastore_query_filters(self, value):
    _filters = value.get('filters')
    filters = []
    model = Model._kind_map.get(value.get('kind'))
    if _filters is None:
      return filters
    for _filter in _filters:
      field = util.get_attr(model, _filter['field'])
      op = _filter['operator']
      value = _filter['value']
      # here we could use
      # field._comparison(op, value)
      # https://code.google.com/p/appengine-ndb-experiment/source/browse/ndb/model.py?r=6b3f88b663a82831e9ecee8adbad014ff774c365#831
      if op == '==': # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this also needs improvements
        filters.append(field == value)
      elif op == '!=':
        filters.append(field != value)
      elif op == '>':
        filters.append(field > value)
      elif op == '<':
        filters.append(field < value)
      elif op == '>=':
        filters.append(field >= value)
      elif op == 'IN':
        filters.append(field.IN(value))
      elif op == 'ALL_IN':
        for v in value:
          filters.append(field == v)
      elif op == 'contains':
        letters = list(string.printable)
        try:
          last = letters[letters.index(value[-1].lower()) + 1]
          filters.append(field >= value)
          filters.append(field < last)
        except ValueError as e:  # Value not in the letter scope, šččđčžćč for example.
          filters.append(field == value)
    return filters
  
  def build_datastore_query_orders(self, value):
    _orders = value.get('orders')
    orders = []
    model = Model._kind_map.get(value.get('kind'))
    if _orders is None:
      return orders
    for _order in _orders:
      field = getattr(model, _order['field'])
      op = _order['operator']
      if op == 'asc':
        orders.append(field)
      else:
        orders.append(-field)
    return orders
  
  def build_datastore_query_options(self, value):
    options = value.get('options', {})
    return QueryOptions(**options)
  
  def build_datastore_query_default_options(self, value):
    default_options = value.get('default_options', {})
    return QueryOptions(**default_options)
  
  def build_datastore_query(self, value):
    filters = self.build_datastore_query_filters(value)
    orders = self.build_datastore_query_orders(value)
    default_options = self.build_datastore_query_default_options(value)
    return Query(kind=value.get('kind'), ancestor=value.get('ancestor'),
                 namespace=value.get('namespace'), projection=value.get('projection'),
                 group_by=value.get('group_by'), default_options=default_options).filter(*filters).order(*orders)
  
  def build_search_query_string(self, value):
    query_string = value.get('query_string', '')
    if query_string:
      return query_string
    _filters = value.get('filters')
    filters = []
    kind = value.get('kind')
    if kind:
      filters.append('(kind=' + kind + ')')
    ancestor = value.get('ancestor')
    if ancestor:
      filters.append('(ancestor=' + ancestor + ')')
    for _filter in _filters:
      field = _filter['field']
      op = _filter['operator']
      value = _filter['value']
      if field == 'query_string':
        filters.append(value)
        break
      if op == '==': # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this also needs improvements
        filters.append('(' + field + '=' + value + ')')
      elif op == '!=':
        filters.append('(NOT ' + field + '=' + value + ')')
      elif op == '>':
        filters.append('(' + field + '>' + value + ')')
      elif op == '<':
        filters.append('(' + field + '<' + value + ')')
      elif op == '>=':
        filters.append('(' + field + '>=' + value + ')')
      elif op == '<=':
        filters.append('(' + field + '<=' + value + ')')
      elif op == 'IN':
        filters.append('(' + ' OR '.join(['(' + field + '=' + v + ')' for v in value]) + ')')
    return ' AND '.join(filters)
  
  def build_search_query_sort_options(self, value):
    _orders = value.get('orders')
    options = value.get('options', {})
    direction = {'asc': search.SortExpression.ASCENDING, 'desc': search.SortExpression.DESCENDING}
    orders = []
    for _order in _orders:
      field = _order['field']
      op = _order['operator']
      default_value = _order['default_value']
      orders.append(search.SortExpression(expression=field, direction=direction.get(op),
                                          default_value=default_value.get(op)))
    return search.SortOptions(expressions=orders, limit=options.get('limit'))
  
  def build_search_query_options(self, value):
    sort_options = self.build_search_query_sort_options(value)
    options = value.get('options', {})
    return search.QueryOptions(limit=options.get('limit'),
                               returned_fields=value.get('projection'),
                               sort_options=sort_options, cursor=options.get('cursor'))
  
  def build_search_query(self, value):
    query_string = self.build_search_query_string(value)
    query_options = self.build_search_query_options(value)
    return search.Query(query_string=query_string, options=query_options)


class SuperReferenceProperty(SuperKeyProperty):
  '''This property can be used to read stuff in async mode upon reading entity from protobuff.
  However, this can be also used for storing keys, behaving like SuperKeyProperty.
  Setter value should always be a key, however it can be an entire entity instance from which it will use its .key
  The property will have no substructure permissions. If you want those, use SuperReferenceStructuredProperty
  >>> entity.user = user_key
  Getter usually retrieves entire entity instance,
  or something else can be returned based on the _format_callback option.
  >>> entity.user.email
  Beware with usage of this property. It will automatically start RPC calls in async mode as soon as the
  from_pb and _post_get callback are executed unless autoload is set to False.
  Main difference between SuperReferenceProperty and SuperReferenceStructuredProperty is that
  it does not have structured field permissions, ergo only permissions it has is on itself and
  it will load when _from_pb, _post_get_hook are executed, so its best usage is seen when retrieving multiple entities
  from datastore.
  Plainly said, it serves as automatic custom getter from the database that
  can retreive whatever it wants and how it wants. @see class Record for reference.
  '''
  _value_class = ReferencePropertyValue

  can_be_copied = False
  
  def __init__(self, *args, **kwargs):
    self._callback = kwargs.pop('callback', None)
    self._format_callback = kwargs.pop('format_callback', None)
    self._target_field = kwargs.pop('target_field', None)
    self._autoload = kwargs.pop('autoload', True)
    self._store_key = kwargs.pop('store_key', False)
    if self._callback != None and not callable(self._callback):
      raise ValueError('callback must be a callable, got %s' % self._callback)
    super(SuperReferenceProperty, self).__init__(*args, **kwargs)
  
  def _set_value(self, entity, value):
    # __set__
    value_instance = self._get_value(entity, internal=True)
    value_instance.set(value)
    if not isinstance(value, Key) and hasattr(value, 'key'):
      value = value.key
    if self._store_key:
      super(SuperReferenceProperty, self)._set_value(entity, value)
  
  def _delete_value(self, entity):
    # __delete__
    value_instance = self._get_value(entity, internal=True)
    value_instance.delete()
    if self._store_key:
      return super(SuperReferenceProperty, self)._delete_value(entity)
  
  def _get_value(self, entity, internal=None):
    # __get__
    value_name = '%s_value' % self._name
    if value_name in entity._values:
      value_instance = entity._values[value_name]
    else:
      value_instance = self._value_class(property_instance=self, entity=entity)
      entity._values[value_name] = value_instance
    if internal:
      return value_instance
    return value_instance.read()
  
  def get_output(self):
    dic = super(SuperReferenceProperty, self).get_meta()
    other = ['_target_field', '_store_key']
    for o in other:
      dic[o[1:]] = getattr(self, o)
    return dic

  def value_format(self, value, path=None):
    return util.Nonexistent


class SuperRecordProperty(SuperRemoteStructuredProperty):
  '''Usage: '_records': SuperRecordProperty(Domain or '6')
  '''

  can_be_copied = False

  def __init__(self, *args, **kwargs):
    args = list(args)
    self._modelclass2 = args[0]
    args[0] = Record
    self._repeated = True
    search = kwargs.get('search', {})
    if 'default' not in search:
      search['default'] = {'filters': [], 'orders': [{'field': 'logged', 'operator': 'desc'}]}
    if 'cfg' not in search:
      search['cfg'] = {
          'indexes': [{
            'ancestor': True,
            'filters': [],
            'orders': [('logged', ['desc'])]
          }],
        }
    kwargs['search'] = search
    super(SuperRecordProperty, self).__init__(*args, **kwargs)
    # Implicitly state that entities cannot be updated or deleted.
    self._updateable = False
    self._deleteable = False
    self._duplicable = False
  
  def get_model_fields(self, **kwargs):
    parent = super(SuperRecordProperty, self).get_model_fields(**kwargs)
    parent.update(self._modelclass2.get_fields())
    return parent
  
  def initialize(self):
    super(SuperRecordProperty, self).initialize()
    if isinstance(self._modelclass2, basestring):
      set_modelclass2 = Model._kind_map.get(self._modelclass2)
      if set_modelclass2 is None:
        raise ValueError('Could not locate model with kind %s' % self._modelclass2)
      else:
        self._modelclass2 = set_modelclass2


class SuperPropertyStorageProperty(SuperPickleProperty):
  '''This property is used to store instances of properties to the datastore pickled.
  Incoming data should be formatted exactly as properties get_output function e.g.
  {
      "searchable": null,
      "repeated": false,
      "code_name": "serving_url",
      "search_document_field_name": null,
      "max_size": null,
      "name": "serving_url", # note the friendly name used, this is intentional since all the names will be user-supplied
      "default": null,
      "type": "SuperStringProperty",
      "required": true,
      "is_structured": false,
      "choices": null,
      "verbose_name": null
  }
  the config should be a list of property instances like so:
  JOURNAL_FIELDS = ((orm.SuperStringProperty(default_keyword_here=True, default_keyword2=False...),
                          (... list of kwargs that cannot be set by user...),
                               (... kwargs that are implicitly required -- by default
                                 all kwargs found in property are required.)),  ... ))
  
  '''
  def __init__(self, *args, **kwargs):
    self._cfg = kwargs.pop('cfg', None)
    super(SuperPropertyStorageProperty, self).__init__(*args, **kwargs)
  
  def get_meta(self):
    dic = super(SuperPropertyStorageProperty, self).get_meta()
    dic['cfg'] = self._cfg
    return dic
  
  def value_format(self, value):
    bogus_kwds = ('type', 'is_structured', 'code_name')  # List of kwds which exist, but can not be set as in __init__.
    value = super(SuperPropertyStorageProperty, self).value_format(value)
    if value is util.Nonexistent:
      return value
    out = collections.OrderedDict()
    def gets(c, i, d=None):
      try:
        return c[i]
      except IndexError:
        return d
    parsed = {}
    for name, kwds in value.iteritems():
      field_type = kwds.get('type')
      field = None
      skip_kwargs = None
      required_kwargs = None
      for cfg in self._cfg:
        the_field = cfg[0]
        skip_kwargs = gets(cfg, 1, ())
        required_kwargs = gets(cfg, 2, None)
        if the_field.__class__.__name__ == field_type: # we compare with __name__ since type in get output is always Class.__name___
          field = the_field
          break
      if field is None:
        raise FormatError('invalid_field_type_provided')
      possible_kwargs = tuple(field.get_meta().keys())
      if required_kwargs is None:
        required_kwargs = possible_kwargs
      for name in required_kwargs:
        if name not in kwds and name not in bogus_kwds:
          raise FormatError('missing_keyword_%s' % name)
      for name in kwds.iterkeys():
        if name not in possible_kwargs:
          raise FormatError('unexpected_keyword_%s' % name)
      kwds['name'] = kwds.get('name') # @todo prefix for name
      if kwds['name'] in parsed:
        raise FormatError('duplicate_property_name_%s' % kwds['name'])
      parsed[kwds['name']] = 1
      field.property_keywords_format(kwds, skip_kwargs)
      for bogus in bogus_kwds:
        kwds.pop(bogus, None)
      out[kwds['name']] = field.__class__(**kwds)
    del parsed
    return out


class SuperPluginStorageProperty(SuperPickleProperty):
  
  _kinds = None
  
  def __init__(self, *args, **kwargs):
    args = list(args)
    if isinstance(args[0], (tuple, list)):
      self._kinds = args[0]
    if isinstance(args[0], basestring):
      self._kinds = (args[0],)
    args = args[1:]
    super(SuperPluginStorageProperty, self).__init__(*args, **kwargs)
    
  def _get_value(self, entity):
    values = super(SuperPluginStorageProperty, self)._get_value(entity)
    if values:
      sequence = len(values)
      for val in values:
        val.read()
        sequence -= 1
        val._sequence = sequence
    return values
  
  def _set_value(self, entity, value):
    # __set__
    # plugin storage needs just to generate key if its non existant, it cannot behave like local struct and remote struct
    # because generally its not in its nature to behave like that
    # its just pickling of data with validation.
    for val in value[:]:
      if val._state == 'deleted':
        value.remove(val)
        continue
      if not val.key:
        val.generate_unique_key()
      for field_key, field in val.get_fields().iteritems():
        if hasattr(field, 'is_structured') and field.is_structured:
          structured = getattr(val, field_key)
          structured.pre_update()
    return super(SuperPluginStorageProperty, self)._set_value(entity, value)
  
  def value_format(self, value, path=None):
    if path is None:
      path = self._code_name
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    out = []
    if not isinstance(value, list):
      raise FormatError('expected_list')
    for v in value:
      out.append(self._structured_property_format(v, path))
    return out
  
  def _structured_property_field_format(self, fields, values, path):
    _state = allowed_state(values.get('_state'))
    _sequence = values.get('_sequence')
    key = values.get('key')
    for value_key, value in values.items():
      field = fields.get(value_key)
      if field:
        if hasattr(field, 'value_format'):
          new_path = '%s.%s' % (path, field._code_name)
          try:
            if hasattr(field, '_structured_property_field_format'):
              val = field.value_format(value, new_path)
            else:
              val = field.value_format(value)
          except FormatError as e:
            if isinstance(e.message, dict):
              for k, v in e.message.iteritems():
                if k not in errors:
                  errors[k] = []
                if isinstance(v, (list, tuple)):
                  errors[k].extend(v)
                else:
                  errors[k].append(v)
            else:
              if e.message not in errors:
                errors[e.message] = []
              errors[e.message].append(new_path)
            continue
          if val is util.Nonexistent:
            del values[value_key]
          else:
            values[value_key] = val
        else:
          del values[value_key]
      else:
        del values[value_key]
    if key:
      values['key'] = Key(urlsafe=key)
    values['_state'] = _state  # Always keep track of _state for rule engine!
    if _sequence is not None:
      values['_sequence'] = _sequence
  
  def _structured_property_format(self, entity_as_dict, path):
    provided_kind_id = entity_as_dict.get('kind')
    fields = self.get_model_fields(kind=provided_kind_id)
    entity_as_dict.pop('class_', None)  # Never allow class_ or any read-only property to be set for that matter.
    try:
      self._structured_property_field_format(fields, entity_as_dict, path)
    except FormatError as e:
      raise FormatError(e.message)
    modelclass = self.get_modelclass(kind=provided_kind_id)
    return modelclass(**entity_as_dict)
  
  def get_modelclass(self, kind):
    if self._kinds and kind:
      if kind:
        _kinds = []
        for other in self._kinds:
          if isinstance(other, Model):
            _the_kind = other.get_kind()
          else:
            _the_kind = other
          _kinds.append(_the_kind)
        if kind not in _kinds:
          raise ValueError('Expected Kind to be one of %s, got %s' % (kind, _kinds))
        model = Model._kind_map.get(kind)
        return model
  
  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()
  
  def get_meta(self):
    out = super(SuperPluginStorageProperty, self).get_meta()
    out['kinds'] = self._kinds
    return out
  
  def property_keywords_format(self, kwds, skip_kwds):
    super(SuperPluginStorageProperty, self).property_keywords_format(kwds, skip_kwds)
    if 'kinds' not in skip_kwds:
      kwds['kinds'] = map(lambda x: unicode(x), kwds['kinds'])


#########################################
########## Core system models! ##########
#########################################


class Record(BaseExpando):
  '''
  The class Record overrides some methods because it needs to accomplish proper deserialization of the logged entity.
  It uses Model._clone_properties() in Record.log_entity() and Record._get_property_for(). That is because
  if we do not call that method, the class(cls) scope - Record._properties will be altered which will cause variable leak,
  meaning that simultaneously based on user actions, new properties will be appended to Record._properties, and that will
  cause complete inconsistency and errors while fetching, storing and deleting data. This behavior was noticed upon testing.
  Same approach must be done with the transaction / entry / line scenario, which implements its own logic for new
  properties.
  This implementation will not cause any performance issues or variable leak whatsoever, the _properties will be adjusted to
  be available in "self" - not "cls".
  In the beginning i forgot to look into the Model._fix_up_properties, which explicitly sets cls._properties to {} which then
  allowed mutations to class(cls) scope.

  '''
  _kind = 0
  
  _use_record_engine = False
  _use_rule_engine = False
  
  # Letters for field aliases are provided in order to avoid conflict with logged object fields, and alow scaling!
  logged = SuperDateTimeProperty('l', auto_now_add=True)
  agent = SuperKeyProperty('u', kind='11', required=True)
  action = SuperKeyProperty('a', kind='1', required=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'message': SuperTextProperty('m'),
    'note': SuperTextProperty('n')
    }
  
  _virtual_fields = {
    '_agent': SuperReferenceProperty(callback=lambda self: self._retreive_agent(),
                                     format_callback=lambda self, value: self._retrieve_agent_name(value)),
    '_action': SuperComputedProperty(lambda self: self._retrieve_action())
    }
  
  def _retrieve_agent_name(self, value):
    return value._primary_email
  
  def _retreive_agent(self):
    return self.agent.get_async()
  
  def _retrieve_action(self):
    entity = self
    action_parent = entity.action.parent()
    modelclass = entity._kind_map.get(action_parent.kind())
    action_id = entity.action.id()
    if modelclass and hasattr(modelclass, '_actions'):
      for action in modelclass._actions:
        if entity.action == action.key:
          return '%s.%s' % (modelclass.__name__, action_id)
  
  def _if_properties_are_cloned(self):
    return not (self.__class__._properties is self._properties)
  
  def _retrieve_cloned_name(self, name):
    for _, prop in self._properties.iteritems():
      if name == prop._code_name:
        return prop._name
  
  def __setattr__(self, name, value):
    if self._if_properties_are_cloned():
      _name = self._retrieve_cloned_name(name)
      if _name:
        name = _name
    return super(Record, self).__setattr__(name, value)
  
  def __getattr__(self, name):
    if self._if_properties_are_cloned():
      _name = self._retrieve_cloned_name(name)
      if _name:
        name = _name
    return super(Record, self).__getattr__(name)
  
  def _get_property_for(self, p, indexed=True, depth=0):
    '''Overrides BaseExpando._get_property_for.
    Only way to merge properties from its parent kind to log entity.
    
    '''
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
      # This loads up proper class to deal with the expandos.
      kind = self.key_parent.kind()
      modelclass = self._kind_map.get(kind)
      # We cannot use entity.get_fields here directly as it returns 'friendly_field_name: prop', and we need 'prop._name: prop'.
      # @todo @problem this is not going to work with either Line or Entry.
      properties = dict([(pr._name, pr) for _, pr in modelclass.get_fields().iteritems()])
      # Adds properties from parent class to the log entity making it possible to deserialize them properly.
      prop = properties.get(next)
      if prop:
        # prop = copy.deepcopy(prop) no need to deepcopy prop for now, we'll see.
        self._clone_properties()  # Clone properties, because if we don't, the Record._properties will be overriden!
        self._properties[next] = prop
        self.add_output(prop._code_name)  # Besides rule engine, this must be here as well.
    return super(Record, self)._get_property_for(p, indexed, depth)
  
  def log_entity(self, entity):
    self._clone_properties()  # Clone properties, because if we don't, the Record._properties will be overriden.
    for _, prop in entity._properties.iteritems():  # We do not call get_fields here because all fields that have been written are in _properties.
      value = prop._get_value(entity)
      if isinstance(value, LocalStructuredPropertyValue): # we can only log locally structured data
        value = value.value
      elif hasattr(prop, 'is_structured') and prop.is_structured:
        continue # we cannot log remote structured properties
      prop = copy.deepcopy(prop)
      prop._indexed = False
      self._properties[prop._name] = prop
      try:
        prop._set_value(self, value)
      except TypeError as e:
        setattr(self, prop._code_name, value)
      self.add_output(prop._code_name)
    return self


class Action(BaseExpando):
  
  _kind = 1
  
  name = SuperStringProperty('1', required=True)
  arguments = SuperPickleProperty('2', required=True, default={}, compressed=False)
  active = SuperBooleanProperty('3', required=True, default=True)
  
  _default_indexed = False
  
  def __init__(self, *args, **kwargs):
    self._plugin_groups = kwargs.pop('_plugin_groups', None)
    super(Action, self).__init__(*args, **kwargs)
  
  @classmethod
  def build_key(cls, kind, action_id):
    return Key(kind, 'action', cls._get_kind(), action_id)


class PluginGroup(BaseExpando):
  
  _kind = 2
  
  name = SuperStringProperty('1', required=True)
  subscriptions = SuperKeyProperty('2', kind='1', repeated=True)
  active = SuperBooleanProperty('3', required=True, default=True)
  sequence = SuperIntegerProperty('4', required=True)  # @todo Not sure if we are gonna need this?
  transactional = SuperBooleanProperty('5', required=True, default=False, indexed=False)
  plugins = SuperPickleProperty('6', required=True, default=[], compressed=False)
  
  _default_indexed = False


class Permission(BasePolyExpando):
  '''Base class for all permissions.
  If the futuer deems scaling to be a problem, possible solutions could be to:
  a) Create DomainUserPermissions entity, that will fan-out on DomainUser entity,
  and will contain all permissions for the domain user (based on it's domain role membership) in it;
  b) Transform this class to BasePolyExpando, so it can be indexed and queried (by model kind, by action...),
  and store each permission in datasotre as child entity of DomainUser;
  c) Some other similar pattern.
  
  '''
  _kind = 3
  
  _default_indexed = False


class ActionPermission(Permission):
  
  _kind = 4
  
  model = SuperStringProperty('1', required=True, indexed=False)
  actions = SuperVirtualKeyProperty('2', kind='1', repeated=True, indexed=False)
  executable = SuperBooleanProperty('3', required=False, default=None, indexed=False)
  condition = SuperStringProperty('4', required=True, indexed=False)
  
  def __init__(self, *args, **kwargs):
    super(ActionPermission, self).__init__(**kwargs)
    if len(args):
      model, actions, executable, condition = args
      if not isinstance(actions, (tuple, list)):
        actions = [actions]
      self.model = model
      self.actions = actions
      self.executable = executable
      self.condition = condition
  
  def run(self, entity, **kwargs):
    kwargs['entity'] = entity
    if (self.model == entity.get_kind()):
      for action in self.actions:
        if (entity.get_action(action) is not None) and (util.safe_eval(self.condition, kwargs)) and (self.executable != None):
          entity._action_permissions[action.urlsafe()]['executable'].append(self.executable)


class FieldPermission(Permission):
  
  _kind = 5
  
  model = SuperStringProperty('1', required=True, indexed=False)
  fields = SuperStringProperty('2', repeated=True, indexed=False)
  writable = SuperBooleanProperty('3', required=False, default=None, indexed=False)
  visible = SuperBooleanProperty('4', required=False, default=None, indexed=False)
  condition = SuperStringProperty('5', required=True, indexed=False)
  
  def __init__(self, *args, **kwargs):
    super(FieldPermission, self).__init__(**kwargs)
    if len(args):
      model, fields, writable, visible, condition = args
      if not isinstance(fields, (tuple, list)):
        fields = [fields]
      self.model = model
      self.fields = fields
      self.writable = writable
      self.visible = visible
      self.condition = condition
  
  def run(self, entity, **kwargs):
    kwargs['entity'] = entity
    if (self.model == entity.get_kind()):
      for field in self.fields:
        parsed_field = util.get_attr(entity, '_field_permissions.' + field)
        if parsed_field and (util.safe_eval(self.condition, kwargs)):
          if (self.writable != None):
            parsed_field['writable'].append(self.writable)
          if (self.visible != None):
            parsed_field['visible'].append(self.visible)
