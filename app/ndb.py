# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import decimal
import hashlib
 
from google.appengine.ext.ndb import *

from app import pyson
 
ctx = get_context()

# memory policy for google app engine ndb calls is set to false, instead we decide per `get` wether to use memcache or not
ctx.set_memcache_policy(False)

# We always put double underscore for our private functions in order to avoid ndb library from clashing with our code
# see https://groups.google.com/d/msg/appengine-ndb-discuss/iSVBG29MAbY/a54rawIy5DUJ

class _BaseModel():
  
  __original_values = {}
  
  def _pre_put_hook(self):
      for p in self._properties:
          prop = self._properties.get(p)
          if prop and hasattr(prop, '_writable') and prop._writable:
             self.__resolve_writable(prop)
 
  def __resolve_writable(self, prop):
      if isinstance(prop._writable, pyson.PYSON):
         environ = EvalEnvironment(self)
         encoded = pyson.PYSONEncoder(environ).encode(prop._writable)
         check = pyson.PYSONDecoder(environ).decode(encoded)
         if not check:
            # if the evaluation is not true, set the original values because new value is not allowed to be set
            prop._set_value(self, self.__original_values.get(prop._name))
    
  def original_values(self):
      for p in self._properties:
          self.__original_values[p] = self._properties[p]._get_value(self)
    
  @classmethod
  def _from_pb(cls, *args, **kwargs):
    """ Allows for model to get original values who get loaded from the protocol buffer  """
      
    entity = super(_BaseModel, cls)._from_pb(*args, **kwargs)
    entity.original_values()
    return entity

  @classmethod
  def _get_kind(cls):
    """Return the kind name for this class.

    This defaults to cls.__name__; users may overrid this to give a
    class a different on-disk name than its class name.
    """
    if hasattr(cls, '_KIND'):
       if cls._KIND < 0:
          raise TypeError('Invalid _KIND ID %s, for %s' % (cls._KIND, cls.__name__)) 
       return str(cls._KIND)
    return cls.__name__

class BaseModel(_BaseModel, Model):
  """
   Base class for all `ndb.Model` entities
  """
  
class BaseExpando(_BaseModel, Expando):
  """
   Base class for all `ndb.Expando` entities
  """
  def has_expando_fields(self):
      if hasattr(self, 'EXPANDO_FIELDS'):
         return self.EXPANDO_FIELDS
      else:
         return False
      
  def __getattr__(self, name):
     ex = self.has_expando_fields()
     if ex:
        vf = ex.get(name) 
        if vf:
           return vf._get_value(self)
     return super(BaseExpando, self).__getattr__(name)
    
  def __setattr__(self, name, value):
      ex = self.has_expando_fields()
      if ex:
         vf = ex.get(name) 
         if vf:
            vf._code_name = name
            self._properties[name] = vf
            vf._set_value(self, value)
            return vf
      return super(BaseExpando, self).__setattr__(name, value)
    
  def __delattr__(self, name):
     ex = self.has_expando_fields()
     if ex:
        vf = ex.get(name) 
        if vf:
           vf._delete_value(self)
           if vf in self.__class__._properties:
               raise RuntimeError('Property %s still in the list of properties for the '
                                     'base class.' % name)
           del self._properties[name]
     return super(BaseExpando, self).__delattr__(name)

class _BaseProperty(object):
  
  _writable = False
  _visible = False
 
  def __init__(self, *args, **kwds):
      self._writable = kwds.pop('writable', self._writable)
      self._visible = kwds.pop('visible', self._visible)
 
      super(_BaseProperty, self).__init__(*args, **kwds)

class BaseProperty(_BaseProperty, Property):
  """
   Base property class for all properties capable of having writable, and visible options
  """
 
class SuperStringProperty(_BaseProperty, StringProperty):
    pass

class SuperIntegerProperty(_BaseProperty, IntegerProperty):
    pass
   
class SuperStateProperty(_BaseProperty, IntegerProperty):
 
    def __get__(self, entity, unused_cls=None):
        value = super(SuperStateProperty, self).__get__(entity, unused_cls)
        return entity.resolve_state_name_by_code(value)

    def __set__(self, entity, value):
      """Descriptor protocol: set the value on the entity."""
      value = entity.resolve_state_code_by_name(value)
      super(SuperStateProperty, self).__get__(entity, value)
  
class SuperKeyProperty(_BaseProperty, KeyProperty):
    pass
 
class DecimalProperty(SuperStringProperty):
  """Decimal property that accepts only `decimal.Decimal`"""
  
  def _validate(self, value):
    if not isinstance(value, (decimal.Decimal)):
      raise TypeError('expected an decimal, got %s' % repr(value)) # explicitly allow only decimal

  def _to_base_type(self, value):
      return str(value) # Doesn't matter which type, always return in string format

  def _from_base_type(self, value):
      return decimal.Decimal(value)  # Always return a decimal

      
class ReferenceProperty(SuperKeyProperty):
    
  """Replicated property from `db` module"""
    
  def _validate(self, value):
      if not isinstance(value, Model):
         raise TypeError('expected an ndb.Model, got %s' % repr(value))

  def _to_base_type(self, value):
      return value.key

  def _from_base_type(self, value):
      return value.get()

class SuperRelationProperty(dict):
  """
    This is a fake property that will `not` be stored in datastore,
     it only represents on what one model can depend. Like so
     
     class UserChildEntity(ndb.BaseModel):
           user = ndb.SuperRelationProperty(User)
           name = ndb.StringProperty(required=True, writable=Eval('user.state') != 'active')
           
     foo = UserChildEntity(name='Edward')
     foo.user = ndb.Key('User', 'foo').get() # since this is a Fake property, it cannot be placed via model constructor
     foo.save()     
     
     The `Eval` will evaluate: self.user.state != 'active' and therefore the property
     will validate itself to be read only
     
     This property only accepts model that needs validation, otherwise it will accept any value provided
  """
  def __get__(self, entity):
      """Descriptor protocol: get the value on the entity."""
      return self.model
      
  def __set__(self, entity, value):
      """Descriptor protocol: set the value on the entity."""
      if self.model_type:
         if not isinstance(value, self.model_type):
            raise TypeError('Expected %s, got %s' % (repr(self.model_type), repr(value)))
      self.model = value
 
  def __init__(self, model=None):
      self.model_type = model
  
  def __getitem__(self, item):
     return getattr(self.model, item)
      
  def __getattr__(self, item):
     try:
        return self.__getitem__(item)
     except KeyError, exception:
        raise AttributeError(*exception.args)
      
  def get(self, item, default=None):
     try:
        return self.__getitem__(item)
     except Exception:
        pass
     return super(SuperRelationProperty, self).get(item, default)     
 
class Validator:
    
  """
   Validator class that can be used for keyword argument `validator` in properties
   Example:
      
   def limit_count(prop, value, limit=100):
       if len(value) > limit:
           return False
       return True
      
   ndb.StringProperty(validator=ndb.Validator(limit_count, limit=100))
  """
    
  def __init__(self, callback, **kwargs):
      self.kwargs = kwargs
      self.callback = callback
    
  def __call__(self, prop, value):
      return self.callback(prop, value, **self.kwargs)
  
class EvalEnvironment(dict):

  def __init__(self, record):
     super(EvalEnvironment, self).__init__()
     self._record = record
        
  def __getitem__(self, item):
     if item in self._record._properties:
        items = item.split('.') # if Eval('object.foo.bar') it will digg till it reaches to .bar
        g = None
        for i in items:
            if not g:
               g = self._record
            # this will throw AttributError if Eval() is not configured properly, or model does not posses the actual
            # object that will return the attribute, wether that be `None` or `False` the attribute must exist
            g = getattr(g, i)
        return g
     return super(EvalEnvironment, self).__getitem__(item)

  def __getattr__(self, item):
      try:
         return self.__getitem__(item)
      except KeyError, exception:
         raise AttributeError(*exception.args)

  def get(self, item, default=None):
      try:
        return self.__getitem__(item)
      except Exception:
        pass
      return super(EvalEnvironment, self).get(item, default)

  def __nonzero__(self):
      return bool(self._record)