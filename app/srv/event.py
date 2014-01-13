# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import cgi
import cloudstorage
import decimal

from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.ext.db import datastore_errors

from app import ndb, memcache, util
from app.srv import log, rule, transaction, auth
 
__SYSTEM_ACTIONS = {}

def get_system_action(action_key):
    global __SYSTEM_ACTIONS
    
    action_key = ndb.Key(Action, action_key)
    
    return __SYSTEM_ACTIONS.get(action_key.urlasfe())
 
  
def register_system_action(*args):
    global __SYSTEM_ACTIONS
    
    for action in args:
        __SYSTEM_ACTIONS[action.key.urlsafe()] = action
 
class Context():
  
  def __init__(self):
 
    self.event = None
    self.transaction = transaction.Context()
    self.rule = rule.Context()
  
    self.log = log.Context()
    self.auth = auth.Context()
    self.response = None
    
    
class Argument():
  
  def __init__(self, name, prop, mapper):
      self.name = name
      self.prop = prop
      self.mapper = mapper
 
 
 
class Action(ndb.BaseExpando):
  
  KIND_ID = 56
  
  # root (namespace Domain)
  # key.id() = code.code
  
  name = ndb.SuperStringProperty('1', required=True)
  arguments = ndb.SuperPickleProperty('2') # dict
  active = ndb.SuperBooleanProperty('3', default=True)
  operation = ndb.SuperStringProperty('4')
  
  @classmethod
  def get_local_action(cls, action_key):
      action = ndb.Key(urlsafe=action_key).get()
      if action.active:
         return action
      else:
         return None
 
  def run(self, args):
    context = Context()
    context.event = self
    self.args = {}
    for key in self.arguments:
      value = args.get(key)
      argument = self.arguments.get(key)
      if argument.prop and hasattr(argument.prop, 'format'):
         value = argument.prop.format(value)
      self.args[key] = value
    return transaction.Engine.run(context)
 
  
class Engine:
  
  @classmethod
  def run(cls, action_key, args):
    
    action = get_system_action(action_key)
    if not action:
      action = Action.get_local_action(action_key)
    
    if action:
      action.run(args)
      
      
class Response(dict):
    
    """ 
      This response class is the main interface trough which the CLIENT will communicate between the model methods.
      Each method that is capable of performing operations that will need some kind of answer need to return instance of 
      this class. Such example
      
      class Example(ndb.BaseModel):
      
            name ... 
            
            def perform_operation(cls, **kwds):
                response = ndb.Response()
                
                if not kwds.get('name'):
                   response.required('name')
                   
                if not response.has_error():
                   ... put() operations etc
                
                return response   
                 
      Each of those class methods must return `response` and the response will be interpreted by the client:
      e.g. JSON.
                
    """
    def transaction_error(self, e):
        """
        This function needs to be used in fashion:
        
        @ndb.transacitonal
        def transaction():
            user.put()
            ...
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        It will automatically set if the transaction failed because of google network.
        
        """
        if isinstance(e, datastore_errors.Timeout):
           return self.transaction_timeout()
        if isinstance(e, datastore_errors.TransactionFailedError):
           return self.transaction_failed()
        
        raise
    
    def not_implemented(self):
        return self.error('system', 'not_implemented')
 
    def transaction_timeout(self):
        # sets error in the response that the transaction that was taking place has timed out
        return self.error('transaction_error', 'timeout')
    
    def transaction_failed(self):
        # sets error in the response that the transaction that was taking place has failed
        return self.error('transaction_error', 'failed')
    
    def required(self, k):
        # sets error that the field is required with name `k`
        return self.error(k, 'required')
        
    def invalid(self, k):
        # sets error that the field is not in proper format with name `k`
        return self.error(k, 'invalid_input')
    
    def status(self, m):
        # generic `status` of the response. 
        self['status'] = m
        return self
    
    def not_found(self):
        # shorthand for informing the response that the entity, object, thing or other cannot be found with the provided params
        self.error('status', 'not_found')
        return self
    
    def not_authorized(self):
        # shorthand for informing the response that the user is not authorize to perform the operation
        return self.error('user', 'not_authorized')
        
    def not_logged_in(self):
        # shorthand for informing the response that the user needs to login in order to perform the operation
        return self.error('user', 'not_logged_in')
    
    def __setattr__(self, *args, **kwargs):
        return dict.__setitem__(self, *args, **kwargs)
    
    def __getattr__(self, *args, **kwargs):
        return dict.__getitem__(self, *args, **kwargs)
 
    def has_error(self, k=None):
        
        if self['errors'] is None:
              return False
        
        if k is None:
           return len(self['errors'].keys())
        else:
           return len(self['errors'][k])
    
    def error(self, f, m):
        
        if self['errors'] == None:
           self['errors'] = {}
           
        if f not in self['errors']:
            self['errors'][f] = list()
            
        self['errors'][f].append(m)
        return self
    
    def __init__(self):
        self['errors'] = None
  
class BlobManager():
    
    """
    This class handles deletations of blobs trough the application. This approach needs to be like this,
    because ndb does not support some of the blobstore query functions.
   
    """
    
    _UNUSED_BLOB_KEY = '_unused_blob_key'
  
    @classmethod
    def blob_keys_from_field_storage(cls, field_storages):
        
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
    def unused_blobs(cls):
        return memcache.temp_memory_get(cls._UNUSED_BLOB_KEY, [])
    
    @classmethod
    def field_storage_used_blob(cls, field_storages):
        
        gets = cls.unused_blobs()
        
        removes = cls.blob_keys_from_field_storage(field_storages)
        
        for remove in removes:
            gets.remove(remove)
            
        memcache.temp_memory_set(cls._UNUSED_BLOB_KEY, gets)
 
    @classmethod
    def field_storage_unused_blob(cls, field_storages):
  
        gets = cls.unused_blobs()
        
        gets.extend(cls.blob_keys_from_field_storage(field_storages))
        
        memcache.temp_memory_set(cls._UNUSED_BLOB_KEY, gets)
  
    
    @classmethod
    def delete_unused_blobs(cls):
        
        k = cls._UNUSED_BLOB_KEY
     
        deletes = cls.unused_blobs()
 
        if len(deletes):
           blobstore.delete(deletes)
 
           memcache.temp_memory_set(k, [])
 
    @classmethod
    def field_storage_get_image_sizes(cls, field_storages):
         
        @ndb.non_transactional
        def operation(field_storages):
            
            sizes = dict()
            single = False
            
            if not isinstance(field_storages, (list, tuple)):
               field_storages = [field_storages]
               single = True
               
            out = []
               
            for field_storage in field_storages:
                
                fileinfo = blobstore.parse_file_info(field_storage)
                blobinfo = blobstore.parse_blob_info(field_storage)
                
                sizes = {}
      
                f = cloudstorage.open(fileinfo.gs_object_name[3:])
                blob = f.read()
        
                image = images.Image(image_data=blob)
                sizes = {}
           
                sizes['width'] = image.width
                sizes['height'] = image.height
                 
                sizes['size'] = fileinfo.size
                sizes['content_type'] = fileinfo.content_type
                sizes['image'] = blobinfo.key()
         
                if not single:
                   out.append(sizes)
                else:
                   out = sizes
                 
                # free buffer memory   
                f.close()
                
                del blob
                  
            return out
        
        return operation(field_storages)
      
def prepare_create(cls, dataset, **kwds):
      return cls.prepare(True, dataset, **kwds)
  
def prepare_update(cls, dataset, **kwds):
      return cls.prepare(False, dataset, **kwds)
 
def prepare(cls, create, dataset, **kwds):
      
      use_get = kwds.pop('use_get', True)
      get_only = kwds.pop('get_only', False)
      expect = kwds.pop('only', [prop._code_name for prop in cls.get_fields()] + ['id'])
      skip = kwds.pop('skip', None)
      ctx_options = kwds.pop('ctx_options', {})
      populate = kwds.pop('populate', True)
      
      if get_only:
         expect = False
         populate = False
      
      datasets = dict()
      
      _id = dataset.pop('key', None)
      
      if not create:
         if not _id:
            return None
         try:
             load = Key(urlsafe=_id)
         except:
             return None
         
      if expect is not False:   
          for i in expect:
              
              if skip is not None and isinstance(skip, (tuple, list)):
                 if i in skip:
                     continue
            
              if i in dataset:
                 datasets[i] = dataset.get(i)
              else:
                 gets = getattr(cls, 'default_%s' % i, None)
                 if gets is not None:
                    datasets[i] = gets()
      else:
          datasets = dataset.copy()
      
      if create:
         datasets.update(kwds)
     
      if create:
         return cls(**datasets)
      else:
         if use_get:
            entity = load.get(**ctx_options)
            if populate:
               entity.populate(**datasets)
            return entity
         else:
            datasets['key'] = load 
            return cls(**datasets)
  