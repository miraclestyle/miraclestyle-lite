# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import cgi

from google.appengine.ext import blobstore

from app import ndb, settings, memcache, util
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


_UNUSED_BLOB_KEY = '_unused_blob_key'


def parse_blob_keys(field_storages):
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

def get_unused_blobs():
  return memcache.temp_memory_get(_UNUSED_BLOB_KEY, [])

def unused_blobs(blob_keys):
  """Marks a key or a list of keys for deletation"""
  return field_storage_unused_blobs(blob_keys)

def field_storage_used_blobs(field_storages):
  """Internal helper for structured properties that handle uploads"""
  unused_blob_keys = get_unused_blobs()
  blob_keys = parse_blob_keys(field_storages)
  for blob_key in blob_keys:
    unused_blob_keys.remove(blob_key)
  memcache.temp_memory_set(_UNUSED_BLOB_KEY, unused_blob_keys)

def field_storage_unused_blobs(field_storages):
  """Internal helper for structured properties that handle uploads"""
  unused_blob_keys = get_unused_blobs()
  unused_blob_keys.extend(parse_blob_keys(field_storages))
  memcache.temp_memory_set(_UNUSED_BLOB_KEY, unused_blob_keys)

def delete_unused_blobs():
  """This functon must be always called last in the application execution."""
  unused_blob_keys = get_unused_blobs()
  if len(unused_blob_keys):
    util.logger('DELETED BLOBS: %s' % len(unused_blob_keys))
    blobstore.delete(unused_blob_keys)
    memcache.temp_memory_set(_UNUSED_BLOB_KEY, [])


class UploadURL(event.Plugin):
  
  gs_bucket_name = ndb.SuperStringProperty('5', required=True, indexed=False)
  
  def run(self, context):
    upload_url = context.input.get('upload_url')
    if upload_url:
      context.output['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=self.gs_bucket_name)
      raise event.TerminateAction()


class UsedBlobs(event.Plugin):
  
  blob_keys_location = ndb.SuperJsonProperty('5', indexed=False, required=True, default={})
  
  def run(self, context):
    """Marks a key or a list of keys to not be deleted"""
    blob_keys = get_attr(context, self.blob_keys_location)
    if blob_keys:
      unused_blob_keys = get_unused_blobs()
      if not isinstance(blob_keys, (list, tuple)):
        blob_keys = [blob_keys]
      for blob_key in blob_keys:
        if blob_key in unused_blob_keys:
          unused_blob_keys.remove(blob_key)
      return unused_blob_keys
