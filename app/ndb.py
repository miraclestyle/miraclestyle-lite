# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import decimal
import hashlib
 
from google.appengine.ext.ndb import *
 
ctx = get_context()

# memory policy for google app engine ndb calls is set to false, instead we decide per `get` wether to use memcache or not
ctx.set_memcache_policy(False)
 
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
            # this is a temporary hack, we need to resolve this thing with __eval__()
            if i == 'state':
              g = self._record._resolve_state_name_by_code(g)
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