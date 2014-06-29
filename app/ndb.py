# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import decimal
import cgi
import datetime
import importlib
import json
import copy

from google.appengine.ext.ndb import *
from google.appengine.ext.ndb import polymodel
from google.appengine.ext import blobstore
from google.appengine.api import images

import cloudstorage

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



def search(query, fetch_all=False, limit=10, cursor=None):
  try:
    cursor = Cursor(urlsafe=cursor)
  except:
    pass
  if fetch_all or isinstance(cursor, (int, long)):
    if fetch_all:
      cursor = 0
      limit = 1000
    entities = []
    more = True
    while True:
      _entities = query.fetch(limit=limit, offset=cursor)
      if len(_entities):
        entities.extend(_entities)
        cursor = cursor + limit
        if not fetch_all:
          break
      else:
        more = False
        break
  elif isinstance(cursor, Cursor):
    entities, cursor, more = query.fetch_page(limit, start_cursor=cursor)
    if cursor:
      cursor = cursor.urlsafe()
  return {'entities': entities, 'cursor': cursor, 'more': more}


def search_ancestor_sequence(model, parent_key, limit=10, start_cursor=None, read_from_start=False):
  if not start_cursor:
    start_cursor = 0
  end_cursor = start_cursor + limit + 1
  if read_from_start:
    start_cursor = 0
  keys = [Key(model.get_kind(), str(i), parent=parent_key) for i in xrange(start_cursor, end_cursor)]
  more = True
  entities = get_multi(keys)
  if entities[-1] == None:  # @todo What happens if the latest fetched entity is none however, there are more entities beyond it?
    more = False
  results = []
  for entity in entities:
    if entity != None:
      results.append(entity)
  if more:
    del results[-1]  # @todo Or results.pop(len(results) - 1)
  return {'entities': results, 'more': more, 'cursor': start_cursor + limit}


#####################################
########## Helper classes. ##########
#####################################


class SuperPropertyManager(object):
  
  def __init__(self, property_instance, storage_entity, **kwds):
    self._property = property_instance
    self._entity = storage_entity  # storage entity of the property
    self._kwds = kwds
  
  def __repr__(self):
    return '%s(entity=%s, property=%s, property_value=%s, kwds=%s)' % (self.__class__.__name__,
                                                                       self._entity, self._property,
                                                                       getattr(self, '_property_value', None), self._kwds)
  
  def has_value(self):
    return hasattr(self, '_property_value')
  
  def has_future(self):
    return isinstance(self._property_value, Future)
  
  def get_output(self):
    return getattr(self, '_property_value', None)


class SuperStructuredPropertyManager(SuperPropertyManager):
  '''StorageEntityManager is the proxy class for all properties that want to implement read, update, delete, concept.
  Example:
  entity = entity_key.get()
  entity._images = [image, image, image] # override data
  entity._images.read().append(image) # or mutate
  # note that .read() must be used because getter retrieves StorageEntityManager
  !! Note: You can only retrieve StorageEntityManager instance by accessing the property like so:
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
  - all properties who have StorageEntityEditor capability will perform .update() function.
  
  '''
  
  def __init__(self, property_instance, storage_entity, **kwds):
    super(StorageEntityManager, self).__init__(property_instance, storage_entity, **kwds)
    if isinstance(self._property._modelclass, basestring):  # In case the model class is a kind str
      self._property._modelclass = Model._kind_map(self._property._modelclass)
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
    return self._property._storage  # @todo Prehaps _storage renamte to _storage_type
  
  def set(self, property_value):
    '''We always verify that the property_value is instance
    of the model that is specified in the property configuration.
    
    '''
    property_value_copy = property_value
    if isinstance(property_value_copy, list):
      if len(property_value_copy):
        property_value_copy = property_value_copy[0]
      else:
        property_value_copy = False
    if property_value_copy != False:
      assert isinstance(property_value_copy, self._property._modelclass)
    self._property_value = property_value
  
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
    property_name = self._property._code_name
    if not property_name:
      property_name = self._property._name
    property_value = getattr(self._entity, property_name)
    self._mark_for_delete(property_value, getattr(self._entity.__class__, property_name))
  
  def _delete_remote_single(self):
    self._delete_remote()
  
  def _delete_remote_multi(self):
    self._delete_remote()
  
  def _delete_remote_multi_sequenced(self):
    self._delete_remote()
  
  def delete(self):
    '''Calls storage type specific delete function, in order to mark property values for deletion.
    
    '''
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
    property_value = property_value_key.get()
    if not property_value:
      property_value = self._property._modelclass(key=property_value_key)
    self._property_value = property_value
  
  def _read_remote_multi(self, **kwds):
    fetch_all = kwds.get('fetch_all', False)
    limit = kwds.get('limit')
    urlsafe_cursor = kwds.get('cursor')
    order = kwds.get('order')
    query = self._property._modelclass.query(ancestor=self._entity.key)
    if order:
      order_field = getattr(self._property._modelclass, order['field'])
      if order['direction'] == 'asc':
        query = query.order(order_field)
      else:
        query = query.order(-order_field)
    results = search(query, fetch_all, limit, urlsafe_cursor)
    self._property_value = results['entities']
    self._property_value_options['cursor'] = results['cursor']
    self._property_value_options['more'] = results['more']
  
  def _read_remote_multi_sequenced(self, **kwds):
    '''Remote multi sequenced storage uses sequencing technique in order to build child entity keys.
    It then uses those keys for retreving, storing and deleting entities of those keys.
    This technique has lowest impact on data storage and retreval, and should be used whenever possible!
    
    '''
    limit = kwds.get('limit')
    start_cursor = kwds.get('start_cursor')
    read_from_start = kwds.get('read_from_start')
    results = search_ancestor_sequence(self._property._modelclass, self._entity.key, limit, start_cursor, read_from_start)
    self._property_value = results['entities']
    self._property_value_options['cursor'] = results['cursor']
    self._property_value_options['more'] = results['more']
  
  def read_async(self, **kwds):
    '''Calls storage type specific read function, in order populate _property_value with values.
    'force_read' keyword will always call storage type specific read function.
    However we are not sure if we are gonna need to force read operation.
    
    '''
    if (not self.has_value()) or kwds.get('force_read'):
      read_function = getattr(self, '_read_%s' % self.storage_type)
      read_function(**kwds)
    return self._property_value
  
  def read(self, **kwds):
    self.read_async(**kwds)
    if self.has_future():
      self._property_value = self._property_value.get_result()
    return self._property_value
  
  def _update_local(self):
    '''We do not call anything when we work with local storage.
    That is intentional behavior because local storage is on entity and it mutates on it.
    
    '''
    pass
  
  def _update_remote_single(self):
    '''Ensure that every entity has the entity ancestor by enforcing it.
    
    '''
    if self._property_value.key_parent != self._entity.key:
      key_id = self._property_value.key_id
      self._property_value.set_key(key_id, parent=self._entity.key)
      self._property_value.put()
  
  def _update_remote_multi(self):
    '''Ensure that every entity has the entity ancestor by enforcing it.
    
    '''
    for entity in self._property_value:
      if entity.key_parent != self._entity.key:
        key_id = entity.key_id
        entity.set_key(key_id, parent=self._entity.key)
    put_multi(self._property_value)
  
  def _update_remote_multi_sequenced(self):
    '''Ensure that every entity has the entity ancestor by enforcing it.
    
    '''
    last_sequence = self._property._modelclass.query(ancestor=self._entity.key).count()
    for i, entity in enumerate(self._property_value):
      if entity.key_id is None:
        entity.set_key(str(last_sequence), parent=self._entity.key)
        last_sequence += 1
      else:
        entity.set_key(str(i), parent=self._entity.key)
    put_multi(self._property_value)
  
  def update(self):
    if self.has_value():
      update_function = getattr(self, '_update_%s' % self.storage_type)
      update_function()
    else:
      pass


class SuperKeyPropertyManager(SuperPropertyManager):
  
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
    if not self.has_value():
      self._read()
    return self._property_value
  
  def read(self):
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


##########################################################
########## Reusable data processiong functions. ##########
##########################################################


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
  return isinstance(field, (SuperStructuredProperty, SuperLocalStructuredProperty)) and field._modelclass


def _rule_read(permissions, entity, field_key, field):
  '''If the field is invisible, ignore substructure permissions and remove field along with entire substructure.
  Otherwise go one level down and check again.
  
  '''
  if (not field_key in permissions) or (not permissions[field_key]['visible']):
    entity.remove_output(field_key)
  else:
    if is_structured_field(field):
      child_entity = getattr(entity, field_key)
      if field._repeated:
        if child_entity is not None:  # @todo We'll see how this behaves for def write as well, because None is sometimes here when they are expando properties.
          for child_entity_item in child_entity:
            child_fields = child_entity_item.get_fields()
            child_fields.update(dict([(p._code_name, p) for _, p in child_entity_item._properties.items()]))
            for child_field_key, child_field in child_fields.items():
              _rule_read(permissions[field_key], child_entity_item, child_field_key, child_field)
      else:
        child_entity = getattr(entity, field_key)
        if child_entity is not None:  # @todo We'll see how this behaves for def write as well, because None is sometimes here when they are expando properties.
          child_fields = child_entity.get_fields()
          child_fields.update(dict([(p._code_name, p) for _, p in child_entity._properties.items()]))
          for child_field_key, child_field in child_fields.items():
            _rule_read(permissions[field_key], child_entity, child_field_key, child_field)


def _rule_write(permissions, entity, field_key, field, field_value):
  '''If the field is writable, ignore substructure permissions and override field fith new values.
  Otherwise go one level down and check again.
  
  '''
  #print '%s.%s=%s' % (entity.__class__.__name__, field_key, field_value)
  if (field_key in permissions) and not (permissions[field_key]['writable']):
    try:
      #if field_value is None:  # @todo This is bug. None value can not be supplied on fields that are not required!
      #  return
      setattr(entity, field_key, field_value)
    except TypeError as e:
      util.logger('write: setattr error: %s' % e)
    except ComputedPropertyError:
      pass
  else:
    if is_structured_field(field):
      child_entity = getattr(entity, field_key)
      for child_field_key, child_field in field.get_model_fields().items():
        if field._repeated:
          for i, child_entity_item in enumerate(child_entity):
            try:
              child_field_value = getattr(field_value[i], child_field_key)
              _rule_write(permissions[field_key], child_entity_item, child_field_key, child_field, child_field_value)
            except IndexError as e:
              pass
        else:
          _rule_write(permissions[field_key], child_entity, child_field_key, child_field, getattr(field_value, child_field_key))


def rule_write(entity, original):
  entity_fields = entity.get_fields()
  for field_key, field in entity_fields.items():
    field_value = getattr(original, field_key)
    _rule_write(entity._field_permissions, entity, field_key, field, field_value)


def rule_read(entity):
  entity_fields = entity.get_fields()
  for field_key, field in entity_fields.items():
    _rule_read(entity._field_permissions, entity, field_key, field)


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
  _use_field_rules = True  # All models by default respect rule engine!
  
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
  
  def _pre_put_hook(self):
    if self._use_field_rules and hasattr(self, '_original'):
      rule_write(self, self._original)
  
  def _post_put_hook(self, future):
    entity = self
    for field in entity.get_fields():
      value = getattr(entity, field)
      if isinstance(value, StorageEntityManager):
        value.update()
  
  def _make_async_calls(self):
    entity = self
    if entity.key and entity.key.id():
      for field, field_instance in entity.get_fields().items():
        if isinstance(field_instance, SuperAsyncProperty):
          manager = field_instance._get_value(entity, internal=True)
          manager.get_async()
  
  @classmethod
  def _post_get_hook(cls, key, future):
    entity = future.get_result()
    if entity is not None:
      entity.make_original()
    entity._make_async_calls()
  
  @classmethod
  def _from_pb(cls, pb, set_key=True, ent=None, key=None):
    entity = super(_BaseModel, cls)._from_pb(pb, set_key, ent, key)
    entity.make_original()
    entity._make_async_calls()
    return entity
  
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
        if isinstance(value, StorageEntityManager):
          value = value.read()
        value = copy.deepcopy(value)
        try:
          setattr(new_entity, field, value)
        except ComputedPropertyError as e:
          pass  # This is intentional
        except Exception as e:
          #util.logger('__deepcopy__ - could not copy %s.%s' % (self.__class__.__name__, field))
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
  
  def make_original(self):
    '''This function will make a copy of the current state of the entity
    and put it into _original field.
    
    '''
    if self._use_field_rules:
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
    if self._use_field_rules and hasattr(self, '_field_permissions'):
      rule_read(self)  # Apply rule read before output.
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


class SuperLocalStructuredProperty(_BaseProperty, LocalStructuredProperty):
  
  def __init__(self, *args, **kwargs):
    args = list(args)
    if isinstance(args[0], basestring):
      args[0] = Model._kind_map.get(args[0])
    super(SuperLocalStructuredProperty, self).__init__(*args, **kwargs)
    self._storage = 'local'
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    dic = super(SuperLocalStructuredProperty, self).get_meta()
    dic['model'] = self._modelclass.get_fields()
    return dic
  
  def get_model_fields(self):
    return self._modelclass.get_fields()
  
  def format(self, value):
    return _structured_property_format(self, value)
  
  def _retrieve_value(self, entity, default=None):
    '''Internal helper to retrieve the value for this Property from an entity.

    This returns None if no value is set, or the default argument if
    given.  For a repeated Property this returns a list if a value is
    set, otherwise None.  No additional transformations are applied.
    '''
    entity_manager = entity._values.get(self._name, default)
    if isinstance(entity_manager, StorageEntityManager):
      return entity_manager.read()
    return entity_manager

  def _get_value(self, entity):
    # __get__
    manager = '%s_manager' % self._name
    if manager in entity._values:
      return entity._values[manager]
    util.logger('LocalStructured._get_value.%s %s' % (manager, entity))
    value = StorageEntityManager(entity=entity, property=self)
    entity._values[manager] = value
    return value


class SuperStructuredProperty(_BaseProperty, StructuredProperty):
  
  def __init__(self, *args, **kwargs):
    args = list(args)
    if isinstance(args[0], basestring):
      args[0] = Model._kind_map.get(args[0])
    super(SuperStructuredProperty, self).__init__(*args, **kwargs)
    self._storage = 'structured'
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    dic = super(SuperStructuredProperty, self).get_meta()
    dic['model'] = self._modelclass.get_fields()
    return dic
  
  def get_model_fields(self):
    return self._modelclass.get_fields()
  
  def format(self, value):
    return _structured_property_format(self, value)
   
  def _retrieve_value(self, entity, default=None):
    """Internal helper to retrieve the value for this Property from an entity.

    This returns None if no value is set, or the default argument if
    given.  For a repeated Property this returns a list if a value is
    set, otherwise None.  No additional transformations are applied.
    """
    entity_manager = entity._values.get(self._name, default)
    if isinstance(entity_manager, StorageEntityManager):
      return entity_manager.read()
    return entity_manager
  
  def _get_value(self, entity):
    # __get__
    manager = '%s_manager' % self._name
    if manager in entity._values:
      return entity._values[manager]
    util.logger('StructuredProperty._get_value.%s %s' % (manager, entity))
    value = StorageEntityManager(entity=entity, property=self)
    entity._values[manager] = value
    return value
 


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


class SuperEntityStorageProperty(Property):
  '''
   This property is not meant to be used as property storage. It should be always defined as virtual property.
   E.g. the property that never gets saved to the datastore.
  '''
 
  _indexed = False
  _modelclass = None
  _repeated = False
 
  def __init__(self, modelclass,
               name=None, compressed=False, keep_keys=True,
               **kwds):
    ## here we can construct more configurations
    self._storage = kwds.pop('storage')
    self._modelclass = modelclass
 
    if self._storage in ['children_multi', 'range_children_multi']:
      self._repeated = True # always enforce repeated on multi entity storage engine
    
    super(SuperEntityStorageProperty, self).__init__(name, **kwds)
    
  def format(self, value):
    return _structured_property_format(self, value)
  
  def _set_value(self, entity, value):
    # __set__
    entity_manager = self._get_user_value(entity)
    entity_manager.set(value)

  def _delete_value(self, entity):
    # __delete__
    entity_manager = self._get_value(entity)
    entity_manager.delete()
  
  def _get_value(self, entity):
    # __get__
    manager = '%s_manager' % self._name
    if manager in entity._values:
      return entity._values[manager]
    util.logger('SuperEntityStorageProperty._get_value.%s %s' % (manager, entity))
    value = StorageEntityManager(entity=entity, property=self)
    entity._values[manager] = value
    return value
  
  def _prepare_for_put(self, entity):
    self._get_value(entity)  # For its side effects.
    
    
class SuperAsyncProperty(SuperKeyProperty):
  '''
   @docstring
  '''
  
  def __init__(self, *args, **kwargs):
    self._callback = kwargs.pop('callback', None)
    self._format_callback = kwargs.pop('format_callback', None)
    self._kind = kwargs.pop('kind', None)
    self._target_field = kwargs.pop('target_field', None)
    
    if not self._target_field and not self._callback:
      raise PropertyError('You must provide either: `callback` or `target_field`')
    
    if self._callback != None and not callable(self._callback):
      raise PropertyError('`callback` must be a callable, got %s' % self._callback)
    if self._format_callback != None and not callable(self._format_callback):
      raise PropertyError('`format_callback` must be either None or callable, got %s' % self._format_callback)
    super(SuperAsyncProperty, self).__init__(*args, **kwargs)
  
  def _set_value(self, entity, value):
    # __set__
    async_manager = self._get_value(entity, internal=True)
    async_manager.set(value)
    return super(SuperAsyncProperty, self)._set_value(entity, value)

  def _delete_value(self, entity):
    # __delete__
    async_manager = self._get_value(entity, internal=True)
    async_manager.delete()
    return super(SuperAsyncProperty, self)._delete_value(entity)
  
  def _retrieve_value(self, entity, default=None):
    """Internal helper to retrieve the value for this Property from an entity.

    This returns None if no value is set, or the default argument if
    given.  For a repeated Property this returns a list if a value is
    set, otherwise None.  No additional transformations are applied.
    """
    entity_manager = entity._values.get(self._name, default)
    if isinstance(entity_manager, AsyncEntityManager):
      return entity_manager.get()
    return entity_manager

  def _get_value(self, entity, internal=None):
    # __get__
    manager = '%s_manager' % self._name
    if manager in entity._values:
      async_manager = entity._values[manager]
    else:
      util.logger('SuperAsyncProperty._get_value.%s %s' % (manager, entity))
      async_manager = AsyncEntityManager(entity=entity, property=self)
      entity._values[manager] = async_manager
    if internal: # if is internal is true, always retrieve manager
      return async_manager
    if not async_manager.has_value():
      return async_manager
    else:
      return async_manager.get()