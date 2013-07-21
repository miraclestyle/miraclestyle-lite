# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

import decimal
import time
import hashlib

# Google Appengine Datastore
from google.appengine.ext.ndb import *
 
class BaseModel(Model):
    
  saved = False  # class variable provides default value

  @classmethod
  def _post_get_hook(cls, key, future):
    obj = future.get_result()
    if obj is not None:
      # test needed because post_get_hook is called even if get() fails!
      obj.saved = True

  def _post_put_hook(self, future):
    self.saved = True
    
  @classmethod
  def md5_create_key(cls, **kwargs):
      _data = []
      for k in kwargs:
          _data.append(unicode(kwargs.get(k)))
      # treba utvrditi koji separator ide za ovo md5 keyovanje    
      return hashlib.md5(u"-".join(_data)).hexdigest()
  
  @classmethod
  def md5_get_by_id(cls, **kwargs):
      return cls.get_by_id(cls.md5_create_key(**kwargs))
  
  
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