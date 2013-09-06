# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import decimal
import hashlib

from app import settings, memcache, pyson
from app.core import logger

from google.appengine.ext.ndb import *
 
contx = get_context()

# memory policy for google app engine ndb calls is set to false, instead we decide per `get` wether to use memcache or not
contx.set_memcache_policy(False)
 
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
 
class _BaseModel:
    
  _KIND = -1
  
  _original_values = {}
  
  def _resolve_writable(self, prop):
      if isinstance(prop._writable, pyson.PYSON):
         environ = EvalEnvironment(self)
         encoded = pyson.PYSONEncoder(environ).encode(prop._writable)
         check = pyson.PYSONDecoder(environ).decode(encoded)
         if not check:
            # if the evaluation is not true, set the original values because new value is not allowed to be set
            setattr(self, prop._name, self._original_values.get(prop._name))
  
  def _pre_put_hook(self):
      for p in self._properties:
          prop = self._properties.get(p)
          if prop and hasattr(prop, '_writable') and prop._writable:
             self._resolve_writable(prop)
           
  def original_values(self, name):
      """
        Sets original value for the property name
      """
      if name in self._original_values:
         return
     
      prop = self._properties.get(name)
      if prop:
         logger('setting original %s for model: %s' % (name, self.__class__.__name__))
         self._original_values[name] = prop._get_value(self)
  
  def _memcache_key(self):
      # memcache generator for this model
      return self._return_memcache_key(self.key.urlsafe())
  
  def _self_clear_memcache(self):
      self._clear_memcache(self.key.urlsafe())
      
  def _self_make_memory(self, structure=None, include_self=None):
      if structure == None:
         structure = {}
      
      if include_self != None:   
         structure['self'] = self
      
      self._make_memory(self.key, structure)
       
  def _self_from_memory(self, segment=None, empty=None):
      return self._get_from_memory(self.key.urlsafe(), segment, empty)    
  
  @classmethod
  def hash_create_key(cls, **kwargs):
      _data = [settings.SALT]
      for k in kwargs:
          _data.append(unicode(kwargs.get(k)))
      hashed = str(hashlib.md5(settings.HASH_BINDER.join(_data)).hexdigest())
      logger('get by hash: %s' % hashed)
      return hashed
  
  @classmethod
  def _hash_get_by_id(cls, async=False, **kwargs):
      
      parent = kwargs.pop('_parent', None)
      app = kwargs.pop('_app', None)
      namespace = kwargs.pop('_namespace', None)
      ctx_options = kwargs.pop('_ctx_options', {})
      ke = cls.hash_create_key(**kwargs)
      
      if async:
         return cls.get_by_id_async(ke, parent, app, namespace, **ctx_options)
      else:
         return cls.get_by_id(ke, parent, app, namespace, **ctx_options)
       
  @classmethod
  def hash_get_by_id(cls, **kwargs):
      return cls._hash_get_by_id(False, **kwargs)
  
  @classmethod
  def hash_get_by_id_async(cls, **kwargs):
      return cls._hash_get_by_id(True, **kwargs)
  
  @classmethod
  def _get_kind(cls):
    """Return the kind name for this class.

    This defaults to cls.__name__; users may overrid this to give a
    class a different on-disk name than its class name.
    """
    if settings.DEBUG:
       return cls.__name__
   
    if cls.__name__ not in ('BaseModel', '_BaseModel', 'BaseExpando'):
       if cls._KIND < 0:
          raise TypeError('Invalid _KIND ID %s, for %s' % (cls._KIND, cls.__name__)) 
    return str(cls._KIND)

  # helper memcache tools
  
  @classmethod
  def _return_memcache_key(cls, kid):
      # `kid` is a ndb.Key(...).urlsafe()
      return str('m-%s' % str(kid))
   
  @classmethod
  def _clear_memcache(cls, kid):
      memcache.delete(cls._return_memcache_key(kid))
  
  @classmethod
  def _make_memory(cls, user, structure, expire=0):
      if not isinstance(structure, dict):
         raise Exception('_make_memory allows only dicts as values')
      memcache.set(cls._return_memcache_key(user.urlsafe()), structure, expire)
  
  @classmethod    
  def _get_from_memory(cls, kid, segment=None, empty=None):
      """
        Allows to retrieve segment or entire memory slot from memory that is this entity, for example saved memcache for user is
        
        user = {
          'self' : User entity,
          'primary_email': UserEmail entity,
          'emails' : [UserEmail...],
          'permissions' : {
              kindID : {
                 kindEntityID : PermissionList
              },
          },
          ...
        }
      """
      gets = memcache.get(cls._return_memcache_key(kid), empty)
      if gets and empty != gets:
         if segment:
            return gets.get(segment, empty) 
         return gets
      return empty

class BaseModel(_BaseModel, Model):
  """
   Base class for all `ndb.Model` entities
  """
  
class BaseExpando(_BaseModel, Expando):
  """
   Base class for all `ndb.Expando` entities
  """  
  
  def has_virtual_fields(self):
      return hasattr(self, '_VIRTUAL_FIELDS')
      
  def __getattr__(self, name):
     if self.has_virtual_fields():
        vf = self._VIRTUAL_FIELDS.get(name) 
        if vf:
           return vf._get_value(self)
     return super(BaseExpando, self).__getattr__(name)
    
  def __setattr__(self, name, value):
      if self.has_virtual_fields():
         vf = self._VIRTUAL_FIELDS.get(name) 
         if vf:
            vf._code_name = name
            self._properties[name] = vf
            vf._set_value(self, value)
            return vf
      return super(BaseExpando, self).__setattr__(name, value)
    
  def __delattr__(self, name):
     if self.has_virtual_fields():
        vf = self._VIRTUAL_FIELDS.get(name) 
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
    
  def _set_value(self, entity, value):
      entity.original_values(self._name)
      return super(_BaseProperty, self)._set_value(entity, value)

class BaseProperty(_BaseProperty, Property):
  """
   Base property class for all properties capable of having writable, and invisible commands
  """
 
class SuperStringProperty(_BaseProperty, StringProperty):
  pass

class SuperIntegerProperty(_BaseProperty, IntegerProperty):
  pass
   
class SuperStateProperty(_BaseProperty, IntegerProperty):
  pass
  
 
class DecimalProperty(StringProperty):
  """Decimal property that accepts only `decimal.Decimal`"""
  
  def _validate(self, value):
    if not isinstance(value, (decimal.Decimal)):
      raise TypeError('expected an decimal, got %s' % repr(value)) # explicitly allow only decimal

  def _to_base_type(self, value):
      return str(value) # Doesn't matter which type, always return in string format

  def _from_base_type(self, value):
      return decimal.Decimal(value)  # Always return a decimal

      
class ReferenceProperty(KeyProperty):
    
  """Replicated property from `db` module"""
    
  def _validate(self, value):
      if not isinstance(value, Model):
         raise TypeError('expected an ndb.Model, got %s' % repr(value))

  def _to_base_type(self, value):
      return value.key

  def _from_base_type(self, value):
      return value.get()
     
     
class SuperReferenceProperty(dict):
  """
    This is a fake property that will `not` be stored in datastore,
     it only represents on what one model can depend. Like so
     
     class UserChildEntity(ndb.BaseModel):
           user = ndb.SuperReferenceProperty(User)
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
     return super(SuperReferenceProperty, self).get(item, default)
  
class _Unexistant():
  """Marks result to be unexisting"""

Unexistant = _Unexistant()

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
            # this is a temporary hack, we need to resolve this thing with __eval__()
            if i == 'state':
              g = self._record._resolve_state_name_by_code(g)
        if not isinstance(g, _Unexistant):
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