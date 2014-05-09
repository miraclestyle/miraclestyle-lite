# -*- coding: utf-8 -*-
'''
Created on Jan 20, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import cgi

from google.appengine.ext import blobstore

from app import ndb, memcache, util


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


class Manager():
  """This class handles deletions of blobs through the application.
  This solution is required because ndb does not support some of the blobstore query functions.
  
  """
  _UNUSED_BLOB_KEY = '_unused_blob_key'
  
  @classmethod
  def parse_blob_keys(cls, field_storages):
    if not isinstance(field_storages, (list, tuple)):
      field_storages = [field_storages]
    blob_keys = []
    for field_storage in field_storages:
      if isinstance(field_storage, blobstore.BlobKey):
        blob_keys.append(field_storage)
        continue
      
      if isinstance(field_storage, cgi.FieldStorage):
        try:
          blob_info = blobstore.parse_blob_info(field_storage)
          blob_keys.append(blob_info.key())
        except blobstore.BlobInfoParseError as e:
          pass
    return blob_keys
  
  @classmethod
  def get_unused_blobs(cls):
    return memcache.temp_memory_get(cls._UNUSED_BLOB_KEY, [])
  
  @classmethod
  def unused_blobs(cls, blob_keys):
    """Marks a key or a list of keys for deletation"""
    return cls.field_storage_unused_blobs(blob_keys)
  
  @classmethod
  def used_blobs(cls, blob_keys):
    """Marks a key or a list of keys to not be deleted"""
    unused_blob_keys = cls.get_unused_blobs()
    if not isinstance(blob_keys, (list, tuple)):
      blob_keys = [blob_keys]
    for blob_key in blob_keys:
      if blob_key in unused_blob_keys:
        unused_blob_keys.remove(blob_key)
    return unused_blob_keys
  
  @classmethod
  def field_storage_used_blobs(cls, field_storages):
    """Internal helper for structured properties that handle uploads"""
    unused_blob_keys = cls.get_unused_blobs()
    blob_keys = cls.parse_blob_keys(field_storages)
    for blob_key in blob_keys:
      unused_blob_keys.remove(blob_key)
    memcache.temp_memory_set(cls._UNUSED_BLOB_KEY, unused_blob_keys)
  
  @classmethod
  def field_storage_unused_blobs(cls, field_storages):
    """Internal helper for structured properties that handle uploads"""
    unused_blob_keys = cls.get_unused_blobs()
    unused_blob_keys.extend(cls.parse_blob_keys(field_storages))
    memcache.temp_memory_set(cls._UNUSED_BLOB_KEY, unused_blob_keys)
  
  @classmethod
  def delete_unused_blobs(cls):
    """This functon must be always called last in the application execution."""
    unused_blob_keys = cls.get_unused_blobs()
    if len(unused_blob_keys):
      util.logger('DELETED BLOBS: %s' % len(unused_blob_keys))
      blobstore.delete(unused_blob_keys)
      memcache.temp_memory_set(cls._UNUSED_BLOB_KEY, [])
