# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

import decimal
import hashlib
from app import settings

# Google Appengine Datastore
from google.appengine.ext.ndb import *
 
class _BaseModel:
  
  @classmethod
  def md5_create_key(cls, **kwargs):
      _data = [settings.SALT]
      for k in kwargs:
          _data.append(unicode(kwargs.get(k)))
      return hashlib.md5(settings.HASH_BINDER.join(_data)).hexdigest()
  
  @classmethod
  def md5_get_by_id(cls, **kwargs):
      return cls.get_by_id(cls.md5_create_key(**kwargs))
  
  @classmethod
  def md5_get_by_id_async(cls, **kwargs):
      return cls.get_by_id_async(cls.md5_create_key(**kwargs))
  
  @classmethod
  def _get_kind(cls):
    """Return the kind name for this class.

    This defaults to cls.__name__; users may overrid this to give a
    class a different on-disk name than its class name.
    """
    
    if not settings.DATASTORE_KINDS:
       return cls.__name__
    
    # this may cause KeyError if we havent defined model inside settings - this is to prevent bad kind names
    return str(settings.DATASTORE_KINDS[cls.__name__])

class BaseModel(_BaseModel, Model):
    pass

class BaseExpando(_BaseModel, Expando):
    pass
 
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