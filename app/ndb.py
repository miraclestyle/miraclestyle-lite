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

class BaseModel(Model):
  
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
    entity = super(BaseModel, cls)._from_pb(*args, **kwargs)
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