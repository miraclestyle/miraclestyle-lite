# -*- coding: utf-8 -*-
'''
Created on Jan 20, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import cgi
 
from google.appengine.ext import blobstore

from app import ndb, memcache

class Image(ndb.BaseModel):
    
    # base class/structured class
    image = ndb.SuperImageKeyProperty('1', required=True, indexed=False)# blob ce se implementirati na GCS
    content_type = ndb.SuperStringProperty('3', required=True, indexed=False)
    size = ndb.SuperFloatProperty('4', required=True, indexed=False)
    width = ndb.SuperIntegerProperty('5', required=True, indexed=False)
    height = ndb.SuperIntegerProperty('6', required=True, indexed=False)
    sequence = ndb.SuperIntegerProperty('7', required=True)

class Manager():
    
    """
    This class handles deletations of blobs trough the application. This approach needs to be like this,
    because ndb does not support some of the blobstore query functions.
   
    """
    
    _UNUSED_BLOB_KEY = '_unused_blob_key'
  
    @classmethod
    def parse_blob_keys(cls, field_storages):
        
        if not isinstance(field_storages, (list, tuple)):
            field_storages = [field_storages]
        
        out = []       
        for i in field_storages:
            
            if isinstance(i, blobstore.BlobKey):
                out.append(i)
                continue
            
            if isinstance(i, cgi.FieldStorage):
                try:
                    blobinfo = blobstore.parse_blob_info(i)
                    out.append(blobinfo.key())
                except blobstore.BlobInfoParseError as e:
                    pass
        return out
  
    @classmethod
    def get_unused_blobs(cls):
        return memcache.temp_memory_get(cls._UNUSED_BLOB_KEY, [])
      
    @classmethod
    def used_blobs(cls, blob_keys):
      
        unused_blobs = cls.get_unused_blobs()
        
        if not isinstance(blob_keys, (list, tuple)):
           blob_keys = [blob_keys]
        
        for blob_key in blob_keys:
          if blob_key in unused_blobs:
             unused_blobs.remove(blob_key)
           
        return unused_blobs
    
    @classmethod
    def field_storage_used_blobs(cls, field_storages):
        
        unused_blobs = cls.get_unused_blobs()
        
        removes = cls.parse_blob_keys(field_storages)
        
        for remove in removes:
            unused_blobs.remove(remove)
            
        memcache.temp_memory_set(cls._UNUSED_BLOB_KEY, unused_blobs)
 
    @classmethod
    def field_storage_unused_blobs(cls, field_storages):
  
        unused_blobs = cls.get_unused_blobs()
        
        unused_blobs.extend(cls.parse_blob_keys(field_storages))
        
        memcache.temp_memory_set(cls._UNUSED_BLOB_KEY, unused_blobs)
  
    
    @classmethod
    def delete_unused_blobs(cls):
        
        k = cls._UNUSED_BLOB_KEY
     
        unused_blobs = cls.get_unused_blobs()
 
        if len(unused_blobs):
           blobstore.delete(unused_blobs)
           memcache.temp_memory_set(k, [])
           