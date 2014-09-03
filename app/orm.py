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
import uuid

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.ndb import *
from google.appengine.ext.ndb import polymodel
from google.appengine.ext.ndb.model import _BaseValue
from google.appengine.ext import blobstore
from google.appengine.api import search, datastore_errors

from app import mem, util, settings


# We always put double underscore for our private functions in order to avoid collision between our code and ndb library.
# For details see: https://groups.google.com/d/msg/appengine-ndb-discuss/iSVBG29MAbY/a54rawIy5DUJ

# We set memory policy for google app engine ndb calls to False, and decide whether to use memcache or not per 'get' call.
ctx = get_context()
ctx.set_memcache_policy(False)
# ctx.set_cache_policy(False)

#############################################
########## System wide exceptions. ##########
#############################################


class ActionDenied(Exception):
  
  def __init__(self, action):
    self.message = {'action_denied': action}


class TerminateAction(Exception):
  pass


class PropertyError(Exception):
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
  # calling in for loop future.get_result() vs Future.wait_all() was not tested if its faster but according to sdk
  # it appears that it will wait for every future to be completed in event loop
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
  _duplicate_appendix
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
  duplicate_appendix
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
  parse_duplicate_appendix
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
  _state = None  # This field is used by rule engine!
  _sequence = None # Internally used for repeated properties
  _use_record_engine = True  # All models are by default recorded!
  _use_rule_engine = True  # All models by default respect rule engine! @todo This control property doen't respect Action control!!
  _use_search_engine = False  # Models can utilize google search services along with datastore search services.
  _parent = None
  _write_custom_indexes = None
  _delete_custom_indexes = None
  _duplicate_appendix = None  # Used to memorize appendix that was used to duplicate this entity. It exists only in duplication runtime.
  
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
  
  def __repr__(self):
    original = 'No, '
    if hasattr(self, '_original') and self._original is not None:
      original = '%s, ' % self._original
    out = super(_BaseModel, self).__repr__()
    out = out.replace('%s(' % self.__class__.__name__, '%s(_original=%s' % (self.__class__.__name__, original))
    virtual_fields = self.get_virtual_fields()
    if virtual_fields:
      out = out[:-1]
      repr = []
      for field_key, field in virtual_fields.iteritems():
        val = getattr(self, field_key, None)
        repr.append('%s=%s' % (field._code_name, val))
      out += '%s)' % ', '.join(repr)
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
        action_key = Key(cls.get_kind(), 'action', '56', action)
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
    dic.update(cls.get_fields())
    return dic
  
  def _make_async_calls(self):
    '''This function is reserved only for SuperReferenceProperty, because it will call its .read_async() method while
    entity is being loaded by from_pb or _post_get_hook.
    
    '''
    entity = self
    if entity.key and entity.key.id():
      for field, field_instance in entity.get_fields().iteritems():
        if isinstance(field_instance, SuperReferenceProperty) and field_instance._autoload:
          manager = field_instance._get_value(entity, internal=True)
          manager.read_async()
  
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
    entity._make_async_calls()
    return entity
  
  def _pre_put_hook(self):
    self.rule_write()
    for field_key, field in self.get_fields().iteritems():
      value = getattr(self, field_key, None)
      if isinstance(value, SuperPropertyManager) and hasattr(value, 'pre_update'):
        value.pre_update()
  
  def _post_put_hook(self, future):
    entity = self
    entity.record()
    for field_key, field in entity.get_fields().iteritems():
      value = getattr(entity, field_key, None)
      if isinstance(value, SuperPropertyManager) and hasattr(value, 'post_update'):
        value.post_update()
    entity.write_search_document()
    # @todo General problem with documents is that they are not transactional, and upon failure of transaction
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
          if isinstance(value, SuperPropertyManager) and hasattr(value, 'delete'):
            value.delete()
  
  @classmethod
  def _post_delete_hook(cls, key, future):
    # Here we can no longer retrieve the deleted entity, so in this case we just delete the document.
    # Problem with deleting the search index in pre_delete_hook is that if the transaciton fails, the
    # index will be deleted anyway.
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
    We cannot copy self.__dict__ because it does not contain all values, because most of them are not initiated yet.
    
    '''
    model = self.__class__
    new_entity = model(_deepcopy=True)
    new_entity.key = copy.deepcopy(self.key)
    for field in self.get_fields():
      if hasattr(self, field):
        value = getattr(self, field, None)
        if isinstance(value, SuperPropertyManager):
          value = value.value
        if isinstance(value, Future) or (isinstance(value, list) and len(value) and isinstance(value[0], Future)):
          continue # this is a problem, we cannot copy futures, we might have to implement flags on properties like
          # copiable=True
          # or deepcopy=True
        else:
          value = copy.deepcopy(value)
        try:
          setattr(new_entity, field, value)
        except ComputedPropertyError as e:
          pass  # This is intentional
        except Exception as e:
          # util.log('__deepcopy__: could not copy %s.%s. Error: %s' % (self.__class__.__name__, field, e))
          pass
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
    self._key = self.build_key(*args, **kwargs)
    return self._key
  
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
    if self.key.parent():
      return self.key.parent().get()
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
        if isinstance(child_entity, SuperPropertyManager):
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
          if isinstance(child_entity, SuperPropertyManager):
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
    # @todo This is the problem with catalog dates...
    if (field_value is None and isinstance(field, SuperDateTimeProperty)) or (hasattr(field, '_updateable') and (not field._updateable and not field._deleteable)):
      return
    if (field_key in permissions):  # @todo How this affects the outcome?? @answer it means that the rule engine will only run on fields that have specification in permissions.
      # For simple (non-structured) fields, if writting is denied, try to roll back to their original value!
      if not hasattr(field, 'is_structured') or not field.is_structured:
        if not permissions[field_key]['writable']:
          try:
            util.log('RuleWrite: revert %s.%s = %s' % (entity.__class__.__name__, field._code_name, field_value))
            setattr(entity, field_key, field_value)
          except TypeError as e:
            util.log('--RuleWrite: setattr error: %s' % e)
          except ComputedPropertyError:
            pass
      else:
        child_entity = getattr(entity, field_key) # child entity can also be none, same destiny awaits it as with field_value
        if isinstance(child_entity, SuperPropertyManager):
          if not child_entity.has_value(): # child entity was not loaded at all, we can skip its validation since user did not supply any value to it
            return
          child_entity = child_entity.value
        if isinstance(field_value, SuperPropertyManager):
          field_value = field_value.value
        is_local_structure = isinstance(field, (SuperStructuredProperty, SuperLocalStructuredProperty))
        field_value_mapping = {}  # Here we hold references of every key from original state.
        if child_entity is None and not field._required:
          # if supplied value from user was none, and this field was not required and if user does not have permission
          # to override it into None, we must revert it completely
          # this is because if we put None on properties that are not required
          if not permissions[field_key]['writable']:
            util.log('RuleWrite: revert %s.%s = %s' % (entity.__class__.__name__, field._code_name, field_value))
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
          if field._repeated:
            to_delete = []
            for current_value in child_entity:
              if not current_value.key or current_value.key.urlsafe() not in field_value_mapping:
                to_delete.append(current_value)
            for delete in to_delete:
              child_entity.remove(delete)
        if not permissions[field_key]['writable'] and not is_local_structure:
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
            cls._rule_write(permissions[field_key], child_entity, child_field_key, child_field, getattr(field_value, child_field_key, None))
  
  def rule_write(self):
    if self._use_rule_engine and hasattr(self, '_field_permissions'):
      if not hasattr(self, '_original'):
        raise PropertyError('Working on entity (%r) without _original. entity.make_original() needs to be called.' % self)
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
          permissions[key] = None
          if not root and not len(value):
            permissions[key] = parent_permissions[key]
  
  @classmethod
  def _rule_override_local_permissions(cls, global_permissions, local_permissions):
    for key, value in local_permissions.iteritems():
      if isinstance(value, dict):
        cls._rule_override_local_permissions(global_permissions[key], local_permissions[key])  # global_permissions[key] will fail in case global and local permissions are (for some reason) out of sync!
      else:
        if key in global_permissions:
          gp_value = global_permissions[key]
          if gp_value is not None and gp_value != value:
            local_permissions[key] = gp_value
        if local_permissions[key] is None:
          local_permissions[key] = False
  
  @classmethod
  def _rule_complement_local_permissions(cls, global_permissions, local_permissions):
    for key, value in global_permissions.iteritems():
      if isinstance(value, dict):
        cls._rule_complement_local_permissions(global_permissions[key], local_permissions[key])  # local_permissions[key] will fail in case global and local permissions are (for some reason) out of sync!
      else:
        if key not in local_permissions:
          local_permissions[key] = value
  
  @classmethod
  def _rule_compile_global_permissions(cls, global_permissions):
    for key, value in global_permissions.iteritems():
      if isinstance(value, dict):
        cls._rule_compile_global_permissions(global_permissions[key])
      else:
        if value is None:
          value = False
        global_permissions[key] = value
  
  @classmethod
  def _rule_compile(cls, global_permissions, local_permissions, strict):
    cls._rule_decide(global_permissions, strict)
    # If local permissions are present, process them.
    if local_permissions:
      cls._rule_decide(local_permissions, strict)
      # Iterate over local permissions, and override them with the global permissions.
      cls._rule_override_local_permissions(global_permissions, local_permissions)
      # Make sure that global permissions are always present.
      cls._rule_complement_local_permissions(global_permissions, local_permissions)
      permissions = local_permissions
    # Otherwise just process global permissions.
    else:
      cls._rule_compile_global_permissions(global_permissions)
      permissions = global_permissions
    return permissions
  
  def rule_prepare(self, global_permissions, local_permissions=None, strict=False, **kwargs):
    '''This method generates permissions situation for the entity object,
    at the time of execution.
    
    '''
    if local_permissions is None:
      local_permissions = []
    self._rule_reset(self)
    for global_permission in global_permissions:
      if isinstance(global_permission, Permission):
        global_permission.run(self, **kwargs)
    # Copy generated entity permissions to separate dictionary.
    global_action_permissions = self._action_permissions.copy()
    global_field_permissions = self._field_permissions.copy()
    # Reset permissions structures.
    self._rule_reset(self)
    local_action_permissions = {}
    local_field_permissions = {}
    if len(local_permissions):
      for local_permission in local_permissions:
        if isinstance(local_permission, Permission):
          local_permission.run(self, **kwargs)
      # Copy generated entity permissions to separate dictionary.
      local_action_permissions = self._action_permissions.copy()
      local_field_permissions = self._field_permissions.copy()
      # Reset permissions structures.
      self._rule_reset(self)
    self._action_permissions = self._rule_compile(global_action_permissions, local_action_permissions, strict)
    self._field_permissions = self._rule_compile(global_field_permissions, local_field_permissions, strict)
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
      if (field_key in read_arguments) or (hasattr(field, '_autoload') and field._autoload):
        # we only read what we're told to or if its a local storage or if its marked for autoload
        field_read_arguments = read_arguments.get(field_key, {})
        if hasattr(field, 'is_structured') and field.is_structured:
          value = getattr(self, field_key)
          value.read_async(field_read_arguments)
          # I don't think these should be keyword arguments because read_arguments is a dictionary that will get
          # passed around as it goes from funciton to funciton, so in that case it may be better not to use keyword arguments,
          # since this just 1 argument approach is perhaps faster.
          futures.append((value, field_read_arguments)) # we have to pack them all for .read()
        elif isinstance(field, SuperReferenceProperty) and field._autoload is False:
          value = field._get_value(self, internal=True)
          value.read_async() # for super-reference we always just call read_async() we do not pack it for future.get_result()
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
  def parse_duplicate_appendix(cls, value):
    # parses value that might contain appendix. throws error if not.
    # @todo this might have to be revised, problem with it that if the custom key is named
    # 24194912412_duplicate_2481412481284_14912941294 it will detect it as a duplicated thing.
    # result will be that the _duplicate_2481412481284_14912941294 will be stripped and a new appendix will be generated
    # 24194912412_<new appendix>
    # but i think this is not big concern since this logic is only employed when we duplicate things, in which case
    # we do not need to keep the original key.
    results = re.findall(r'(.*)_duplicate_.*', value)
    return results[0]
  
  @property
  def duplicate_appendix(self):
    ent = self._root
    if ent._duplicate_appendix is None:
      ent._duplicate_appendix = str(uuid.uuid4())
    return ent._duplicate_appendix
  
  def duplicate_key_id(self, key=None):
    '''If key is provided, it will use its id for construction'''
    if key is None:
      the_id = self.key_id_str
    else:
      the_id = key._id_str
    try:
      the_id = self.parse_duplicate_appendix(the_id)
    except IndexError:
      pass
    return '%s_duplicate_%s' % (the_id, self.duplicate_appendix)
  
  def duplicate(self):
    '''Duplicate this entity.
    Based on entire model configuration and hierarchy, the .duplicate() methods will be called
    on its structured children as well.
    Structured children are any properties that subclass _BaseStructuredProperty.
    Take a look at this example:
    class CatalogImage(Image):
    _virtual_fields = {
    '_descriptions': ndb.SuperStorageStructuredProperty(Descriptions, storage='multi'),
    }
    class Catalog(ndb.BaseModel):
    _virtual_fields = {
    '_images': ndb.SuperStorageStructuredProperty(CatalogImage, storage='multi'),
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
    @todo Referenced entity keys pose a problem when doing duplicates. E.g.
    ProductCopy = Product.duplicate
    CatalogPricetagCopy = CatalogPricetag.duplicate
    CatalogPricetagCopy
     ->product = Product # old product key stays
     ...
    This was solved with making unique duplicate key appendixes + logic that changes those keys implicitly.
    The duplicate appendix is only generated once per root entity duplicated.
    So for duplicating Catalog, appendix would be located on new_catalog._duplicate_appendix.
    
    '''
    new_entity = copy.deepcopy(self) # deep copy will copy all static properties
    new_entity._use_rule_engine = False # we skip the rule engine here because if we dont
    new_entity._parent = self._parent
    the_id = new_entity.duplicate_key_id()
    # user with insufficient permissions on fields might not be in able to write complete copy of entity
    # basically everything that got loaded inb4
    for field_key, field in new_entity.get_fields().iteritems():
      if hasattr(field, 'is_structured') and field.is_structured:
        value = getattr(new_entity, field_key, None)
        if value:
           value.duplicate() # call duplicate for every structured field
    if new_entity.key:
      # '%s_duplicate_%s' % (self.key_id, time.time())
      new_entity.set_key(the_id, parent=self.key_parent, namespace=self.key_namespace)
      # we append _duplicate to the key, this we could change the behaviour of this by implementing something like
      # prepare_duplicate_key()
      # we always set the key last, because if we dont, then ancestor queries wont work because we placed a new key that
      # does not exist yet
    return new_entity
  
  def make_original(self):
    '''This function will make a copy of the current state of the entity
    and put it into _original field. Again note that only get_fields() and key will be copied.
    
    '''
    if self._use_rule_engine:
      self._original = None
      original = copy.deepcopy(self)
      self._original = original
  
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
          try:
            if operation == 'index':
              index.put(documents_partition)
            elif operation == 'unindex':
              index.delete(documents_partition)
          except Exception as e:
            util.log('INDEX FAILED! ERROR: %s' % e)
            pass
  
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
        if isinstance(value, SuperPropertyManager) and hasattr(value, 'value_options') and value.has_value():
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
      dic['key'] = self.key.urlsafe()
      dic['id'] = self.key.id()
      dic['namespace'] = self.key.namespace()
      dic['parent'] = {}
      if self.key.parent():
        parent = self.key.parent()
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
    names = self._output
    try:
      for name in names:
        value = getattr(self, name, None)
        dic[name] = value
    except Exception as e:
      util.log(e, 'exception')
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
        self._properties[prop._name] = prop
        prop._set_value(self, value)
        return prop
    return super(BaseExpando, self).__setattr__(name, value)
  
  def __delattr__(self, name):
    expando_fields = self.get_expando_fields()
    if expando_fields:
      prop = expando_fields.get(name)
      if prop:
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


#################################################
########## Superior Property Managers. ##########
#################################################

# Repository of all managers available.
PROPERTY_MANAGERS = []

class SuperPropertyManager(object):
  
  def __init__(self, property_instance, storage_entity, **kwds):
    self._property = property_instance
    self._entity = storage_entity  # Storage entity of the property.
    self._kwds = kwds
  
  def __repr__(self):
    return '%s(entity=instance of %s, property=%s, property_value=%s, kwds=%s)' % (self.__class__.__name__,
                                                                                   self._entity.__class__.__name__,
                                                                                   self._property.__class__.__name__,
                                                                                   self.value, self._kwds)
  
  @property
  def value(self):
    return getattr(self, '_property_value', None)
  
  @property
  def property_name(self):
    # Retrieves code name of the field for setattr usage. If _code_name is not available it will use _name
    name = self._property._code_name
    if not name:
      name = self._property._name
    return name
  
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
  
  def has_value(self):
    return hasattr(self, '_property_value')
  
  def has_future(self):
    value = self.value
    if isinstance(value, list):
      if len(value):
        value = value[0]
    return isinstance(value, Future)
  
  def get_output(self):
    return self.value


class SuperStructuredPropertyManager(SuperPropertyManager):
  '''SuperStructuredPropertyManager is the proxy class for all properties that want to implement read, update, delete, concept.
  Example:
  entity = entity_key.get()
  entity._images = [image, image, image] # override data
  entity._images.read().append(image) # or mutate
  # note that .read() must be used because getter retrieves StorageEntityManager
  !! Note: You can only retrieve SuperStructuredPropertyManager instance by accessing the property like so:
  entity_manager = entity._images
  entity_manager.read()
  entity_manager.update()
  entity_manager.delete()
  entity._images.set() can be called by either
  setattr(entity, '_images', [image, image])
  or
  entity._images = [image, image, image]
  Process after performing entity.put() which has this property
  entity.put()
  => post_put_hook()
  - all properties who have SuperStructuredPropertyManager capability will perform .update() function.
  
  '''
  
  def __init__(self, property_instance, storage_entity, **kwds):
    super(SuperStructuredPropertyManager, self).__init__(property_instance, storage_entity, **kwds)
    self._property_value_options = {}
    # @todo We might want to change this to something else, but right now it is the most elegant.
  
  @property
  def value(self):
    # overrides the parent value bcuz we have problem with ndb _BaseValue wrapping upon prepare_for_put hook
    # so in that case we always call self.read() to mutate the list properly when needed
    if self.storage_type == 'local': # it happens only on local props
      self._read_local() # recursion is present if we call .read() at return self.value
    return super(SuperStructuredPropertyManager, self).value
  
  @property
  def value_options(self):
    ''''_property_value_options' is used for storing and returning information that
    is related to property value(s). For exmaple: 'more' or 'cursor' parameter in querying.
    
    '''
    return self._property_value_options
  
  @property
  def storage_type(self):
    '''Possible values of _storage variable can be: 'local', 'remote_single', 'remote_multi' values stored.
    'local' is a structured value stored in a parent entity.
    'remote_single' is a single child (fan-out) entity of the parent entity.
    'remote_multi' is set of children entities of the parent entity, they are usualy accessed by ancestor query.
    '''
    return self._property._storage  # @todo Prehaps _storage rename to _storage_type
  
  def set(self, property_value):
    '''We always verify that the property_value is instance
    of the model that is specified in the property configuration.
    
    '''
    if property_value is not None:
      property_value_copy = property_value
      if not self._property._repeated:
        property_value_copy = [property_value_copy]
      for property_value_item in property_value_copy:
        if not isinstance(property_value_item, self._property.get_modelclass()):
          raise PropertyError('Expected %r, got %r' % (self._property.get_modelclass(), property_value_item))
    self._property_value = property_value
    self._set_parent()
  
  def _read_reference(self, read_arguments=None):
    if read_arguments is None:
      read_arguments = {}
    target_field = self._property._storage_config.get('target_field')
    callback = self._property._storage_config.get('callback')
    if not target_field and not callback:
      target_field = self.property_name
    if callback:
      self._property_value = callback(self._entity)
    elif target_field:
      field = getattr(self._entity, target_field)
      if field is None:  # If value is none the key was not set, therefore value must be null.
        self._property_value = None
        return self._property_value
      if not isinstance(field, Key):
        raise PropertyError('Targeted field value must be instance of Key. Got %s' % field)
      if self._property.get_modelclass().get_kind() != field.kind():
        raise PropertyError('Kind must be %s, got %s' % (self._property.get_modelclass().get_kind(), field.kind()))
      self._property_value = field.get_async()
    return self._property_value
  
  def _read_local(self, read_arguments=None):
    '''Every structured/local structured value requires a sequence generated upon reading
    
    '''
    if read_arguments is None:
      read_arguments = {}
    property_value = self._property._get_user_value(self._entity)
    property_value_copy = property_value
    if property_value_copy is not None:
      if not self._property._repeated:
        property_value_copy = [property_value_copy]
      for i, value in enumerate(property_value_copy):
        value._sequence = i
      self._property_value = property_value
    else:
      if self._property._repeated:
        self._property_value = []
  
  def _process_read_async_remote_single(self, read_arguments=None):
    result = self._property_value.get_result()
    if result is None:
      remote_single_key = Key(self._property.get_modelclass().get_kind(), self._entity.key_id_str, parent=self._entity.key)
      result = self._property.get_modelclass()(key=remote_single_key)
    self._property_value = result
  
  def _read_remote_single(self, read_arguments=None):
    '''Remote single storage always follows the same pattern,
    it composes its own key by using its kind, ancestor string id, and ancestor key as parent!
    
    '''
    if read_arguments is None:
      read_arguments = {}
    property_value_key = Key(self._property.get_modelclass().get_kind(), self._entity.key_id_str, parent=self._entity.key)
    self._property_value = property_value_key.get_async()
  
  def _read_remote_multi(self, read_arguments=None):
    if read_arguments is None:
      read_arguments = {}
    config = read_arguments.get('config', {})
    urlsafe_cursor = config.get('cursor')
    limit = config.get('limit', 10)
    order = config.get('order')
    supplied_entities = config.get('entities')
    supplied_keys = config.get('keys')
    if supplied_entities:
      entities = get_multi_clean([entity.key for entity in supplied_entities if entity.key is not None])
      cursor = None
    elif supplied_keys:
      supplied_keys = SuperKeyProperty(kind=self._property.get_modelclass().get_kind(), repeated=True).value_format(supplied_keys)
      for supplied_key in supplied_keys:
        if supplied_key.parent() != self._entity.key:
          raise PropertyError('invalid_parent_for_key_%s' % supplied_key.urlsafe())
      entities = get_multi_clean(supplied_keys)
      cursor = None
    else:
      query = self._property.get_modelclass().query(ancestor=self._entity.key)
      if order:
        order_field = getattr(self._property.get_modelclass(), order['field'])
        if order['direction'] == 'asc':
          query = query.order(order_field)
        else:
          query = query.order(-order_field)
      try:
        cursor = Cursor(urlsafe=urlsafe_cursor)
      except:
        cursor = Cursor()
      if limit == -1:
        entities = query.fetch_async()
      else:
        entities = query.fetch_page_async(limit, start_cursor=cursor)
      cursor = None
    self._property_value = entities
    self._property_value_options['cursor'] = cursor
  
  def _read_deep(self, read_arguments=None):  # @todo Just as entity.read(), this function fails it's purpose by calling both read_async() and read()!!!!!!!!
    '''This function will keep calling .read() on its sub-entity-like-properties until it no longer has structured properties.
    This solves the problem of hierarchy.
    
    '''
    if read_arguments is None:
      read_arguments = {}
    if self.has_value():
      entities = self._property_value
      if not self._property._repeated:
        entities = [entities]
      futures = []
      for entity in entities:
        for field_key, field in entity.get_fields().iteritems():
          if hasattr(field, 'is_structured') and field.is_structured:
            if (field_key in read_arguments) or (hasattr(field, '_autoload') and field._autoload):
              value = getattr(entity, field_key)
              field_read_arguments = read_arguments.get(field_key, {})
              value.read_async(field_read_arguments)
              if value.has_future():
                futures.append((value, field_read_arguments))
      for future, field_read_arguments in futures:
        future.read(field_read_arguments)  # Again, enforce read and re-loop if any.
  
  def read_async(self, read_arguments=None):
    '''Calls storage type specific read function, in order populate _property_value with values.
    'force_read' keyword will always call storage type specific read function.
    However we are not sure if we are gonna need to force read operation.
    
    '''
    if read_arguments is None:
      read_arguments = {}
    if self._property._read_arguments is not None and isinstance(self._property._read_arguments, dict):
      util.merge_dicts(read_arguments, self._property._read_arguments)
    config = read_arguments.get('config', {})
    if self._property._readable:
      if (not self.has_value()) or config.get('force_read'):
        # read_local must be called multiple times because it gets loaded between from_pb and post_get.
        read_function = getattr(self, '_read_%s' % self.storage_type)
        read_function(read_arguments)
      return self.value
  
  def read(self, read_arguments=None):
    if read_arguments is None:
      read_arguments = {}
    if self._property._read_arguments is not None and isinstance(self._property._read_arguments, dict):
      util.merge_dicts(read_arguments, self._property._read_arguments)
    if self._property._readable:
      self.read_async(read_arguments)
      if self.has_future():
        process_read_fn = '_process_read_async_%s' % self.storage_type
        if hasattr(self, process_read_fn):
          process_read_fn = getattr(self, process_read_fn)
          process_read_fn(read_arguments)
        else:
          property_value = []
          if isinstance(self._property_value, list):
            get_async_results(self._property_value)
          elif isinstance(self._property_value, Future):
            property_value = self._property_value.get_result()
            if isinstance(property_value, tuple):
              cursor = property_value[1]
              if cursor:
                cursor = cursor.urlsafe()
              self._property_value = property_value[0]
              self._property_value_options['cursor'] = cursor
              self._property_value_options['more'] = property_value[2]
            else:
              self._property_value = property_value
      format_callback = self._property._storage_config.get('format_callback')
      if callable(format_callback):
        self._property_value = format_callback(self._entity, self._property_value)
      self._set_parent()
      self._read_deep(read_arguments)
      return self.value
  
  def add(self, entities):
    # @todo Is it preferable to branch this function to helper functions, like we do for read, update, delete (_add_local, _add_remote_sigle...)?
    if self._property._repeated:
      if not self.has_value():
        self._property_value = []
      self._property_value.extend(entities)
    else:
      self._property_value = entities
    # Always trigger setattr on the property itself
    setattr(self._entity, self.property_name, self._property_value)
  
  def _pre_update_local(self):
    '''Process local structures.
    
    '''
    if self.has_value():
      if self._property._repeated:
        delete_entities = []
        for entity in self._property_value:
          if entity._state == 'deleted':
            delete_entities.append(entity)
        for delete_entity in delete_entities:
          self._property_value.remove(delete_entity)  # This mutates on the entity and on the _property_value.
      else:
        # We must mutate on the entity itself.
        if self._property_value._state == 'deleted':
          setattr(self._entity, self.property_name, None)  # Comply with expando and virtual fields.
  
  def _pre_update_reference(self):
    pass
  
  def _pre_update_remote_single(self):
    pass
  
  def _pre_update_remote_multi(self):
    pass
  
  def _post_update_local(self):
    pass
  
  def _post_update_reference(self):
    pass
  
  def _post_update_remote_single(self):
    '''Ensure that every entity has the entity ancestor by enforcing it.
    
    '''
    if not hasattr(self._property_value, 'prepare'):
      if self._property_value.key_parent != self._entity.key:
        key_id = self._property_value.key_id
        self._property_value.set_key(key_id, parent=self._entity.key)
    else:
      self._property_value.prepare(parent=self._entity.key)
    if self._property_value._state == 'deleted':
      self._property_value.key.delete()
    else:
      self._property_value.put()
  
  def _post_update_remote_multi(self):
    '''Ensure that every entity has the entity ancestor by enforcing it.
    
    '''
    delete_entities = []
    for entity in self._property_value:
      if not hasattr(entity, 'prepare'):
        if entity.key_parent != self._entity.key:
          key_id = entity.key_id
          entity.set_key(key_id, parent=self._entity.key)
      else:
        entity.prepare(parent=self._entity.key)
      if entity._state == 'deleted':
        delete_entities.append(entity)
    for delete_entity in delete_entities:
      self._property_value.remove(delete_entity)
    delete_multi([entity.key for entity in delete_entities])
    put_multi(self._property_value)
  
  def pre_update(self):
    if self._property._updateable:
      if self.has_value():
        pre_update_function = getattr(self, '_pre_update_%s' % self.storage_type)
        pre_update_function()
      else:
        pass
  
  def post_update(self):
    if self._property._updateable:
      if self.has_value():
        post_update_function = getattr(self, '_post_update_%s' % self.storage_type)
        post_update_function()
      else:
        pass
  
  def _mark_for_delete(self, property_value, property_instance=None):
    '''Mark each of property values for deletion by setting the '_state' to 'deleted'!
    
    '''
    if not property_instance:
      property_instance = self._property
    if not property_instance._repeated:
      property_value = [property_value]
    for value in property_value:
      value._state = 'deleted'
  
  def _delete_local(self):
    self.read()
    self._mark_for_delete(self._property_value)
  
  def _delete_remote_single(self):
    self.read()
    self._property_value.key.delete()
  
  def _delete_remote_multi(self):
    cursor = Cursor()
    limit = 200
    query = self._property.get_modelclass().query(ancestor=self._entity.key)
    while True:
      _entities, cursor, more = query.fetch_page(limit, start_cursor=cursor)
      if len(_entities):
        self._set_parent(_entities)
        delete_multi([entity.key for entity in _entities])
        if not cursor or not more:
          break
      else:
        break
  
  def _delete_reference(self):
    pass
  
  def delete(self):
    '''Calls storage type specific delete function, in order to mark property values for deletion.
    
    '''
    if self._property._deleteable:
      delete_function = getattr(self, '_delete_%s' % self.storage_type)
      delete_function()
  
  def _duplicate_local(self):
    self.read()
    if self._property._repeated:
      entities = []
      for entity in self._property_value:
        entities.append(entity.duplicate())
    else:
      entities = self._property_value.duplicate()
    setattr(self._entity, self.property_name, entities)
  
  def _duplicate_remote_single(self):
    self.read()
    self._property_value = self._property_value.duplicate()
  
  def _duplicate_remote_multi(self):
    '''Fetch ALL entities that belong to this entity.
    On every entity called, .duplicate() function will be called in order to ensure complete recursion.
    
    '''
    entities = []
    _entities = self._property.get_modelclass().query(ancestor=self._entity.key).fetch()
    if len(_entities):
      for entity in _entities:
        self._set_parent(entity)
        entities.append(entity.duplicate())
    self._property_value = entities
  
  def _duplicate_reference(self):
    pass
  
  def duplicate(self):
    '''Calls storage type specific duplicate function.
    
    '''
    duplicate_function = getattr(self, '_duplicate_%s' % self.storage_type)
    duplicate_function()
    self._set_parent()


class SuperReferencePropertyManager(SuperPropertyManager):
  
  def set(self, value):
    if isinstance(value, Key):
      self._property_value = value.get_async()
    elif isinstance(value, Model):
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
        raise PropertyError('Targeted field value must be instance of Key. Got %s' % field)
      if self._property._kind != None and field.kind() != self._property._kind:
        raise PropertyError('Kind must be %s, got %s' % (self._property._kind, field.kind()))
      self._property_value = field.get_async()
    return self.value
  
  def read_async(self):
    if self._property._readable:
      if not self.has_value():
        self._read()
      return self.value
  
  def read(self):
    if self._property._readable:
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


PROPERTY_MANAGERS.extend((SuperStructuredPropertyManager, SuperReferencePropertyManager))


#########################################################
########## Superior properties implementation! ##########
#########################################################


class _BaseProperty(object):
  '''Base property class for all superior properties.'''
  
  _max_size = None
  _value_filters = None
  _searchable = None
  _search_document_field_name = None
  
  def __init__(self, *args, **kwargs):
    self._max_size = kwargs.pop('max_size', self._max_size)
    self._value_filters = kwargs.pop('value_filters', self._value_filters)
    self._searchable = kwargs.pop('searchable', self._searchable)
    self._search_document_field_name = kwargs.pop('search_document_field_name', self._search_document_field_name)
    super(_BaseProperty, self).__init__(*args, **kwargs)
  
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
            raise PropertyError('property_%s_too_long' % k)
        elif k in ('indexed', 'required', 'repeated', 'searchable'):
          v = bool(v)
        elif k == 'choices':
          if v is not None:
            if not isinstance(v, list):
              raise PropertyError('expected_list_for_choices')
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
        raise PropertyError('max_size_exceeded')
    if value is None and self._required:
      raise PropertyError('required')
    if hasattr(self, '_choices') and self._choices:
      if value not in self._choices:
        raise PropertyError('not_in_specified_choices')
  
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
        raise PropertyError('required')
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
  _deleteable = True
  _managerclass = None
  _autoload = True
  
  def __init__(self, *args, **kwargs):
    args = list(args)
    self._readable = kwargs.pop('readable', self._readable)
    self._updateable = kwargs.pop('updateable', self._updateable)
    self._deleteable = kwargs.pop('deleteable', self._deleteable)
    self._managerclass = kwargs.pop('managerclass', self._managerclass)
    self._autoload = kwargs.pop('autoload', self._autoload)
    self._storage_config = kwargs.pop('storage_config', {})
    self._read_arguments = kwargs.pop('read_arguments', {})
    if self._managerclass is None:
      self._managerclass = SuperStructuredPropertyManager
    if not kwargs.pop('generic', None): # this is because storage structured property does not need the logic below
      if isinstance(args[0], basestring):
        set_arg = Model._kind_map.get(args[0])
        if set_arg is not None: # if model is not scanned yet, do not set it to none
          args[0] = set_arg
    self._storage = 'local'
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
        raise PropertyError('Could not locate model with kind %s' % self._modelclass)
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
    dic['managerclass'] = self._managerclass.__name__
    other = ['_autoload', '_readable', '_updateable', '_deleteable', '_storage', '_read_arguments']
    for o in other:
      dic[o[1:]] = getattr(self, o)
    return dic
  
  def property_keywords_format(self, kwds, skip_kwds):
    super(_BaseStructuredProperty, self).property_keywords_format(kwds, skip_kwds)
    if 'modelclass' not in skip_kwds:
      model = Model._kind_map.get(kwds['modelclass_kind'])
      if model is None:
        raise PropertyError('invalid_kind')
      kwds['modelclass'] = model
    if 'managerclass' not in skip_kwds:
      possible_managers = dict((manager.__name__, manager) for manager in PROPERTY_MANAGERS)
      if kwds['managerclass'] not in possible_managers:
        raise PropertyError('invalid_manager_supplied')
      else:
        kwds['managerclass'] = possible_managers.get(kwds['managerclass'])
  
  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()
  
  def value_format(self, value):
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
      out.append(self._structured_property_format(v))
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out
  
  def _set_value(self, entity, value):
    # __set__
    manager = self._get_value(entity)
    current_values = value
    if self._repeated:
      if manager.has_value():
        if manager.value:
          current_values = manager.value
        else:
          current_values = []
        if value:
          for val in value:
            if val.key:
              for i,current_value in enumerate(current_values):
                if current_value.key == val.key:
                  current_values[i] = val
                  break
            else:
              val.generate_unique_key()
              current_values.append(val)
          def sorting_function(val):
            return val._sequence
          current_values = sorted(current_values, key=sorting_function)
      else:
        for val in current_values:
          val.generate_unique_key()
    elif not self._repeated:
      generate = False
      if manager.has_value():
        current_values = manager.value
        if current_values and current_values.key: # ensure that we will always have a key
          value.key = current_values.key
        else:
          generate = True
        current_values = value
      else:
        generate = True
      if generate:
        current_values.generate_unique_key()
    manager.set(current_values)
    return super(_BaseStructuredProperty, self)._set_value(entity, current_values)
  
  def _delete_value(self, entity):
    # __delete__
    manager = self._get_value(entity)
    manager.delete()
    return super(_BaseStructuredProperty, self)._delete_value(entity)
  
  def _get_value(self, entity):
    # __get__
    manager_name = '%s_manager' % self._name
    if manager_name in entity._values:
      manager = entity._values[manager_name]
    else:
      manager = self._managerclass(property_instance=self, storage_entity=entity)
      entity._values[manager_name] = manager
    super(_BaseStructuredProperty, self)._get_value(entity)
    return manager
  
  def _structured_property_field_format(self, fields, values):
    _state = values.get('_state')
    _sequence = values.get('_sequence')
    key = values.get('key')
    for value_key, value in values.items():
      field = fields.get(value_key)
      if field:
        if hasattr(field, 'value_format'):
          val = field.value_format(value)
          if val is util.Nonexistent:
            del values[value_key]
          else:
            values[value_key] = val
        else:
          del values[value_key]
      else:
        del values[value_key]
    if key:
      values['key'] = Key(urlsafe=key) # will throw an error if key was malformed in any way.
    values['_state'] = _state  # Always keep track of _state for rule engine!
    if _sequence is not None:
      values['_sequence'] = _sequence
  
  def _structured_property_format(self, entity_as_dict):
    provided_kind_id = entity_as_dict.get('kind')
    fields = self.get_model_fields(kind=provided_kind_id)
    entity_as_dict.pop('class_', None)  # Never allow class_ or any read-only property to be set for that matter.
    self._structured_property_field_format(fields, entity_as_dict)
    modelclass = self.get_modelclass(kind=provided_kind_id)
    return modelclass(**entity_as_dict)
  
  @property
  def is_structured(self):
    return True
  
  def initialize(self):
    self.get_modelclass()  # Enforce premature loading of lazy-set model logic to prevent errors.


class BaseProperty(_BaseProperty, Property):
  '''Base property class for all properties capable of having _max_size option.'''


class SuperComputedProperty(_BaseProperty, ComputedProperty):
  pass


class SuperLocalStructuredProperty(_BaseStructuredProperty, LocalStructuredProperty):
  
  def __init__(self, *args, **kwargs):
    super(SuperLocalStructuredProperty, self).__init__(*args, **kwargs)
    self._keep_keys = True # always keep keys!


class SuperStructuredProperty(_BaseStructuredProperty, StructuredProperty):
  
  def _serialize(self, entity, pb, prefix='', parent_repeated=False,
                   projection=None):  This method violates identation (uncommented to bring attention)!
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
        subentity.key = subentity._properties.get(stored_key)._get_value(subentity)
        del subentity._properties[stored_key]


class SuperMultiLocalStructuredProperty(_BaseStructuredProperty, LocalStructuredProperty):
  
  _kinds = None
  
  def __init__(self, *args, **kwargs):
    '''So basically:
    argument: SuperMultiLocalStructuredProperty(('52' or ModelItself, '21' or ModelItself))
    will allow instancing of both 51 and 21 that is provided from the input.
    This property should not be used for datastore. Its specifically used for arguments.
    Currently we do not have the code that would allow this to be saved in datastore:
    Entity.images
    => Image
    => OtherTypeOfImage
    => AnotherTypeOfImage
    We only support
    Entity.images
    => Image
    => Image
    => Image
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
          raise PropertyError('Expected Kind to be one of %s, got %s' % (_kinds, kind))
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


class SuperPickleProperty(_BaseProperty, PickleProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    return value


class SuperDateTimeProperty(_BaseProperty, DateTimeProperty):
  
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
      return [unicode(v) for v in value]
    else:
      return unicode(value)
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(value)
    return search.TextField(name=self.search_document_field_name, value=value)


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
      raise PropertyError('malformed_key_%s' % value)
    for key in out:
      if self._kind and key.kind() != self._kind:
        raise PropertyError('invalid_kind')
    entities = get_multi(out)
    for i, entity in enumerate(entities):
      if entity is None:
        raise PropertyError('not_found_%s' % out[i].urlsafe())
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
        raise PropertyError('invalid_kind')
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
      assert isinstance(value, list) == True
      if self._repeated:
        for v in value:
          for key_path in v:
            key = Key(*key_path)
            if self._kind and key.kind() != self._kind:
              raise PropertyError('invalid_kind')
            out.append(key)
          entities = get_multi(out)
          for i, entity in enumerate(entities):
            if entity is None:
              raise PropertyError('not_found_%s' % out[i].urlsafe())
      else:
        out = Key(*value)
        if self._kind and out.kind() != self._kind:
          raise PropertyError('invalid_kind')
        entity = out.get()
        if entity is None:
          raise PropertyError('not_found_%s' % out.urlsafe())
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
    if self._repeated:
      value = [decimal.Decimal(v) for v in value]
    else:
      value = decimal.Decimal(value)
    if value is None:
      raise PropertyError('invalid_number')
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
      raise PropertyError('expected_decimal')  # Perhaps, here should be some other type of exception?
  
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
      raise PropertyError('invalid_model_kind_%s' % kind)
  
  def _ancestor_format(self, values):
    ancestor = values.get('ancestor')
    if ancestor is not None:
      ancestor_kind = self._cfg.get('ancestor_kind')
      if ancestor_kind is not None:
        values['ancestor'] = SuperKeyProperty(kind=ancestor_kind, required=True).value_format(ancestor)
      else:
        del values['ancestor']
  
  def _keys_format(self, values):
    keys = values.get('keys')
    if keys is not None:
      if self._cfg.get('search_by_keys'):
        values['keys'] = SuperKeyProperty(kind=values['kind'], repeated=True).value_format(keys)
      else:
        del values['keys']
  
  def _projection_group_by_format(self, values):
    def list_format(list_values):
      if not isinstance(list_values, (tuple, list)):
        raise PropertyError('not_list')
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
        raise PropertyError('%s_values_mismatch' % method)  # @todo Write this error correctly!
      for i, input_value in enumerate(input_values):  # @todo If input_values length is 0, and above validation passes, than there should not be any errors!?
        cfg_value = cfg_values[i]
        if input_value['field'] != cfg_value[0]:
          raise PropertyError('expected_field_%s_%s_%s' % (method, cfg_value[0], i))
        if input_value['operator'] not in cfg_value[1]:
          raise PropertyError('expected_operator_%s_%s_%s' % (method, cfg_value[1], i))
    
    if self._cfg.get('search_by_keys') and 'keys' in values:
      return values
    ancestor = values.get('ancestor')
    filters = values.get('filters', [])
    orders = values.get('orders', [])
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
            raise PropertyError('ancestor_not_allowed')
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
      raise PropertyError(e)
  
  def _datastore_query_options_format(self, values):
    def options_format(options_values):
      for value_key, value in options_values.items():
        if value_key in ['keys_only', 'produce_cursors']:
          if not isinstance(value, bool):
            del options_values[value_key]
        elif value_key == 'limit':
          if not isinstance(value, (int, long)):
            raise PropertyError('limit_value_incorrect')
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
      raise PropertyError('limit_value_missing')
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
      raise PropertyError('limit_value_missing')
    for value_key, value in options.iteritems():
      if value_key == 'limit':
        if not isinstance(value, (int, long)):
          raise PropertyError('limit_value_incorrect')
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
    util.merge_dicts(values, override)
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
      #if field == 'query_string':
        #filters.append(value)
        #break
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


class SuperStorageStructuredProperty(_BaseStructuredProperty, Property):
  '''This property is not meant to be used as property storage. It should be always defined as virtual property.
  E.g. the property that never gets saved to the datastore.
  
  '''
  _indexed = False
  _modelclass = None
  _repeated = False
  _readable = True
  _updateable = True
  _deleteable = True
  _managerclass = None
  _autoload = False
  
  def __init__(self, modelclass, name=None, compressed=False, keep_keys=True, **kwds):
    storage = kwds.pop('storage')
    if isinstance(modelclass, basestring):
      set_modelclass = Model._kind_map.get(modelclass)
      if set_modelclass is not None:
        modelclass = set_modelclass
    kwds['generic'] = True
    super(SuperStorageStructuredProperty, self).__init__(name, **kwds)
    self._modelclass = modelclass
    # Calling this init will also call _BaseStructuredProperty.__init__ and overide _storage into 'local' always.
    # That's why we deal with _storage after inherited init methods are finished.
    self._storage = storage
    # we use storage_config dict instead of keywords,
    # because we cannot forsee how many key-values we can invent for per-storage type
    if self._storage in ['remote_multi']:
      self._repeated = True  # Always enforce repeated on multi entity storage engine!
  
  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()
  
  def _set_value(self, entity, value):
    # __set__
    manager = self._get_value(entity)
    manager.set(value)
  
  def _get_value(self, entity):
    # __get__
    manager_name = '%s_manager' % self._name
    if manager_name in entity._values:
      return entity._values[manager_name]
    manager = self._managerclass(property_instance=self, storage_entity=entity)
    entity._values[manager_name] = manager
    return manager
  
  def _prepare_for_put(self, entity):
    self._get_value(entity)  # For its side effects.


class SuperReferenceProperty(SuperKeyProperty):
  '''This property can be used to read stuff in async mode upon reading entity from protobuff.
  However, this can be also used for storing keys, behaving like SuperKeyProperty.
  Setter value should always be a key, however it can be an entire entity instance from which it will use its .key.
  >>> entity.user = user_key
  Getter usually retrieves entire entity instance,
  or something else can be returned based on the _format_callback option.
  >>> entity.user.email
  Beware with usage of this property. It will automatically start RPC calls in async mode as soon as the
  from_pb and _post_get callback are executed unless autoload is set to False.
  '''
  _readable = True
  _updateable = True
  _deletable = True
  
  def __init__(self, *args, **kwargs):
    self._callback = kwargs.pop('callback', None)
    self._format_callback = kwargs.pop('format_callback', None)
    self._target_field = kwargs.pop('target_field', None)
    self._readable = kwargs.pop('readable', True)
    self._updateable = kwargs.pop('updateable', True)
    self._deleteable = kwargs.pop('deleteable', True)
    self._autoload = kwargs.pop('autoload', True)
    self._store_key = kwargs.pop('store_key', False)
    if self._callback != None and not callable(self._callback):
      raise PropertyError('"callback" must be a callable, got %s' % self._callback)
    if self._format_callback is None or not callable(self._format_callback):
      raise PropertyError('"format_callback" must be provided and callable, got %s' % self._format_callback)
    super(SuperReferenceProperty, self).__init__(*args, **kwargs)
  
  def _set_value(self, entity, value):
    # __set__
    manager = self._get_value(entity, internal=True)
    manager.set(value)
    if not isinstance(value, Key) and hasattr(value, 'key'):
      value = value.key
    if self._store_key:
      return super(SuperReferenceProperty, self)._set_value(entity, value)
  
  def _delete_value(self, entity):
    # __delete__
    manager = self._get_value(entity, internal=True)
    manager.delete()
    if self._store_key:
      return super(SuperReferenceProperty, self)._delete_value(entity)
  
  def _get_value(self, entity, internal=None):
    # __get__
    manager_name = '%s_manager' % self._name
    if manager_name in entity._values:
      manager = entity._values[manager_name]
    else:
      manager = SuperReferencePropertyManager(property_instance=self, storage_entity=entity)
      entity._values[manager_name] = manager
    if internal:  # If internal is true, always retrieve manager.
      return manager
    if not manager.has_value():
      return manager
    else:
      return manager.read()
  
  def get_output(self):
    dic = super(SuperReferenceProperty, self).get_meta()
    other = ['_target_field', '_readable', '_updateable', '_deleteable',  '_autoload',  '_store_key']
    for o in other:
      dic[o[1:]] = getattr(self, o)
    return dic


class SuperRecordProperty(SuperStorageStructuredProperty):
  '''Usage: '_records': SuperRecordProperty(Domain or '6')
  
  '''
  def __init__(self, *args, **kwargs):
    args = list(args)
    self._modelclass2 = args[0]
    args[0] = Record
    kwargs['storage'] = 'remote_multi'
    read_arguments = kwargs.get('read_arguments', {})
    if 'config' not in read_arguments:
      read_arguments['config'] = {} # enforce logged and direction.
    read_arguments['config']['order'] = {'field': 'logged', 'direction': 'desc'}
    kwargs['read_arguments'] = read_arguments
    super(SuperRecordProperty, self).__init__(*args, **kwargs)
    # Implicitly state that entities cannot be updated or deleted.
    self._updateable = False
    self._deleteable = False
  
  def get_model_fields(self, **kwargs):
    parent = super(SuperRecordProperty, self).get_model_fields(**kwargs)
    parent.update(self._modelclass2.get_fields())
    return parent
  
  def initialize(self):
    super(SuperRecordProperty, self).initialize()
    if isinstance(self._modelclass2, basestring):
      set_modelclass2 = Model._kind_map.get(self._modelclass2)
      if set_modelclass2 is None:
        raise PropertyError('Could not locate model with kind %s' % self._modelclass2)
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
        raise PropertyError('invalid_field_type_provided')
      possible_kwargs = tuple(field.get_meta().keys())
      if required_kwargs is None:
        required_kwargs = possible_kwargs
      for name in required_kwargs:
        if name not in kwds and name not in bogus_kwds:
          raise PropertyError('missing_keyword_%s' % name)
      for name in kwds.iterkeys():
        if name not in possible_kwargs:
          raise PropertyError('unexpected_keyword_%s' % name)
      kwds['name'] = kwds.get('name') # @todo prefix for name
      if kwds['name'] in parsed:
        raise PropertyError('duplicate_property_name_%s' % kwds['name'])
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
  
  def _set_value(self, entity, value):
    # __set__
    current_values = self._get_value(entity)
    if value:
      for val in value:
        if val.key:
          for i,current_value in enumerate(current_values):
            if current_value.key == val.key:
              current_values[i] = val
              break
        else:
          val.generate_unique_key() # for new values always generate new keys
          current_values.append(val)
      def sorting_function(val):
        return val._sequence
      current_values = sorted(current_values, key=sorting_function)
    return super(SuperPluginStorageProperty, self)._set_value(entity, current_values)
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    out = []
    if not isinstance(value, list):
      raise PropertyError('expected_list')
    for v in value:
      out.append(self._structured_property_format(v))
    return out
  
  def _structured_property_field_format(self, fields, values):
    _state = values.get('_state')
    _sequence = values.get('_sequence')
    key = values.get('key')
    for value_key, value in values.items():
      field = fields.get(value_key)
      if field:
        if hasattr(field, 'value_format'):
          val = field.value_format(value)
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
  
  def _structured_property_format(self, entity_as_dict):
    provided_kind_id = entity_as_dict.get('kind')
    fields = self.get_model_fields(kind=provided_kind_id)
    entity_as_dict.pop('class_', None)  # Never allow class_ or any read-only property to be set for that matter.
    self._structured_property_field_format(fields, entity_as_dict)
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
          raise PropertyError('Expected Kind to be one of %s, got %s' % (kind, _kinds))
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


class Action(BaseExpando):
  
  _kind = 56
  
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
  
  _kind = 52
  
  name = SuperStringProperty('1', required=True)
  subscriptions = SuperKeyProperty('2', kind='56', repeated=True)
  active = SuperBooleanProperty('3', required=True, default=True)
  sequence = SuperIntegerProperty('4', required=True)  # @todo Not sure if we are gonna need this?
  transactional = SuperBooleanProperty('5', required=True, default=False, indexed=False)
  plugins = SuperPickleProperty('6', required=True, default=[], compressed=False)
  
  _default_indexed = False


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
class Record(BaseExpando):
  
  _kind = 5
  
  _use_record_engine = False
  _use_rule_engine = False
  
  # Letters for field aliases are provided in order to avoid conflict with logged object fields, and alow scaling!
  logged = SuperDateTimeProperty('l', auto_now_add=True)
  agent = SuperKeyProperty('u', kind='0', required=True)
  action = SuperKeyProperty('a', kind='56', required=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'message': SuperTextProperty('m'),
    'note': SuperTextProperty('n')
    }
  
  _virtual_fields = {
    '_agent': SuperReferenceProperty(callback=lambda self: self._retreive_agent(),
                                     format_callback=lambda self, value: self._retrieve_agent_name(value)),
    '_action': SuperReferenceProperty(callback=lambda self: self._retrieve_action(), format_callback=lambda self, value: value)
    }
  
  def _retrieve_agent_name(self, value):
    # We have to involve Domain User here, although ndb should be unavare of external models!
    if value.key.kind() == '8':
      return value.name
    else:
      return value._primary_email
  
  def _retreive_agent(self):
    # We have to involve Domain User here, although ndb should be unavare of external models!
    entity = self
    if entity.key_namespace and entity.agent.id() != 'system':
      domain_user_key = Key('8', str(entity.agent.id()), namespace=entity.key_namespace)
      return domain_user_key.get_async()
    else:
      return entity.agent.get_async()
  
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
      if isinstance(value, SuperPropertyManager):
        value = value.value
      # prop = copy.deepcopy(prop) no need to deepcopy prop for now, we'll see.
      self._properties[prop._name] = prop
      try:
        prop._set_value(self, value)
      except TypeError as e:
        setattr(self, prop._code_name, value)
      self.add_output(prop._code_name)
    return self


class Permission(BasePolyExpando):
  '''Base class for all permissions.
  If the futuer deems scaling to be a problem, possible solutions could be to:
  a) Create DomainUserPermissions entity, that will fan-out on DomainUser entity,
  and will contain all permissions for the domain user (based on it's domain role membership) in it;
  b) Transform this class to BasePolyExpando, so it can be indexed and queried (by model kind, by action...),
  and store each permission in datasotre as child entity of DomainUser;
  c) Some other similar pattern.
  
  '''
  _kind = 78
  
  _default_indexed = False


class ActionPermission(Permission):
  
  _kind = 79
  
  model = SuperStringProperty('1', required=True, indexed=False)
  actions = SuperVirtualKeyProperty('2', kind='56', repeated=True, indexed=False)
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
  
  _kind = 80
  
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
