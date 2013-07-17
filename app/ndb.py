# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

import decimal
import time

# Google Appengine Datastore
from google.appengine.ext.ndb import *
 
class Model(Model):
    
  saved = False  # class variable provides default value

  @classmethod
  def _post_get_hook(cls, key, future):
    obj = future.get_result()
    if obj is not None:
      # test needed because post_get_hook is called even if get() fails!
      obj.saved = True

  def _post_put_hook(self, future):
    self.saved = True
     
    
class ReferenceProperty(KeyProperty):
    def _validate(self, value):
        if not isinstance(value, Model):
            raise TypeError('expected an ndb.Model, got %s' % repr(value))

    def _to_base_type(self, value):
        return value.key

    def _from_base_type(self, value):
        return value.get()