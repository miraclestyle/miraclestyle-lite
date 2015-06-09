# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import cgi
import cloudstorage
import copy
from urlparse import urlparse

from google.appengine.ext import blobstore
from google.appengine.api import images, urlfetch
from google.appengine.datastore.datastore_query import Cursor

import orm, mem, settings
from util import *


__all__ = ['Role', 'GlobalRole', 'Image']


# @see https://developers.google.com/appengine/docs/python/googlecloudstorageclient/retryparams_class
default_retry_params = cloudstorage.RetryParams(initial_delay=0.2, max_delay=5.0, backoff_factor=2,
                                                max_retries=5, max_retry_period=60, urlfetch_timeout=30)
cloudstorage.set_default_retry_params(default_retry_params)


##########################################
########## Extra system models! ##########
##########################################


class Role(orm.BaseExpando):
  
  _kind = 6
  
  # feature proposition (though it should create overhead due to the required drilldown process!)
  # parent_record = orm.SuperKeyProperty('1', kind='Role', indexed=False)
  # complete_name = orm.SuperTextProperty('2')
  name = orm.SuperStringProperty('1', required=True)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  permissions = orm.SuperPickleProperty('3', required=True, default=[], compressed=False) # List of Permissions instances. Validation is required against objects in this list, if it is going to be stored in datastore.
  
  _default_indexed = False


class GlobalRole(Role):
  
  _kind = 7


class Image(orm.BaseExpando):
  
  _kind = 8
  
  image = orm.SuperBlobKeyProperty('1', required=True, indexed=False)
  content_type = orm.SuperStringProperty('2', required=True, indexed=False)
  size = orm.SuperFloatProperty('3', required=True, indexed=False)
  gs_object_name = orm.SuperStringProperty('4', required=True, indexed=False)
  serving_url = orm.SuperStringProperty('5', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'proportion': orm.SuperFloatProperty('6')
    }