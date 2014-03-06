# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import decimal
import cgi
import importlib

from google.appengine.ext.ndb import *
from google.appengine.ext.ndb import polymodel
from google.appengine.ext import blobstore
from google.appengine.api import images

import cloudstorage

from app import util


# We always put double underscore for our private functions in order to avoid collision between our code and ndb library.
# For details see: https://groups.google.com/d/msg/appengine-ndb-discuss/iSVBG29MAbY/a54rawIy5DUJ

# We set memory policy for google app engine ndb calls to False, and decide whether to use memcache or not per 'get' call.
ctx = get_context()
ctx.set_memcache_policy(False)
# ctx.set_cache_policy(False)


class PropertyError(Exception):
  pass


def _validate_prop(value, prop):
  """This helper function will raise exception based on ndb property specifications
  (max_size, required, choices).
  
  """
  if prop._max_size:
    if len(value) > prop._max_size:
      raise PropertyError('max_size_exceeded')
  if value is None and prop._required:
    raise PropertyError('required')
  if hasattr(prop, '_choices') and prop._choices:
    if value not in prop._choices:
      raise PropertyError('not_in_specified_choices')

def _property_value(prop, value):
  if value is None and not prop._required:
    if prop._default is not None:
      value = prop._default
  if prop._repeated:
    if not isinstance(value, (list, tuple)):
      value = [value]
    out = []
    for v in value:
      _validate_prop(v, prop)
      out.append(v)
    return out
  else:
    _validate_prop(value, prop)
    return value

def make_complete_name(entity, name_property, parent_property=None, separator=None):
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

def factory(module_model_path):
  """Retrieves model by its module path
  (e.g. model = factory('app.srv.log.Record'), where 'model' will be Record class).
  
  """
  custom_kinds = module_model_path.split('.')
  far = custom_kinds[-1]
  del custom_kinds[-1]
  try:
    module = importlib.import_module(".".join(custom_kinds))
  except Exception as e:
    util.logger('Failed to import %s. Error: %s.' % (module_model_path, e), 'exception')
    return None
  return getattr(module, far)

# Monkeypatch ndb.Key
def _get_entity(self):
  return self.get()

Key.entity = property(_get_entity)


class _BaseModel(object):
  
  def __init__(self, *args, **kwargs):
    super(_BaseModel, self).__init__(*args, **kwargs)
    self._output = []
    for key in self.get_fields():
      self.add_output(key)
    self.add_output('_actions')
  
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
  
  def __todict__(self):
    """
    This function returns dictionary of stored or dynamically generated data (but not meta data) of the model.
    Currently however, 'self._output' contains '_actions' branch, which is meta data, and in the future should be
    excluded from 'self._output'. The future convention would rename this function from '__todict__' to 'get_output', 
    and include 'get_meta' function in '_BaseModel' which will return dictionary of meta data of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    """
    dic = {}
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
  
  def loaded(self):
    return self.key != None and self.key.id()
  
  @classmethod
  def build_key(cls, *args, **kwargs):
    new_args = [cls._get_kind()]
    new_args.extend(args)
    return Key(*new_args, **kwargs)
  
  def set_key(self, *args, **kwargs):
    self._key = self.build_key(*args, **kwargs)
    return self._key
  
  @classmethod
  def _get_kind(cls):
    """Return the kind name for this class.
    Return value defaults to cls.__name__.
    Users may override this method to give a class different on-disk name than its class name.
    We overide this method in order to numerise kinds and conserve datastore space.
    
    """
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
    class_actions = getattr(cls, '_actions', {})
    for key, action in class_actions.items():
      actions[action.key.urlsafe()] = action
    return actions
  
  def get_instance_fields(self):
    fields = {}
    for prop_key, prop in self._properties.items():
      fields[prop._code_name] = prop
    virtual_fields = self.get_instance_virtual_fields()
    if virtual_fields:
      fields.update(virtual_fields)
    if hasattr(self, 'get_instance_expando_fields'):
      expando_fields = self.get_instance_expando_fields()
      if expando_fields:
        fields.update(expando_fields)
    return fields
  
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
  
  def get_instance_virtual_fields(self):
    if hasattr(self, '_virtual_fields'):
      for prop_key, prop in self._virtual_fields.items():
        if not prop._code_name:
          prop._code_name = prop_key
      return self._virtual_fields
    else:
      return False
  
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
  
  def __getattr__(self, name):
    virtual_fields = self.get_virtual_fields()
    if virtual_fields:
      prop = virtual_fields.get(name)
      if prop:
        return prop._get_value(self)
    return super(_BaseModel, self).__getattr__(name)
  
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
    return super(BaseExpando, self).__delattr__(name)
  
  @property
  def key_id(self):
    return self.key.id()
  
  @property
  def key_id_str(self):
    return str(self.key_id)
  
  @property
  def key_namespace(self):
    return self.key.namespace()
  
  @property
  def key_parent(self):
    return self.key.parent()
  
  @property
  def namespace_entity(self):
    if self.key.namespace():
      return Key(urlsafe=self.key.namespace()).get()
    else:
      return None
  
  @property
  def parent_entity(self):
    if self.key.parent():
      return self.key.parent().get()
    else:
      return None


class BaseModel(_BaseModel, Model):
  """Base class for all 'ndb.Model' entities."""


class BasePoly(_BaseModel, polymodel.PolyModel):
  
  @classmethod
  def _get_hierarchy(cls):
    """Internal helper method to return the list of polymorphic base classes.
    This returns a list of class objects, e.g. [Animal, Feline, Cat].
    
    """
    bases = []
    for base in cls.mro():  # pragma: no branch
      if hasattr(base, '_get_hierarchy') and base.__name__ not in ('BasePoly', 'BasePolyExpando'):
        bases.append(base)
    del bases[-1]  # Delete PolyModel itself.
    bases.reverse()
    return bases
  
  @classmethod
  def _get_kind(cls):
    if hasattr(cls, '_kind'):
      if cls._kind < 0:
        raise TypeError('Invalid _kind %s, for %s.' % (cls._kind, cls.__name__))
      return str(cls._kind)
    return cls.__name__
  
  @classmethod
  def _class_name(cls):
    if hasattr(cls, '_kind'):
      if cls._kind < 0:
        raise TypeError('Invalid _kind %s, for %s.' % (cls._kind, cls.__name__))
      return str(cls._kind)
    return cls.__name__


class BaseExpando(_BaseModel, Expando):
  """Base class for all 'ndb.Expando' entities."""
  
  def get_instance_expando_fields(self):
    if hasattr(self, '_expando_fields'):
      for prop_key, prop in self._expando_fields.items():
        if not prop._code_name:
          prop._code_name = prop_key
      return self._expando_fields
    else:
      return False
  
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
    """Internal helper method to get the Property for a protobuf-level property."""
    
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


class _BaseProperty(object):
  
  _max_size = None
  
  def __todict__(self):
    """
    This function returns dictionary of meta data (not stored or dynamically generated data, like it's 
    counterpart in _BaseModel does) of the model. The future convention would rename this function 
    from '__todict__' to 'get_meta'.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    """
    choices = self._choices
    if choices:
      choices = list(self._choices)
    return {
            'verbose_name': getattr(self, '_verbose_name'),
            'required': self._required,
            'max_size': self._max_size,
            'choices':  choices,
            'default': self._default,
            'repeated': self._repeated,
            'type': self.__class__.__name__,
            }
  
  def __init__(self, *args, **kwds):
    self._max_size = kwds.pop('max_size', self._max_size)
    custom_kind = kwds.get('kind')
    if custom_kind and isinstance(custom_kind, basestring) and '.' in custom_kind:
      kwds['kind'] = factory(custom_kind)
    super(_BaseProperty, self).__init__(*args, **kwds)


class BaseProperty(_BaseProperty, Property):
  """Base property class for all properties capable of having _max_size option."""


class SuperLocalStructuredProperty(_BaseProperty, LocalStructuredProperty):
  
  def __todict__(self):
    """
    This function returns dictionary of meta data (not stored or dynamically generated data, like it's 
    counterpart in _BaseModel does) of the model. The future convention would rename this function 
    from '__todict__' to 'get_meta'.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    """
    response = super(SuperLocalStructuredProperty, self).__todict__()
    response['model'] = self._modelclass.get_fields()
    return response


class SuperStructuredProperty(_BaseProperty, StructuredProperty):
  
  def __todict__(self):
    """
    This function returns dictionary of meta data (not stored or dynamically generated data, like it's 
    counterpart in _BaseModel does) of the model. The future convention would rename this function 
    from '__todict__' to 'get_meta'.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    """
    response = super(SuperStructuredProperty, self).__todict__()
    response['model'] = self._modelclass.get_fields()
    return response


class SuperPickleProperty(_BaseProperty, PickleProperty):
  pass


class SuperDateTimeProperty(_BaseProperty, DateTimeProperty):
  pass


class SuperJsonProperty(_BaseProperty, JsonProperty):
  pass


class SuperTextProperty(_BaseProperty, TextProperty):
  
  def format(self, value):
    value = _property_value(self, value)
    if self._repeated:
      return [unicode(v) for v in value]
    else:
      return unicode(value)


class SuperStringProperty(_BaseProperty, StringProperty):
  
  def format(self, value):
    value = _property_value(self, value)
    if self._repeated:
      return [unicode(v) for v in value]
    else:
      return unicode(value)


class SuperFloatProperty(_BaseProperty, FloatProperty):
  
  def format(self, value):
    value = _property_value(self, value)
    if self._repeated:
      return [float(v) for v in value]
    else:
      return float(value)


class SuperIntegerProperty(_BaseProperty, IntegerProperty):
  
  def format(self, value):
    value = _property_value(self, value)
    if self._repeated:
      return [long(v) for v in value]
    else:
      return long(value)


class SuperKeyProperty(_BaseProperty, KeyProperty):
  
  def format(self, value):
    if self._repeated:
      if not isinstance(value, (tuple, list)):
        value = [value]
      returns = [Key(urlsafe=v) for v in value]
      single = False
    else:
      returns = [Key(urlsafe=value)]
      single = True
    
    for k in returns:
      if self._kind and k.kind() != self._kind:
        raise PropertyError('invalid_kind')
    
    items = get_multi(returns, use_cache=True)
    for i, item in enumerate(items):
      if item is None:
        raise PropertyError('not_found_%s' % returns[i].urlsafe())
    
    if single:
      return returns[0]
    else:
      return returns


class SuperBooleanProperty(_BaseProperty, BooleanProperty):
  
  def format(self, value):
    value = _property_value(self, value)
    if self._repeated:
      return [bool(long(v)) for v in value]
    else:
      return bool(long(value))


class SuperBlobKeyProperty(_BaseProperty, BlobKeyProperty):
  
  def format(self, value):
    value = _property_value(self, value)
    if self._repeated:
      values = []
      for v in value:
        # This alone will raise error if the upload is malformed.
        blob = blobstore.parse_blob_info(v)
        values.append(blob.key())
      return values
    else:
      # This alone will raise error if the upload is malformed.
      blob = blobstore.parse_blob_info(value)
      return blob.key()


class SuperRawProperty(SuperStringProperty):
  
  def format(self, value):
    value = _property_value(self, value)
    return value


class SuperImageKeyProperty(_BaseProperty, BlobKeyProperty):
  
  def format(self, value):
    value = _property_value(self, value)
    if not self._repeated:
      blobs = [value]
      value = blobstore.parse_blob_info(value).key()
    else:
      blobs = value
      value = [blobstore.parse_blob_info(val).key() for val in value]
    
    for blob in blobs:
      info = blobstore.parse_file_info(blob)
      meta_required = ('image/jpeg', 'image/jpg', 'image/png')
      if info.content_type not in meta_required:
        raise PropertyError('invalid_file_type')
      # This code below is used to validate if the blob that's uploaded to gcs is an image.
      gs_object_name = info.gs_object_name
      cloudstorage_file = cloudstorage.open(filename=gs_object_name[3:])
      image_data = cloudstorage_file.read()  # We must read the file in order to analyize width/height of an image.
      # Will throw error if the file is not an image, or it's just corrupted.
      load_image = images.Image(image_data=image_data)
      # Closes the pipeline.
      cloudstorage_file.close()
      del load_image, cloudstorage_file  # Free memory.
    
    return value


class SuperLocalStructuredImageProperty(SuperLocalStructuredProperty):
  
  @classmethod
  def _format_value(cls, prop, value):
    """This function is used for structured and also for local property,
    because its formatting logic is identical
    
    """
    value = _property_value(prop, value)
    if not prop._repeated:
      blobs = [value]
    else:
      blobs = value
    
    models = []
    for blob in blobs:
      # These will throw errors if the 'blob' is not cgi.FileStorage.
      file_info = blobstore.parse_file_info(blob)
      blob_info = blobstore.parse_blob_info(blob)
      meta_required = ('image/jpeg', 'image/jpg', 'image/png')
      if file_info.content_type not in meta_required:
        raise PropertyError('invalid_image_type')
      gs_object_name = file_info.gs_object_name
      cloudstorage_file = cloudstorage.open(filename=gs_object_name[3:])
      # This will throw an error if the file does not exist in cloudstorage.
      image_data = cloudstorage_file.read()  # We must read the file in order to analyize width/height of an image.
      # Will throw error if the file is not an image, or its corrupted.
      load_image = images.Image(image_data=image_data)
      # Closes the pipeline.
      cloudstorage_file.close()
      # _modelclass (SuperLocalStructuredImageProperty(ModelClass)) must have
      # 'width', 'height', 'size', and 'image' properties (see @app.srv.blob.Image as an example).
      models.append(prop._modelclass(**{
                                        'width': load_image.width,
                                        'height': load_image.height,
                                        'size': file_info.size,
                                        'content_type': file_info.content_type,
                                        'image': blob_info.key(),
                                        }))
      del image_data, load_image  # Free memory?
    
    if not prop._repeated:
      if len(models):
        return models[0]
      else:
        return None
    else:
      return models
  
  def format(self, value):
    return self._format_value(self, value)


class SuperStructuredImageProperty(SuperStructuredProperty):
  
  def format(self, value):
    return SuperLocalStructuredImageProperty._format_value(self, value)


class SuperDecimalProperty(SuperStringProperty):
  """Decimal property that accepts only 'decimal.Decimal'"""
  
  def format(self, value):
    value = _property_value(self, value)
    if self._repeated:
      value = [decimal.Decimal(v) for v in value]
    else:
      value = decimal.Decimal(value)
    if value is None:
      raise PropertyError('invalid_number')
    return value
  
  def _validate(self, value):
    if not isinstance(value, (decimal.Decimal)):
      raise PropertyError('expected_decimal') # Perhaps, here should be some other type of exception?
  
  def _to_base_type(self, value):
    return str(value)
  
  def _from_base_type(self, value):
    return decimal.Decimal(value)
