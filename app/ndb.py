# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import decimal
import datetime
import importlib
import json
import copy
import collections
import dis
import string

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.ndb import *
from google.appengine.ext.ndb import polymodel
from google.appengine.ext import blobstore

from app import util, settings


# We always put double underscore for our private functions in order to avoid collision between our code and ndb library.
# For details see: https://groups.google.com/d/msg/appengine-ndb-discuss/iSVBG29MAbY/a54rawIy5DUJ

# We set memory policy for google app engine ndb calls to False, and decide whether to use memcache or not per 'get' call.
ctx = get_context()
ctx.set_memcache_policy(False)
# ctx.set_cache_policy(False)


#############################################
########## System wide exceptions. ##########
#############################################


class TerminateAction(Exception):
  pass


class PropertyError(Exception):
  pass


############################################################
########## System wide data processing functions! ##########
############################################################


def make_complete_name(entity, name_property, parent_property=None, separator=None):
  '''Returns a string build by joining individual string values,
  extracted from the same property traced in a chain of interrelated entities.
  
  '''
  if separator is None:
    separator = unicode(' / ')
  path = entity
  names = []
  while True:
    parent = None
    if parent_property is None:
      parent_key = path.key.parent()
      parent = parent_key.get()
    else:
      parent_key = getattr(path, parent_property)
      if parent_key:
        parent = parent_key.get()
    if not parent:
      names.append(getattr(path, name_property))
      break
    else:
      names.append(getattr(path, name_property))
      path = parent
  names.reverse()
  return separator.join(names)


def factory(complete_path):
  '''Retrieves model by its module path,
  (e.g. model = factory('app.models.base.Record'), where 'model' will be Record class).
  
  '''
  path_elements = complete_path.split('.')
  module_path = '.'.join(path_elements[:-1])
  model_name = path_elements[-1]
  try:
    module = importlib.import_module(module_path)
    model = getattr(module, model_name)
  except Exception as e:
    util.logger('Failed to import %s. Error: %s.' % (complete_path, e), 'exception')
    return None
  return model


def is_structured_field(field):
  '''Checks if the provided field is instance of one of the structured properties,
  and if the '_modelclass' is set.
  
  '''
  return isinstance(field, (SuperStructuredProperty, SuperLocalStructuredProperty, SuperPropertyManager)) and field._modelclass


_CODES = ['POP_TOP', 'ROT_TWO', 'ROT_THREE', 'ROT_FOUR', 'DUP_TOP', 'BUILD_LIST',
          'BUILD_MAP', 'BUILD_TUPLE', 'LOAD_CONST', 'RETURN_VALUE',
          'STORE_SUBSCR', 'UNARY_POSITIVE', 'UNARY_NEGATIVE', 'UNARY_NOT',
          'UNARY_INVERT', 'BINARY_POWER', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
          'BINARY_FLOOR_DIVIDE', 'BINARY_TRUE_DIVIDE', 'BINARY_MODULO',
          'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_LSHIFT', 'BINARY_RSHIFT',
          'BINARY_AND', 'BINARY_XOR', 'BINARY_OR', 'STORE_MAP', 'LOAD_NAME',
          'COMPARE_OP', 'LOAD_ATTR', 'STORE_NAME', 'GET_ITER',
          'FOR_ITER', 'LIST_APPEND', 'JUMP_ABSOLUTE', 'DELETE_NAME',
          'JUMP_IF_TRUE', 'JUMP_IF_FALSE', 'JUMP_IF_FALSE_OR_POP',
          'JUMP_IF_TRUE_OR_POP', 'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
          'BINARY_SUBSCR', 'JUMP_FORWARD']


_ALLOWED_CODES = set(dis.opmap[x] for x in _CODES if x in dis.opmap)


def _compile_source(source):
  comp = compile(source, '', 'eval')
  codes = []
  co_code = comp.co_code
  i = 0
  while i < len(co_code):
    code = ord(co_code[i])
    codes.append(code)
    if code >= dis.HAVE_ARGUMENT:
      i += 3
    else:
      i += 1
  for code in codes:
    if code not in _ALLOWED_CODES:
      raise ValueError('opcode %s not allowed' % dis.opname[code])
  return comp


def safe_eval(source, data=None):
  if '__subclasses__' in source:
    raise ValueError('__subclasses__ not allowed')
  comp = _compile_source(source)
  try:
    return eval(comp, {'__builtins__': {'True': True, 'False': False, 'str': str,
                                        'globals': locals, 'locals': locals, 'bool': bool,
                                        'dict': dict, 'round': round, 'Decimal': decimal.Decimal}}, data)
  except Exception as e:
    raise Exception('Failed to process code "%s" error: %s' % ((source, data), e))


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
Key.entity = property(_get_entity)
Key.namespace_entity = property(_get_namespace_entity)  # @todo Can we do this?
Key.parent_entity = property(_get_parent_entity)  # @todo Can we do this?


################################################################
########## Base extension classes for all ndb models! ##########
################################################################


class _BaseModel(object):
  
  _state = None  # This field is used by rule engine!
  _use_record_engine = True  # All models are by default recorded!
  _use_rule_engine = True  # All models by default respect rule engine!
  
  def __init__(self, *args, **kwargs):
    _deepcopied = '_deepcopy' in kwargs
    if _deepcopied:
      kwargs.pop('_deepcopy')
    super(_BaseModel, self).__init__(*args, **kwargs)
    if not _deepcopied:
      self.make_original()
    self._output = []
    for key in self.get_fields():
      self.add_output(key)
  
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
  
  @classmethod
  def get_kind(cls):
    return cls._get_kind()
  
  @classmethod
  def get_actions(cls):
    actions = {}
    class_actions = getattr(cls, '_actions', [])
    for action in class_actions:
      actions[action.key.urlsafe()] = action
    return actions
  
  @classmethod
  def get_plugin_groups(cls, action):
    return getattr(action, '_plugin_groups', [])
  
  @classmethod
  def get_fields(cls):
    fields = {}
    for prop_key, prop in cls._properties.items():
      fields[prop._code_name] = prop
    virtual_fields = cls.get_virtual_fields()
    if virtual_fields:
      fields.update(virtual_fields)
    if hasattr(cls, 'get_expando_fields'):
      expando_fields = cls.get_expando_fields()
      if expando_fields:
        fields.update(expando_fields)
    return fields
  
  @classmethod
  def get_virtual_fields(cls):
    if hasattr(cls, '_virtual_fields'):
      for prop_key, prop in cls._virtual_fields.items():
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
    dic['_actions'] = getattr(cls, '_actions', {})
    dic.update(cls.get_fields())
    return dic
  
  @classmethod
  def prepare_field(cls, entity, field_path):
    fields = str(field_path).split('.')
    last_field = fields[-1]
    drill = fields[:-1]
    i = -1
    while not last_field:
      i = i - 1
      last_field = fields[i]
      drill = fields[:i]
    for field in drill:
      if field:
        if isinstance(entity, dict):
          try:
            entity = entity[field]
          except KeyError as e:
            return None
        elif isinstance(entity, list):
          try:
            entity = entity[int(field)]
          except IndexError as e:
            return None
        else:
          try:
            entity = getattr(entity, field)
          except ValueError as e:
            return None
    return (entity, last_field)
  
  def get_field(self, field_path):
    result = self.prepare_field(self, field_path)
    if result == None:
      return None
    entity, last_field = result
    if isinstance(entity, dict):
      return entity.get(last_field, None)
    elif isinstance(entity, list):
      try:
        return entity[int(last_field)]
      except:
        return None
    else:
      return getattr(entity, last_field, None)
  
  def _make_async_calls(self):
    entity = self
    if entity.key and entity.key.id():
      for field, field_instance in entity.get_fields().items():
        if isinstance(field_instance, SuperPropertyManager):
          manager = field_instance._get_value(entity, internal=True)
          manager.read_async()
  
  @classmethod
  def _post_get_hook(cls, key, future):
    entity = future.get_result()
    if entity is not None and entity.key:  # @todo http://stackoverflow.com/questions/2209755/python-operation-vs-is-not
      entity.make_original()
      entity._make_async_calls()
  
  @classmethod
  def _from_pb(cls, pb, set_key=True, ent=None, key=None):
    entity = super(_BaseModel, cls)._from_pb(pb, set_key, ent, key)
    entity.make_original()
    entity._make_async_calls()
    return entity
  
  def _pre_put_hook(self):
    if self._use_rule_engine:
      if not hasattr(self, '_original'):
        raise PropertyError('Working on entity (%r) without _original.' % self)
      self.rule_write()
    for field in self.get_fields():
      value = getattr(self, field)
      if isinstance(value, SuperPropertyManager):
        value.pre_update()
  
  def _post_put_hook(self, future):
    entity = self
    entity.record_write()
    for field in entity.get_fields():
      value = getattr(entity, field)
      if isinstance(value, SuperPropertyManager):
        value.post_update()
  
  @classmethod
  def _pre_delete_hook(cls, key):
    if key:
      entity = key.get()
      entity.record_write()
      @toplevel
      def delete_async():
        for field_key, field in entity.get_fields().items():
          if is_structured_field(field):
            manager = getattr(entity, field_key, None)
            if isinstance(manager, SuperPropertyManager):
              manager.delete()
      delete_async()
  
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
    if isinstance(self, BaseExpando):
      return super(BaseExpando, self).__delattr__(name)
  
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
        value = copy.deepcopy(value)
        try:
          setattr(new_entity, field, value)
        except ComputedPropertyError as e:
          pass  # This is intentional
        except Exception as e:
          #util.logger('__deepcopy__ - could not copy %s.%s. Error: %s' % (self.__class__.__name__, field, e))
          pass
    return new_entity
  
  @classmethod
  def build_key(cls, *args, **kwargs):
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
  def search(cls, argument, namespace=None, limit=10, urlsafe_cursor=None):
    keys = None
    args = []
    kwds = {}
    filters = argument.get('filters')
    order_by = argument.get('order_by')
    for _filter in filters:
      if _filter['field'] == 'ancestor':
        kwds['ancestor'] = _filter['value']
        continue
      if _filter['field'] == 'key':
        keys = _filter['value']
        break
      field = getattr(cls, _filter['field'])
      op = _filter['operator']
      value = _filter['value']
      if op == '==': # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this also needs improvements
        args.append(field == value)
      elif op == '!=':
        args.append(field != value)
      elif op == '>':
        args.append(field > value)
      elif op == '<':
        args.append(field < value)
      elif op == '>=':
        args.append(field >= value)
      elif op == 'IN':
        args.append(field.IN(value))
      elif op == 'contains':
        letters = list(string.printable)
        try:
          last = letters[letters.index(value[-1].lower()) + 1]
          args.append(field >= value)
          args.append(field < last)
        except ValueError as e:  # Value not in the letter scope, šččđčžćč for example.
          args.append(field == value)
    query = cls.query(namespace=namespace, **kwds)
    query = query.filter(*args)
    if order_by:
      order_by_field = getattr(cls, order_by['field'])
      if order_by['operator'] == 'asc':
        query = query.order(order_by_field)
      else:
        query = query.order(-order_by_field)
    # Caller must be capable of differentiating possible results returned!
    if keys is not None:
      if not isinstance(keys, list):
        keys = [keys]
      return get_multi(keys)
    else:
      try:
        cursor = Cursor(urlsafe=urlsafe_cursor)
      except:
        cursor = Cursor()
      return query.fetch_page(limit, start_cursor=cursor)
  
  @classmethod
  def _rule_read(cls, permissions, entity, field_key, field):  # @todo Not sure if this should be class method, but it seamed natural that way!?
    '''If the field is invisible, ignore substructure permissions and remove field along with entire substructure.
    Otherwise go one level down and check again.

    '''
    if (not field_key in permissions) or (not permissions[field_key]['visible']):
      entity.remove_output(field_key)
    else:
      if is_structured_field(field):
        child_entity = getattr(entity, field_key)
        if isinstance(child_entity, SuperPropertyManager):
          child_entity = child_entity.value
        if field._repeated:
          if child_entity is not None:  # @todo We'll see how this behaves for def write as well, because None is sometimes here when they are expando properties.
            for child_entity_item in child_entity:
              child_fields = child_entity_item.get_fields()
              child_fields.update(dict([(p._code_name, p) for _, p in child_entity_item._properties.items()]))
              for child_field_key, child_field in child_fields.items():
                cls._rule_read(permissions[field_key], child_entity_item, child_field_key, child_field)
        else:
          child_entity = getattr(entity, field_key)
          if isinstance(child_entity, SuperPropertyManager):
            child_entity = child_entity.value
          if child_entity is not None:  # @todo We'll see how this behaves for def write as well, because None is sometimes here when they are expando properties.
            child_fields = child_entity.get_fields()
            child_fields.update(dict([(p._code_name, p) for _, p in child_entity._properties.items()]))
            for child_field_key, child_field in child_fields.items():
              cls._rule_read(permissions[field_key], child_entity, child_field_key, child_field)
  
  def rule_read(self):
    entity_fields = self.get_fields()
    for field_key, field in entity_fields.items():
      self._rule_read(self._field_permissions, self, field_key, field)
  
  @classmethod
  def _rule_write(cls, permissions, entity, field_key, field, field_value):  # @todo Not sure if this should be class method, but it seamed natural that way!?
    '''Old principle was: If the field is writable, ignore substructure permissions and override field fith new values.
    Otherwise go one level down and check again.
    
    '''
    if (field_key in permissions):  #  @todo How this affects the outcome??
      # For simple (non-structured) fields, if writting is denied, try to roll back to their original value!
      if not (is_structured_field(field)):
        if not permissions[field_key]['writable']:
          try:
            #if field_value is None:  # @todo This is bug. None value can not be supplied on fields that are not required!
            #  return
            setattr(entity, field_key, field_value)
          except TypeError as e:
            util.logger('write: setattr error: %s' % e)
          except ComputedPropertyError:
            pass
      else:
        child_entity = getattr(entity, field_key)
        if isinstance(child_entity, SuperPropertyManager):
          child_entity = child_entity.value
        if isinstance(field_value, SuperPropertyManager):
          field_value = field_value.value
        is_local_structure = isinstance(field, (SuperStructuredProperty, SuperLocalStructuredProperty))
        field_value_mapping = {}  # Here we hold references of every key from original state.
        if field._repeated:
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
        for child_field_key, child_field in field.get_model_fields().items():
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
    entity_fields = self.get_fields()
    for field_key, field in entity_fields.items():
      field_value = getattr(self._original, field_key)
      self._rule_write(self._field_permissions, self, field_key, field, field_value)
  
  @classmethod
  def _rule_reset_actions(cls, action_permissions, actions):
    for action_key in actions:
      action_permissions[action_key] = {'executable': []}
  
  @classmethod
  def _rule_reset_fields(cls, field_permissions, fields):
    for field_key, field in fields.items():
      if field_key not in field_permissions:
        field_permissions[field_key] = collections.OrderedDict([('writable', []), ('visible', [])])
      if is_structured_field(field):
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
    for key, value in permissions.items():
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
    for key, value in local_permissions.items():
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
    for key, value in global_permissions.items():
      if isinstance(value, dict):
        cls._rule_complement_local_permissions(global_permissions[key], local_permissions[key])  # local_permissions[key] will fail in case global and local permissions are (for some reason) out of sync!
      else:
        if key not in local_permissions:
          local_permissions[key] = value
  
  @classmethod
  def _rule_compile_global_permissions(cls, global_permissions):
    for key, value in global_permissions.items():
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
  
  @toplevel  # @todo Not sure if this is ok?
  def record_write(self):
    if not isinstance(self, Record) and self._use_record_engine and hasattr(self, 'key') and self.key_id:
      if self._record_arguments and self._record_arguments.get('agent') and self._record_arguments.get('action'):
        log_entity = self._record_arguments.pop('log_entity', True)
        record = Record(parent=self.key, **self._record_arguments)
        if log_entity is True:
          record.log_entity(self)
        return record.put_async()  # @todo How do we implement put_multi in this situation!?
  
  def read(self, input=None):
    '''This method loads all sub-entities based on input details.
    
    '''
    for field_key, field in self.get_fields().items():
      if is_structured_field(field):
        value = getattr(self, field_key)
        kwargs = {}
        if input is not None:
          entities = input.get(field_key)
          if entities:
            kwargs['entities'] = entities
          else:  # Entities is not provided, use read_options from the input if any to determine cursor
            read_options = input.get('read_options')
            if read_options:
              read_options = read_options.get(field_key)
              if read_options:
                kwargs = read_options
        # otherwise we will just retrieve entities without any configurations
        value.read_async(**kwargs)
    self.make_original() # finalize original before touching anything
  
  def make_original(self):
    '''This function will make a copy of the current state of the entity
    and put it into _original field.
    
    '''
    if self._use_rule_engine:
      self._original = None
      original = copy.deepcopy(self)
      self._original = original
  
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
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    if self._use_rule_engine and hasattr(self, '_field_permissions'):
      self.rule_read()  # Apply rule read before output.
    dic = {}
    dic['kind'] = self.get_kind()
    dic['_state'] = self._state
    if self.key:
      dic['key'] = self.key.urlsafe()
      dic['id'] = self.key.id()
    names = self._output
    for name in names:
      value = getattr(self, name, None)
      dic[name] = value
    for k, v in dic.items():
      if isinstance(v, Key):
        dic[k] = v.urlsafe()
    return dic


class BaseModel(_BaseModel, Model):
  '''Base class for all 'ndb.Model' entities.'''


class BasePoly(_BaseModel, polymodel.PolyModel):
  
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
  def get_expando_fields(cls):
    if hasattr(cls, '_expando_fields'):
      for prop_key, prop in cls._expando_fields.items():
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
        for expando_prop_key, expando_prop in expando_fields.items():
          if expando_prop._name == next:
            prop = expando_prop
            self._properties[expando_prop._name] = expando_prop
            break
    if prop is None:
      prop = self._fake_property(p, next, indexed)
    return prop


class BasePolyExpando(BasePoly, BaseExpando):
  pass


#####################################################################
########## Reusable superior property formating functions. ##########
#####################################################################


def _property_value_validate(prop, value):
  if prop._max_size:
    if len(value) > prop._max_size:
      raise PropertyError('max_size_exceeded')
  if value is None and prop._required:
    raise PropertyError('required')
  if hasattr(prop, '_choices') and prop._choices:
    if value not in prop._choices:
      raise PropertyError('not_in_specified_choices')


def _property_value_filter(prop, value):
  if prop._value_filters:
    if isinstance(prop._value_filters, (list, tuple)):
      for value_filter in prop._value_filters:
        value = value_filter(prop, value)
    else:
      value = prop._value_filters(prop, value)
  return value


def _property_value_format(prop, value):
  if value is None:
    if prop._default is not None:
      value = prop._default
  if prop._repeated:
    out = []
    if not isinstance(value, (list, tuple)):
      value = [value]
    for v in value:
      _property_value_validate(prop, v)
      out.append(v)
    return _property_value_filter(prop, out)
  else:
    _property_value_validate(prop, value)
    return _property_value_filter(prop, value)


def _structured_property_field_format(fields, values):
  _state = values.get('_state')
  if values.get('key'):
    values['key'] = Key(urlsafe=values.get('key'))
  for value_key, value in values.items():
    field = fields.get(value_key)
    if field:
      if hasattr(field, 'format'):
        values[value_key] = field.format(value)
    else:
      del values[value_key]
  values['_state'] = _state  # Always keep track of _state for rule engine!


def _structured_property_format(prop, value):
  value = _property_value_format(prop, value)
  out = []
  if not prop._repeated:
    value = [value]
  fields = prop.get_model_fields()
  for v in value:
    _structured_property_field_format(fields, v)
    entity = prop._modelclass(**v)
    out.append(entity)
  if not prop._repeated:
    try:
      out = out[0]
    except IndexError as e:
      out = None
  return out


#################################################
########## Superior Property Managers. ##########
#################################################


class SuperPropertyManager(object):
  
  def __init__(self, property_instance, storage_entity, **kwds):
    self._property = property_instance
    self._entity = storage_entity  # storage entity of the property
    self._kwds = kwds
  
  def __repr__(self):
    return '%s(entity=%s, property=%s, property_value=%s, kwds=%s)' % (self.__class__.__name__,
                                                                       self._entity, self._property,
                                                                       getattr(self, '_property_value', None), self._kwds)
  
  @property
  def value(self):
    return getattr(self, '_property_value', None)
  
  @property
  def property_name(self):
    # Retrieves proper name of the field for setattr usage.
    name = self._property._code_name
    if not name:
      name = self._property._name
    return name
  
  def has_value(self):
    return hasattr(self, '_property_value')
  
  def has_future(self):
    value = self._property_value
    if isinstance(value, list):
      if len(value):
        value = value[0]
    return isinstance(value, Future)
  
  def get_output(self):
    return getattr(self, '_property_value', None)


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
    if isinstance(self._property._modelclass, basestring):  # In case the model class is a kind str
      self._property._modelclass = Model._kind_map.get(self._property._modelclass)
    self._property_value_options = {}
    # @todo We might want to change this to something else, but right now it is the most elegant.
  
  @property
  def value_options(self):
    ''' '_property_value_options' is used for storing and returning information that
    is related to property value(s). For exmaple: 'more' or 'cursor' parameter in querying.
    
    '''
    return self._property_value_options
  
  @property
  def storage_type(self):
    ''' Possible values of _storage variable can be: 'local', 'remote_single', 'remote_multi', 'remote_multi_sequenced' values stored.
    'local' is a structured value stored in a parent entity.
    'remote_single' is a single child (fan-out) entity of the parent entity.
    'remote_multi' is set of children entities of the parent entity, they are usualy accessed by ancestor query.
    'remote_multi_sequenced' is exactly as the above, however, their id-s represent sequenced numberes, and they are usually accessed via get_multi.
    
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
        if not isinstance(property_value_item, self._property._modelclass):
          raise PropertyError('Expected %r, got %r' % (self._property._modelclass, self._property_value))
    self._property_value = property_value
  
  def _copy_record_arguments(self, entity):
    if hasattr(self._entity, '_record_arguments'):
      if hasattr(entity, '_record_arguments'):
        record_arguments = entity._record_arguments
      else:
        record_arguments = {}
      entity_record_arguments = self._entity._record_arguments
      record_arguments['action'] = entity_record_arguments.get('aciton')
      record_arguments['agent'] = entity_record_arguments.get('agent')
      entity._record_arguments = record_arguments
  
  def _mark_for_delete(self, property_value, property_instance=None):
    '''Mark each of property values for deletion by setting the '_state'' to 'deleted'!
    
    '''
    if not property_instance:
      property_instance = self._property
    if not property_instance._repeated:
      property_value = [property_value]
    for value in property_value:
      value._state = 'deleted'
  
  def _delete_local(self):
    self._mark_for_delete(self._property_value)
  
  def _delete_remote(self):
    cursor = Cursor()
    limit = 200
    query = self._property._modelclass.query(ancestor=self._entity.key)
    while True:
      _entities, cursor, more = query.fetch_page(limit, start_cursor=cursor)
      if len(_entities):
        for entity in _entities:
          self._copy_record_arguments(entity)
        delete_multi([entity.key for entity in _entities])
        if not cursor or not more:
          break
      else:
        break
  
  def _delete_remote_single(self):
    property_value_key = Key(self._property._modelclass.get_kind(), self._entity.key_id_str, parent=self._entity.key)
    entity = property_value_key.get()
    self._copy_record_arguments(entity)
    entity.key.delete()
  
  def _delete_remote_multi(self):
    self._delete_remote()
  
  def _delete_remote_multi_sequenced(self):
    self._delete_remote()
  
  def delete(self):
    '''Calls storage type specific delete function, in order to mark property values for deletion.
    
    '''
    if self._property._deletable:
      delete_function = getattr(self, '_delete_%s' % self.storage_type)
      delete_function()
  
  def _read_local(self, **kwds):
    '''Every structured/local structured value requires a sequence id for future identification purposes!
    
    '''
    property_value = self._property._get_user_value(self._entity)
    property_value_copy = property_value
    if property_value_copy is not None:
      if not self._property._repeated:
        property_value_copy = [property_value_copy]
      for i, value in enumerate(property_value_copy):
        value.set_key(str(i))
    else:
      if self._property._repeated:
        property_value = []
    self._property_value = property_value
  
  def _read_remote_single(self, **kwds):
    '''Remote single storage always follows the same pattern,
    it composes its own key by using its kind, ancestor string id, and ancestor key as parent!
    
    '''
    property_value_key = Key(self._property._modelclass.get_kind(), self._entity.key_id_str, parent=self._entity.key)
    property_value = property_value_key.get()  # @todo How do we use async call here, when we need to investigate the value below?
    if not property_value:
      property_value = self._property._modelclass(key=property_value_key)
    self._property_value = property_value
  
  def _read_remote_multi(self, **kwds):
    urlsafe_cursor = kwds.get('cursor')
    limit = kwds.get('limit', 10)
    order = kwds.get('order')
    supplied_entities = kwds.get('entities')
    if supplied_entities:
      entities = get_multi([entity.key for entity in supplied_entities if entity.key is not None])
      entities = [entity for entity in entities if entity is not None]
      cursor = None
    else:
      query = self._property._modelclass.query(ancestor=self._entity.key)
      if order:
        order_field = getattr(self._property._modelclass, order['field'])
        if order['direction'] == 'asc':
          query = query.order(order_field)
        else:
          query = query.order(-order_field)
      try:
        cursor = Cursor(urlsafe=urlsafe_cursor)
      except:
        cursor = Cursor()
      entities = query.fetch_page_async(limit, start_cursor=cursor)
      cursor = None
    self._property_value = entities
    self._property_value_options['cursor'] = cursor
  
  def _read_remote_multi_sequenced(self, **kwds):
    '''Remote multi sequenced storage uses sequencing technique in order to build child entity keys.
    It then uses those keys for retreving, storing and deleting entities of those keys.
    This technique has lowest impact on data storage and retreval, and should be used whenever possible!
    
    '''
    cursor = kwds.get('cursor', 0)
    limit = kwds.get('limit', 10)
    entities = []
    supplied_entities = kwds.get('entities')
    if supplied_entities:
      entities = get_multi([entity.key for entity in supplied_entities if entity.key is not None])
      entities = [entity for entity in entities if entity is not None]
      cursor = None
    else:
      keys = [Key(self._property._modelclass.get_kind(),
                  str(i), parent=self._entity.key) for i in xrange(cursor, cursor + limit)]
      entities = get_multi_async(keys)
      cursor = cursor + limit
    self._property_value = entities
    self._property_value_options['cursor'] = cursor
  
  def read_async(self, **kwds):
    '''Calls storage type specific read function, in order populate _property_value with values.
    'force_read' keyword will always call storage type specific read function.
    However we are not sure if we are gonna need to force read operation.
    
    '''
    if self._property._readable:
      if (not self.has_value()) or kwds.get('force_read'):
        # read_local must be called multiple times because it gets loaded between from_pb and post_get.
        read_function = getattr(self, '_read_%s' % self.storage_type)
        read_function(**kwds)
      return self._property_value
  
  def read(self, **kwds):
    if self._property._readable:
      self.read_async(**kwds)
      if self.has_future():
        property_value = []
        if isinstance(self._property_value, list):
          if len(self._property_value):
            for value in self._property_value:
              if isinstance(value, Future):
                entity = value.get_result()
                if entity is not None:
                  property_value.append(entity)
            self._property_value = property_value
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
      return self._property_value
  
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
        setattr(self._entity, self.property_name, None)  # Comply with expando and virtual fields.
  
  def _pre_update_remote_single(self):
    pass
  
  def _pre_update_remote_multi(self):
    pass
  
  def _pre_update_remote_multi_sequenced(self):
    pass
  
  def _post_update_local(self):
    pass
  
  def _post_update_remote_single(self):
    '''Ensure that every entity has the entity ancestor by enforcing it.
    
    '''
    if not hasattr(self._property_value, 'prepare_key'):
      if self._property_value.key_parent != self._entity.key:
        key_id = self._property_value.key_id
        self._property_value.set_key(key_id, parent=self._entity.key)
    else:
      self._property_value.prepare_key(parent=self._entity.key)
    # We do put eitherway
    # @todo If state is deleted, shall we delete the single storage entity?
    self._copy_record_arguments(self._property_value)
    if self._property_value._state == 'deleted':
      self._property_value.key.delete()
    else:
      self._property_value.put()
  
  def _post_update_remote_multi(self):
    '''Ensure that every entity has the entity ancestor by enforcing it.
    
    '''
    delete_entities = []
    for entity in self._property_value:
      self._copy_record_arguments(entity)
      if not hasattr(entity, 'prepare_key'):
        if entity.key_parent != self._entity.key:
          key_id = entity.key_id
          entity.set_key(key_id, parent=self._entity.key)
      else:
        entity.prepare_key(parent=self._entity.key)
      if entity._state == 'deleted':
        delete_entities.append(entity)
    for delete_entity in delete_entities:
      self._property_value.remove(delete_entity)
    delete_multi([entity.key for entity in delete_entities])
    put_multi(self._property_value)
  
  def _post_update_remote_multi_sequenced(self):
    '''Ensure that every entity has the entity ancestor by enforcing it.
    
    '''
    delete_entities = []
    last_sequence = self._property._modelclass.query(ancestor=self._entity.key).count()
    for i, entity in enumerate(self._property_value):
      self._copy_record_arguments(entity)
      if entity._state == 'deleted':
        delete_entities.append(entity)
        continue
      if entity.key_id is None:
        if not hasattr(entity, 'prepare_key'):
          entity.set_key(str(last_sequence), parent=self._entity.key)
        else:
          entity.prepare_key(parent=self._entity.key, id=str(last_sequence))
        last_sequence += 1
      else:
        entity.set_key(str(i), parent=self._entity.key)
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


class SuperReadPropertyManager(SuperPropertyManager):
  
  def _read(self):
    if self._property._callback:
      self._property_value = self._property._callback(self._entity)
    elif self._property._target_field:
      field = getattr(self._entity, self._property._target_field)
      if not isinstance(field, Key):
        raise PropertyError('Target field must be instance of Key. Got %s' % field)
      if self._property._kind != None and field.kind() != self._property._kind:
        raise PropertyError('Kind must be %s, got %s' % (self._property._kind, field.kind()))
      self._property_value = field.get_async()
    return self._property_value
  
  def read_async(self):
    if self._property._readable:
      if not self.has_value():
        self._read()
      return self._property_value
  
  def read(self):
    if self._property._readable:
      self.read_async()
      if self.has_future():
        self._property_value = self._property_value.get_result()
        if self._property._format_callback:
          self._property_value = self._property._format_callback(self._entity, self._property_value)
      return self._property_value
  
  def set(self, value):
    if isinstance(value, Key):
      self._property_value = value.get_async()
    elif isinstance(value, BaseModel):
      self._property_value = value
  
  def delete(self):
    self._property_value = None
    
  def pre_update(self):
    pass
  
  def post_update(self):
    pass


#########################################################
########## Superior properties implementation! ##########
#########################################################


class _BaseProperty(object):
  '''Base property class for all superior properties.'''
  
  _max_size = None
  _value_filters = None
  
  def __init__(self, *args, **kwargs):
    self._max_size = kwargs.pop('max_size', self._max_size)
    self._value_filters = kwargs.pop('value_filters', self._value_filters)
    custom_kind = kwargs.get('kind')
    if custom_kind and isinstance(custom_kind, basestring) and '.' in custom_kind:
      kwargs['kind'] = factory(custom_kind)
    super(_BaseProperty, self).__init__(*args, **kwargs)
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    choices = self._choices
    if choices:
      choices = list(self._choices)
    dic = {'verbose_name': getattr(self, '_verbose_name'),
           'required': self._required,
           'max_size': self._max_size,
           'choices': choices,
           'default': self._default,
           'repeated': self._repeated,
           'type': self.__class__.__name__}
    return dic


class BaseProperty(_BaseProperty, Property):
  '''Base property class for all properties capable of having _max_size option.'''


class SuperComputedProperty(_BaseProperty, ComputedProperty):
  pass


class _BaseStructuredProperty(object):
  '''Base class for structured property.
  
  '''
  _readable = True
  _updateable = True
  _deleteable = True
  _managerclass = None
  
  def __init__(self, *args, **kwargs):
    args = list(args)
    self._readable = kwargs.pop('readable', True)
    self._updateable = kwargs.pop('updateable', True)
    self._deleteable = kwargs.pop('deleteable', True)
    self._managerclass = kwargs.pop('managerclass', None)
    if isinstance(args[0], basestring):
      args[0] = Model._kind_map.get(args[0])
    super(_BaseStructuredProperty, self).__init__(*args, **kwargs)
    self._storage = 'local'
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    dic = super(_BaseStructuredProperty, self).get_meta()
    dic['model'] = self._modelclass.get_fields()
    return dic
  
  def get_model_fields(self):
    return self._modelclass.get_fields()
  
  def format(self, value):
    return _structured_property_format(self, value)
  
  def _set_value(self, entity, value):
    # __set__
    manager = self._get_value(entity)
    manager.set(value)
    return super(_BaseStructuredProperty, self)._set_value(entity, value)
  
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
      util.logger('%s._get_value.%s %s' % (self.__class__.__name__, manager_name, entity))
      manager_class = SuperStructuredPropertyManager
      if self._managerclass:
        manager_class = self._managerclass
      manager = manager_class(property_instance=self, storage_entity=entity)
      entity._values[manager_name] = manager
    super(_BaseStructuredProperty, self)._get_value(entity)
    return manager


class SuperLocalStructuredProperty(_BaseStructuredProperty, _BaseProperty, LocalStructuredProperty):
  pass


class SuperStructuredProperty(_BaseStructuredProperty, _BaseProperty, StructuredProperty):
  pass


class SuperPickleProperty(_BaseProperty, PickleProperty):
  pass


class SuperDateTimeProperty(_BaseProperty, DateTimeProperty):
  
  def format(self, value):
    value = _property_value_format(self, value)
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


class SuperJsonProperty(_BaseProperty, JsonProperty):
  
  def format(self, value):
    value = _property_value_format(self, value)
    if isinstance(value, basestring):
      return json.loads(value)
    else:
      return value


class SuperTextProperty(_BaseProperty, TextProperty):
  
  def format(self, value):
    value = _property_value_format(self, value)
    if self._repeated:
      return [unicode(v) for v in value]
    else:
      return unicode(value)


class SuperStringProperty(_BaseProperty, StringProperty):
  
  def format(self, value):
    value = _property_value_format(self, value)
    if self._repeated:
      return [unicode(v) for v in value]
    else:
      return unicode(value)


class SuperFloatProperty(_BaseProperty, FloatProperty):
  
  def format(self, value):
    value = _property_value_format(self, value)
    if self._repeated:
      return [float(v) for v in value]
    else:
      return float(value)


class SuperIntegerProperty(_BaseProperty, IntegerProperty):
  
  def format(self, value):
    value = _property_value_format(self, value)
    if self._repeated:
      return [long(v) for v in value]
    else:
      if not self._required and value is None:
        return value
      return long(value)


class SuperKeyProperty(_BaseProperty, KeyProperty):
  '''This property is used on models to reference ndb.Key property.
  Its format function will convert urlsafe string into a ndb.Key and check if the key
  exists in the datastore. If the key does not exist, it will throw an error.
  If key existence feature isn't required, SuperVirtualKeyProperty() can be used in exchange.
  
  '''
  def format(self, value):
    value = _property_value_format(self, value)
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
    entities = get_multi(out, use_cache=True)
    for i, entity in enumerate(entities):
      if entity is None:
        raise PropertyError('not_found_%s' % out[i].urlsafe())
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out


class SuperVirtualKeyProperty(SuperKeyProperty):
  '''This property is exact as SuperKeyProperty, except its format function is not making any calls
  to the datastore to check the existence of the provided urlsafe key. It will simply format the
  provided urlsafe key into a ndb.Key.
  
  '''
  def format(self, value):
    value = _property_value_format(self, value)
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
  
  def format(self, value):
    try:
      # First it attempts to construct the key from urlsafe
      return super(SuperKeyProperty, self).format(value)
    except:
      # Failed to build from urlsafe, proceed with KeyFromPath.
      value = _property_value_format(self, value)
      out = []
      assert isinstance(value, list) == True
      if self._repeated:
        for v in value:
          for key_path in v:
            key = Key(*key_path)
            if self._kind and key.kind() != self._kind:
              raise PropertyError('invalid_kind')
            out.append(key)
          entities = get_multi(out, use_cache=True)  # @todo Added use_cache, not sure if that's ok?
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
  
  def format(self, value):
    value = _property_value_format(self, value)
    if self._repeated:
      return [bool(long(v)) for v in value]
    else:
      return bool(long(value))


class SuperBlobKeyProperty(_BaseProperty, BlobKeyProperty):
  
  def format(self, value):
    value = _property_value_format(self, value)
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


class SuperDecimalProperty(SuperStringProperty):
  '''Decimal property that accepts only decimal.Decimal.'''
  
  def format(self, value):
    value = _property_value_format(self, value)
    if self._repeated:
      value = [decimal.Decimal(v) for v in value]
    else:
      value = decimal.Decimal(value)
    if value is None:
      raise PropertyError('invalid_number')
    return value
  
  def _validate(self, value):
    if not isinstance(value, (decimal.Decimal)):
      raise PropertyError('expected_decimal')  # Perhaps, here should be some other type of exception?
  
  def _to_base_type(self, value):
    return str(value)
  
  def _from_base_type(self, value):
    return decimal.Decimal(value)


class SuperSearchProperty(SuperJsonProperty):
  
  def __init__(self, *args, **kwargs):
    '''Filters work like this:
    First you configure SuperSearchProperty with filters, indexes and order_by parameters.
    This configuration takes place at the property definition place.
    filters = {'field': {'operators': ['==', '>', '<', '>=', '<=', 'contains'],  With 'operators'' you define possible filter operators.
                         'type': SuperStringProperty(required=True)}} With 'type'' you define a filter value property.
    
    indexes = [{'filter': ['field1', 'field2', 'field3'], 'order_by': [['field1', ['asc', 'desc']]]},
               {'filter': ['field1', 'field2'], 'order_by': [['field1', ['asc', 'desc']]]}]
    
    order_by = {'field': {'operators': ['asc', 'desc']}}
    
    search = SuperSearchProperty(filters=filters, indexes=indexes, order_by=order_by)
    
    Search values that are provided with input will be validated trough SuperSearchProperty().format() function.
    Example of search values that are provided in input after processing:
    context.output['search'] = {'filters': [{'field': 'name', 'operator': '==', 'value': 'Test'}],
                                'order_by': {'field': 'name', 'operator': 'asc'}}
    
    '''
    filters = kwargs.pop('filters', {})
    order_by = kwargs.pop('order_by', {})
    indexes = kwargs.pop('indexes', {})
    self._filters = filters
    self._order_by = order_by
    self._indexes = indexes
    super(SuperSearchProperty, self).__init__(*args, **kwargs)
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    dic = super(SuperSearchProperty, self).get_meta()
    dic['filters'] = self._filters
    dic['order_by'] = self._order_by
    dic['indexes'] = self._indexes
    return dic
  
  def format(self, value):
    value = super(SuperSearchProperty, self).format(value)
    search = {'filters': value.get('filters'),
              'order_by': value.get('order_by'),
              'property': self}
    for_composite_filter = []
    for config in search['filters']:
      key = config.get('field')
      _filter = self._filters.get(key)
      if not _filter:
        raise PropertyError('field_not_in_filter_list')
      assert config.get('operator') in _filter['operators']
      new_value = _filter['type'].format(config.get('value'))  # Format the value based on the property type.
      config['value'] = new_value
      for_composite_filter.append(key)
    for_composite_order_by = []
    config = search['order_by']
    if config:
      key = config.get('field')
      _order_by = self._order_by.get(key)
      if not _order_by:
        raise PropertyError('field_not_in_order_by_list')
      assert config.get('operator') in _order_by['operators']
      for_composite_order_by.append(key)
      for_composite_order_by.append(config.get('operator'))
    composite_filter = False
    composite_order_by = False
    for index in self._indexes:
      if index.get('filter') == for_composite_filter:
        composite_filter = True
      order_by = index.get('order_by')
      if order_by:
        for order_by_config in order_by:
          try:
            if order_by_config[0] == for_composite_order_by[0] and for_composite_order_by[1] in order_by_config[1]:
              composite_order_by = True
          except IndexError as e:
            pass
      elif not config:
        composite_order_by = True
    assert composite_filter is True and composite_order_by is True
    return search


class SuperEntityStorageStructuredProperty(Property):
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
  
  def __init__(self, modelclass, name=None, compressed=False, keep_keys=True, **kwds):
    self._storage = kwds.pop('storage')
    self._modelclass = modelclass
    self._readable = kwds.pop('readable', True)
    self._updateable = kwds.pop('updateable', True)
    self._deleteable = kwds.pop('deleteable', True)
    self._managerclass = kwds.pop('managerclass', None)
    if self._storage in ['remote_multi', 'remote_multi_sequenced']:
      self._repeated = True  # Always enforce repeated on multi entity storage engine!
    super(SuperEntityStorageStructuredProperty, self).__init__(name, **kwds)
  
  def get_model_fields(self):
    if isinstance(self._modelclass, basestring):
      self._modelclass = Model._kind_map.get(self._modelclass)
    return self._modelclass.get_fields()
  
  def format(self, value):
    return _structured_property_format(self, value)
  
  def _set_value(self, entity, value):
    # __set__
    manager = self._get_user_value(entity)
    manager.set(value)
  
  def _get_value(self, entity):
    # __get__
    manager_name = '%s_manager' % self._name
    if manager_name in entity._values:
      return entity._values[manager_name]
    util.logger('SuperEntityStorageStructuredProperty._get_value.%s %s' % (manager_name, entity))
    manager_class = SuperStructuredPropertyManager
    if self._managerclass:
      manager_class = self._managerclass
    manager = manager_class(property_instance=self, storage_entity=entity)
    entity._values[manager_name] = manager
    return manager
  
  def _prepare_for_put(self, entity):
    self._get_value(entity)  # For its side effects.


class SuperReadProperty(SuperKeyProperty):
  '''This property can be used to read stuff in async mode upon reading entity from protobuff.
  However, this can be also used for storing keys, behaving like SuperKeyProperty.
  Setter value should always be a key, however it can be an entire entity instance from which it will use its .key.
  >>> entity.user = user_key
  Getter usually retrieves entire entity instance,
  or something else can be returned based on the _format_callback option.
  >>> entity.user.email
  Beware with usage of this property. It will automatically get the entity in async mode as soon as the
  from_pb and _post_get callback are executed.
  This functionality can be suppressed by implementing additional kwarg called 'autoload', and based on that
  the read_async call could be skipped in _BaseModel at make_async_calls().
  
  '''
  _readable = True
  _updateable = True
  _deletable = True
  
  def __init__(self, *args, **kwargs):
    self._callback = kwargs.pop('callback', None)
    self._format_callback = kwargs.pop('format_callback', None)
    self._kind = kwargs.pop('kind', None)
    self._target_field = kwargs.pop('target_field', None)
    self._readable = kwargs.pop('readable', True)
    self._updateable = kwargs.pop('updateable', True)
    self._deleteable = kwargs.pop('deleteable', True)
    if not self._target_field and not self._callback:
      raise PropertyError('You must provide either: "callback"" or "target_field"')
    if self._callback != None and not callable(self._callback):
      raise PropertyError('"callback" must be a callable, got %s' % self._callback)
    if self._format_callback != None and not callable(self._format_callback):
      raise PropertyError('"format_callback" must be either None or callable, got %s' % self._format_callback)
    super(SuperReadProperty, self).__init__(*args, **kwargs)
  
  def _set_value(self, entity, value):
    # __set__
    manager = self._get_value(entity, internal=True)
    manager.set(value)
    if not isinstance(value, Key) and hasattr(value, 'key'):
      value = value.key
    return super(SuperReadProperty, self)._set_value(entity, value)
  
  def _delete_value(self, entity):
    # __delete__
    manager = self._get_value(entity, internal=True)
    manager.delete()
    return super(SuperReadProperty, self)._delete_value(entity)
  
  def _get_value(self, entity, internal=None):
    # __get__
    manager_name = '%s_manager' % self._name
    if manager_name in entity._values:
      manager = entity._values[manager_name]
    else:
      util.logger('SuperReadProperty._get_value.%s %s' % (manager_name, entity))
      manager = SuperReadPropertyManager(property_instance=self, storage_entity=entity)
      entity._values[manager_name] = manager
    if internal:  # If internal is true, always retrieve manager.
      return manager
    if not manager.has_value():
      return manager
    else:
      return manager.read()


class SuperRecordProperty(SuperEntityStorageStructuredProperty):
  '''Usage: '_records': SuperRecordProperty(Domain or '6')
  
  '''
  def __init__(self, *args, **kwargs):
    args = list(args)
    self._modelclass2 = args[0]
    args[0] = Record
    kwargs['storage'] = 'remote_multi'
    super(SuperRecordProperty, self).__init__(*args, **kwargs)
    self._updateable = False
    self._deleteable = False
  
  def get_model_fields(self):
    parent = super(SuperRecordProperty, self).get_model_fields()
    if isinstance(self._modelclass2, basestring):
      self._modelclass2 = Model._kind_map.get(self._modelclass2)
    parent.update(self._modelclass2.get_fields())
    return parent


#########################################
########## Core system models! ##########
#########################################


class Action(BaseExpando):
  
  _kind = 56
  
  name = SuperStringProperty('1', required=True)
  arguments = SuperPickleProperty('2', required=True, default={}, compressed=False)
  active = SuperBooleanProperty('3', required=True, default=True)
  
  _default_indexed = False
  
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
    '_agent': SuperReadProperty(callback=lambda self: self._retreive_agent(),
                                format_callback=lambda self: self._retrieve_agent_name()),
    '_action': SuperReadProperty(callback=lambda self: self._retrieve_action())
    }
  
  def _retrieve_agent_name(self):
    # We have to involve Domain User here, although ndb should be unavare of external models!
    if self.key.kind() == '8':
      return self.name
    else:
      return self._primary_email
  
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
          break
  
  def _if_properties_are_cloned(self):
    return not (self.__class__._properties is self._properties)
  
  def _retrieve_cloned_name(self, name):
    for _, prop in self._properties.items():
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
      properties = dict([(pr._name, pr) for _, pr in modelclass.get_fields().items()])
      # Adds properties from parent class to the log entity making it possible to deserialize them properly.
      prop = properties.get(next)
      if prop:
        self._clone_properties()  # Clone properties, because if we don't, the Record._properties will be overriden!
        self._properties[next] = prop
        self.add_output(prop._code_name)  # Besides rule engine, this must be here as well.
    return super(Record, self)._get_property_for(p, indexed, depth)
  
  def log_entity(self, entity):
    self._clone_properties()  # Clone properties, because if we don't, the Record._properties will be overriden.
    for _, prop in entity._properties.items():  # We do not call get_fields here because all fields that have been written are in _properties.
      value = prop._get_value(entity)
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
  actions = SuperKeyProperty('2', kind='56', repeated=True, indexed=False)
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
        if (action.urlsafe() in entity.get_actions()) and (safe_eval(self.condition, kwargs)) and (self.executable != None):
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
        parsed_field = entity.get_field('_field_permissions.' + field)
        if parsed_field and (safe_eval(self.condition, kwargs)):
          if (self.writable != None):
            parsed_field['writable'].append(self.writable)
          if (self.visible != None):
            parsed_field['visible'].append(self.visible)
