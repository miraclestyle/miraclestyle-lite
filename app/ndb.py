# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

import decimal
import hashlib
import logging

from app import settings
from app.memcache import smart_cache

# Google Appengine Datastore
from google.appengine.ext.ndb import *

contx = get_context()

contx.set_memcache_policy(False)
 
class _BaseModel:
    
  _KIND = -1  
    
  def _memcache_key(self):
      # memcache generator for this model
      return self._return_memcache_key(self.key.id())
  
  _memcache_key = _memcache_key
   
  def _self_clear_memcache(self):
      self._clear_memcache(self.key.id())
      
  def _self_make_memory(self, structure=None, include_self=None):
      if structure == None:
         structure = {}
      
      if include_self != None:   
         structure['self'] = self
      
      self._make_memory(self.key, structure)
       
  def _self_from_memory(self, segment=None, empty=None):
      return self._get_from_memory(self.key.id(), segment, empty)    
  
  @classmethod
  def hash_create_key(cls, **kwargs):
      _data = [settings.SALT]
      for k in kwargs:
          _data.append(unicode(kwargs.get(k)))
      hashed = str(hashlib.md5(settings.HASH_BINDER.join(_data)).hexdigest())
      if settings.DEBUG and settings.DO_LOGS:
         logging.info('get by hash: %s' % hashed)    
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
   
    if cls.__name__ not in ('BaseModel', 'BaseExpando'):
       if cls._KIND < 0:
          raise TypeError('Invalid _KIND ID') 
    return str(cls._KIND)

  # helper memcache tools
  
  @classmethod
  def _return_memcache_key(cls, kid):
      return str('mc-%s-%s' % (cls._get_kind(), kid))
   
  @classmethod
  def _clear_memcache(cls, kid):
      smart_cache.delete(cls._return_memcache_key(kid))
  
  @classmethod
  def _make_memory(cls, user, structure, expire=0):
      if not isinstance(structure, dict):
         raise Exception('_make_memory allows only dicts as values')
      smart_cache.set(cls._return_memcache_key(user.id()), structure, expire)
  
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
      gets = smart_cache.get(cls._return_memcache_key(kid), empty)
      if gets and empty != gets:
         if segment:
            return gets.get(segment, empty) 
         return gets
      return empty

class BaseModel(_BaseModel, Model):
    pass

class BaseExpando(_BaseModel, Expando):
    
    def set_virtual_field(self, value, alias, prop):
        prop._code_name = alias
        self._properties[alias] = prop
        prop._set_value(self, value)
        return self
 
class DecimalProperty(StringProperty):
  def _validate(self, value):
    if not isinstance(value, (decimal.Decimal)):
      raise TypeError('expected an decimal, got %s' % repr(value))

  def _to_base_type(self, value):
    return str(value) # Doesn't matter if it's an int or a long

  def _from_base_type(self, value):
    return decimal.Decimal(value)  # Always return a long  
     
    
class ReferenceProperty(KeyProperty):
    def _validate(self, value):
        if not isinstance(value, Model):
            raise TypeError('expected an ndb.Model, got %s' % repr(value))

    def _to_base_type(self, value):
        return value.key

    def _from_base_type(self, value):
        return value.get()