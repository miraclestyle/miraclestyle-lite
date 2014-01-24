# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
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
 
ctx = get_context()

# memory policy for google app engine ndb calls is set to false, instead we decide per `get` wether to use memcache or not
ctx.set_memcache_policy(False)
#ctx.set_cache_policy(False)

# We always put double underscore for our private functions in order to avoid ndb library from clashing with our code
# see https://groups.google.com/d/msg/appengine-ndb-discuss/iSVBG29MAbY/a54rawIy5DUJ

class DescriptiveError(Exception):
  pass

def _property_value(prop, value):
  
    def validate_max_size(value, size):
        if size:
          if len(value) > size:
             raise DescriptiveError('max_size_exceeded')
  
    if prop._repeated:
       if not isinstance(value, (list, tuple)):
          value = [value]
       out = []   
       for v in value:
           validate_max_size(v, prop._max_size)
           out.append(v)
       return out
    else:
       validate_max_size(value, prop._max_size)
       return value


def make_complete_name(entity, property_name, parent=None, separator=None):
    
    if separator is None:
       separator = unicode(' / ')
       
    gets_entity = entity
    names = []
    while True:
        
        if parent is None:
           parents = gets_entity.key.parent() 
           parents = parents.get()
        else:
           parents = getattr(gets_entity, parent)
           if parents:
              parents = parents.get()
 
        if not parents:
           names.append(getattr(gets_entity, property_name))
           break
        else:
           value = getattr(gets_entity, property_name)
           names.append(value)
           gets_entity = parents
 
    names.reverse()
    return separator.join(names)
       
def factory(module_model_path):
    """
     Retrieves model by its module path. e.g.
     model = factory('app.core.misc.Country')
     
     `model` will be a Country class.
     
    """
    custom_kinds = module_model_path.split('.')
    far = custom_kinds[-1] 
    del custom_kinds[-1] 
    try:
       module = importlib.import_module(".".join(custom_kinds)) # replace util.import_module with importlib.import_module
    except Exception as e:
       util.logger('Failed to import %s. Error: %s' % (module_model_path, e), 'exception')
       return None
    return getattr(module, far)
   
class _BaseModel():
  
  @classmethod
  def build_key(cls, *args, **kwargs):
      new_args = [cls._get_kind()]
      new_args.extend(args)
      return Key(*new_args, **kwargs)
      
  def set_key(self, *args, **kwargs):
      self._key = self.build_key(*args, **kwargs)
      return self._key
  
  def __todict__(self):
      """
        This function can be used to make representation of the model into the dictionary.
        The dictionary can be then used to be translated into other understandable code to clients, e.g. JSON
        
        Currently, this method calls native Model.to_dict() method which converts the values into dictionary format.
      """
      dic = self.to_dict()
      
      if self.key:
         dic['id'] = self.key.urlsafe()
         
      for k,v in dic.items():
          if isinstance(v, Key):
             dic[k] = v.urlsafe()
         
      return dic
   
  def loaded(self):
      return self.key != None and self.key.id()
  
  @classmethod 
  def get_kind(cls):
      return cls._get_kind()
 
  @classmethod
  def _get_kind(cls):
    """Return the kind name for this class.

    This defaults to cls.__name__; users may overrid this to give a
    class a different on-disk name than its class name.
    """
    if hasattr(cls, '_kind'):
       if cls._kind < 0:
          raise TypeError('Invalid _kind %s, for %s' % (cls._kind, cls.__name__)) 
       return str(cls._kind)
    return cls.__name__
  
  @classmethod
  def get_actions(cls):
      actions = getattr(cls, '_actions', {})
      new_actions = {}
      for key,action in actions.items():
          new_actions[action.key.urlsafe()] = action
      return new_actions
  
  @classmethod
  def get_fields(cls):
      fields = {}
      for prop_key,prop in cls._properties.items():
          fields[prop._code_name] = prop
          
      if hasattr(cls, 'get_expando_fields'):
         expandos = cls.get_expando_fields()
         if expandos: 
             for expando_prop_key,expando_prop in expandos.items():
                 fields[expando_prop._code_name] = expando_prop
      return fields
  
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
    """ Base class for all `ndb.Model` entities """

      
class BasePoly(_BaseModel, polymodel.PolyModel):

   @classmethod
   def _get_hierarchy(cls):
      """Internal helper to return the list of polymorphic base classes.
  
      This returns a list of class objects, e.g. [Animal, Feline, Cat].
      """
      bases = []
      for base in cls.mro():  # pragma: no branch
        if hasattr(base, '_get_hierarchy') and base.__name__ not in ('BasePoly', 'BasePolyExpando'):
          bases.append(base)
      del bases[-1]  # Delete PolyModel itself
      bases.reverse()
      return bases   
 
   @classmethod
   def _get_kind(cls):
      if hasattr(cls, '_kind'):
        if cls._kind < 0:
          raise TypeError('Invalid _kind %s, for %s' % (cls._kind, cls.__name__))
        return str(cls._kind)
      return cls.__name__
  
   @classmethod
   def _class_name(cls):
      if hasattr(cls, '_kind'):
        if cls._kind < 0:
          raise TypeError('Invalid _kind %s, for %s' % (cls._kind, cls.__name__))
        return str(cls._kind)
      return cls.__name__
 
  
class BaseExpando(_BaseModel, Expando):
    """ Base class for all `ndb.Expando` entities """
 
    @classmethod
    def get_expando_fields(cls):
        if hasattr(cls, '_expando_fields'):
           for i,v in cls._expando_fields.items():
               if not v._code_name:
                  v._code_name = i 
                  cls._expando_fields[i] = v
                   
           return cls._expando_fields
        else:
           return False
        
    def __getattr__(self, name):
       ex = self.get_expando_fields()
       if ex:
          vf = ex.get(name) 
          if vf:
             return vf._get_value(self)
       return super(BaseExpando, self).__getattr__(name)
      
    def __setattr__(self, name, value):
        ex = self.get_expando_fields()
        if ex:
           vf = ex.get(name) 
           if vf:
              self._properties[vf._name] = vf
              vf._set_value(self, value)
              return vf
        return super(BaseExpando, self).__setattr__(name, value)
      
    def __delattr__(self, name):
       ex = self.get_expando_fields()
       if ex:
          vf = ex.get(name) 
          if vf:
             vf._delete_value(self)
             pname = vf._name
             if vf in self.__class__._properties:
                 raise RuntimeError('Property %s still in the list of properties for the '
                                       'base class.' % name)
             del self._properties[pname]
       return super(BaseExpando, self).__delattr__(name)
   
    def _get_property_for(self, p, indexed=True, depth=0):
        """Internal helper to get the Property for a protobuf-level property."""
        name = p.name()
        parts = name.split('.')
        if len(parts) <= depth:
          # Apparently there's an unstructured value here.
          # Assume it is a None written for a missing value.
          # (It could also be that a schema change turned an unstructured
          # value into a structured one.  In that case, too, it seems
          # better to return None than to return an unstructured value,
          # since the latter doesn't match the current schema.)
          return None
        next = parts[depth]
    
        prop = self._properties.get(next)
        if prop is None:
           expando = self.get_expando_fields()
           if expando:
              for k,v in expando.items():
                  if v._name == next:
                     prop = v
                     self._properties[v._name] = v
                     break        
  
        if prop is None:
          prop = self._fake_property(p, next, indexed)
        return prop
      
class BasePolyExpando(BasePoly, BaseExpando):
      pass

class _BaseProperty(object):
 
    _max_size = None
 
    def __init__(self, *args, **kwds):
      
        self._max_size = kwds.pop('max_size', self._max_size)
         
        custom_kind = kwds.get('kind')
  
        if custom_kind and isinstance(custom_kind, basestring) and '.' in custom_kind:
           kwds['kind'] = factory(custom_kind)
           
            
        super(_BaseProperty, self).__init__(*args, **kwds)
        

class BaseProperty(_BaseProperty, Property):
   """
    Base property class for all properties capable of having writable, and visible options
   """
   
class SuperLocalStructuredProperty(_BaseProperty, LocalStructuredProperty):
    pass
  
class SuperStructuredProperty(_BaseProperty, StructuredProperty):
    pass
    
class SuperPickleProperty(_BaseProperty, PickleProperty):
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
 
class SuperDateTimeProperty(_BaseProperty, DateTimeProperty):
    pass

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
               raise DescriptiveError('invalid_kind')
        
        items = get_multi(returns, use_cache=True)
        
        for i,item in enumerate(items):
            if item is None:
               raise DescriptiveError('not_found_%s' % returns[i].urlsafe())
  
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
           new = []
           for blob in value:
               if not isinstance(blob, cgi.FieldStorage) or 'blob-key' not in blob.type_options:
                  raise ValueError('value provided is not cgi.FieldStorage instance, or its type is not blob-key, or the blob failed to save,\
                   got %r instead.' % blob)
               else:
                  v = blobstore.parse_blob_info(blob)
               new.append(v.key())
           return new
        else:
           if not isinstance(value, cgi.FieldStorage) or 'blob-key' not in value.type_options:
              raise ValueError('value provided is not cgi.FieldStorage instance, or its type is not blob-key, or the blob failed to save, \
              got %r instead.' % value)
           else:
               value = blobstore.parse_blob_info(value)
           return value.key()

class SuperImageKeyProperty(_BaseProperty, BlobKeyProperty):
  
    @classmethod
    def get_image_sizes(cls, field_storages):
         
        @non_transactional
        def operation(field_storages):
            
            sizes = dict()
            single = False
            
            if not isinstance(field_storages, (list, tuple)):
               field_storages = [field_storages]
               single = True
               
            out = []
               
            for field_storage in field_storages:
                
                fileinfo = blobstore.parse_file_info(field_storage)
                blobinfo = blobstore.parse_blob_info(field_storage)
                
                sizes = {}
      
                f = cloudstorage.open(fileinfo.gs_object_name[3:])
                blob = f.read()
        
                image = images.Image(image_data=blob)
                sizes = {}
           
                sizes['width'] = image.width
                sizes['height'] = image.height
                 
                sizes['size'] = fileinfo.size
                sizes['content_type'] = fileinfo.content_type
                sizes['image'] = blobinfo.key()
         
                if not single:
                   out.append(sizes)
                else:
                   out = sizes
     
                f.close()
                
                del blob
                  
            return out
        
        return operation(field_storages)  
  
    def format(self, value):
 
       value = _property_value(self, value)
       
       if not self._repeated:
          blobs = [value]
          value = blobstore.parse_blob_info(value).key()
       else:
          value = [blobstore.parse_blob_info(val).key() for val in value]
          
       for blob in blobs:
           info = blobstore.parse_file_info(blob)
           meta_required = ('image/jpeg', 'image/jpg', 'image/png')
           if info.content_type not in meta_required:
              raise DescriptiveError('invalid_file_type')
           else:
              """
              try:
                  self.get_image_sizes(blob)
              except Exception as e:
                  raise DescriptiveError('invalid_image: %s' % e)
              """
           
       return value

class SuperJsonProperty(_BaseProperty, JsonProperty):
    pass
  
class SuperDecimalProperty(SuperStringProperty):
    
    """Decimal property that accepts only `decimal.Decimal`"""
    
    def format(self, value):
        value = _property_value(self, value)
        if self._repeated:
           value = [decimal.Decimal(v) for v in value]
        else:
           value = decimal.Decimal(value)
           
        if value is None:
           raise ValueError('Invalid number provided')
           
        return value
    
    def _validate(self, value):
      if not isinstance(value, (decimal.Decimal)):
        raise TypeError('expected a decimal, got %s' % repr(value)) # explicitly allow only decimal
    
    def _to_base_type(self, value):
        return str(value) # Doesn't matter which type, always return in string format
    
    def _from_base_type(self, value):
        return decimal.Decimal(value)  # Always return a decimal