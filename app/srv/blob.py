# -*- coding: utf-8 -*-
'''
Created on Jan 20, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings


class Image(ndb.BaseModel):
  
  _kind = 69
  
  # Base class / Structured class
  image = ndb.SuperImageKeyProperty('1', required=True, indexed=False)
  content_type = ndb.SuperStringProperty('2', required=True, indexed=False)
  size = ndb.SuperFloatProperty('3', required=True, indexed=False)
  width = ndb.SuperIntegerProperty('4', indexed=False)
  height = ndb.SuperIntegerProperty('5', indexed=False)
  gs_object_name = ndb.SuperStringProperty('6', indexed=False)
  serving_url = ndb.SuperStringProperty('7', indexed=False)
  
  def get_serving_url(self, size):
    if self.serving_url:
      return '%s=s%s' % (self.serving_url, size)
    else:
      return ''
