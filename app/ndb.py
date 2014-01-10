# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import decimal

from google.appengine.ext.ndb import *
from google.appengine.ext.ndb import polymodel
 
from app import util
from app.srv import event
 
ctx = get_context()

# memory policy for google app engine ndb calls is set to false, instead we decide per `get` wether to use memcache or not
ctx.set_memcache_policy(False)
#ctx.set_cache_policy(False)

# We always put double underscore for our private functions in order to avoid ndb library from clashing with our code
# see https://groups.google.com/d/msg/appengine-ndb-discuss/iSVBG29MAbY/a54rawIy5DUJ

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
     
     `model` will be a Country class.
     
    """
    custom_kinds = module_model_path.split('.')
    far = custom_kinds[-1] 
    del custom_kinds[-1] 
         
    return getattr(util.import_module(".".join(custom_kinds)), far)
   
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

  def get_kind(self):
      return self._get_kind()
 
  @classmethod
  def _get_kind(cls):
    """Return the kind name for this class.

    This defaults to cls.__name__; users may overrid this to give a
    class a different on-disk name than its class name.
    """
    if hasattr(cls, 'KIND_ID'):
       if cls.KIND_ID < 0:
          raise TypeError('Invalid KIND_ID %s, for %s' % (cls.KIND_ID, cls.__name__)) 
       return str(cls.KIND_ID)
    return cls.__name__
  
  @classmethod
  def get_actions(cls):
      return getattr(cls, '_actions', {})
  
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
 
  @classmethod
  def create(cls, values, **kwargs):
        return cls.manage(True, values, **kwargs)
    
  @classmethod
  def update(cls, values, **kwargs):
        return cls.manage(False, values, **kwargs)

 
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
      if hasattr(cls, 'KIND_ID'):
        if cls.KIND_ID < 0:
          raise TypeError('Invalid KIND_ID %s, for %s' % (cls.KIND_ID, cls.__name__))
        return str(cls.KIND_ID)
      return cls.__name__
  
   @classmethod
   def _class_name(cls):
      if hasattr(cls, 'KIND_ID'):
        if cls.KIND_ID < 0:
          raise TypeError('Invalid KIND_ID %s, for %s' % (cls.KIND_ID, cls.__name__))
        return str(cls.KIND_ID)
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
 
    _max_size = False
 
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
    pass
 
class SuperStringProperty(_BaseProperty, StringProperty):
    pass

class SuperFloatProperty(_BaseProperty, FloatProperty):
    pass

class SuperIntegerProperty(_BaseProperty, IntegerProperty):
    pass

class SuperDateTimeProperty(_BaseProperty, DateTimeProperty):
    pass

class SuperKeyProperty(_BaseProperty, KeyProperty):
    pass

class SuperBooleanProperty(_BaseProperty, BooleanProperty):
    pass

class SuperBlobKeyProperty(_BaseProperty, BlobKeyProperty):
    pass

class SuperImageKeyProperty(_BaseProperty, BlobKeyProperty):
    pass

class SuperJsonProperty(_BaseProperty, JsonProperty):
    pass
  
class SuperDecimalProperty(SuperStringProperty):
    
    """Decimal property that accepts only `decimal.Decimal`"""
    
    def _validate(self, value):
      if not isinstance(value, (decimal.Decimal)):
        raise TypeError('expected a decimal, got %s' % repr(value)) # explicitly allow only decimal
    
    def _to_base_type(self, value):
        return str(value) # Doesn't matter which type, always return in string format
    
    def _from_base_type(self, value):
        return decimal.Decimal(value)  # Always return a decimal