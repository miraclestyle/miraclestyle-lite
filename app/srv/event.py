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
  
  def __init__(self, name, formatter, mapper, value=None):
      self.name = name
      self.formatter = formatter
      self.mapper = mapper
      self.value = value
     
 
 
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
      self.args[key] = args.get(key)
    return transaction.Engine.run(context)
 
  
class Engine:
  
  @classmethod
  def run(cls, action_key, args):
    
    action = get_system_action(action_key)
    if not action:
      action = Action.get_local_action(action_key)
    
    if action:
      action.run(args)
      
      

class DescriptiveError(Exception):
      # executes an exception in a way that it will have its own meaning instead of just "invalid"
      pass
 
class Formatter():
 
    @classmethod
    def _value(cls, prop, value):
        if prop._repeated:
           if not isinstance(value, (list, tuple)):
              value = [value]
           out = []   
           for v in value:
               out.append(v)
           return out
        else:
           return value
       
    @classmethod
    def string(cls, prop, value):
        value = cls._value(prop, value)
        if prop._repeated:
           return [unicode(v) for v in value]
        else:
           return unicode(value)
       
    @classmethod   
    def int(cls, prop, value):
        value = cls._value(prop, value)
        if prop._repeated:
           return [long(v) for v in value]
        else:
           return long(value)
       
    @classmethod           
    def ndb_key(cls, prop, value, **kwds):
        value = cls._value(prop, value)
        if prop._repeated:
           returns = [ndb.Key(urlsafe=v) for v in value]
           single = False
        else:
           returns = [ndb.Key(urlsafe=value)]
           single = True
           
        for k in returns:
            if prop._kind and k.kind() != prop._kind:
               raise DescriptiveError('invalid_kind')
        
        items = ndb.get_multi(returns, use_cache=True)
        
        for item in items:
            if item is None:
               raise DescriptiveError('not_found')
            else:
               if hasattr(item, 'is_usable') and kwds.get('skip_usable_check', None) is None:
                  can = item.is_usable
                  if not can:
                     raise DescriptiveError('not_usable')
                 
        if single:
           return returns[0]
        else:
           return returns
 
       
    @classmethod   
    def float(cls, prop, value):
        value = cls._value(prop, value)
        if prop._repeated:
           return [float(v) for v in value]
        else:
           return float(value)
       
    @classmethod   
    def bool(cls, prop, value):
        value = cls._value(prop, value)
        if prop._repeated:
           return [bool(int(v)) for v in value]
        else:
           return bool(int(value))
       
    @classmethod
    def blobfile(cls, prop, value):
        # to validate blob file, it must have fully validated, uploaded blob
        value = cls._value(prop, value)
        if prop._repeated:
           new = []
           for v in value:
               if not isinstance(v, cgi.FieldStorage) or 'blob-key' not in v.type_options:
                  raise ValueError('value provided is not cgi.FieldStorage instance, or its type is not blob-key, or the blob failed to save,\
                   got %r instead.' % v)
               else:
                  v = blobstore.parse_blob_info(v)
               new.append(v.key())
           return new
        else:
           if not isinstance(value, cgi.FieldStorage) or 'blob-key' not in value.type_options:
              raise ValueError('value provided is not cgi.FieldStorage instance, or its type is not blob-key, or the blob failed to save, \
              got %r instead.' % value)
           else:
               value = blobstore.parse_blob_info(value)
           return value.key()
    
    @classmethod
    def decimal(cls, prop, value):
        value = cls._value(prop, value)
        if prop._repeated:
           return [decimal.Decimal(v) for v in value]
        else:
           return decimal.Decimal(value)
       
    @classmethod
    def imagefile(cls, prop, value):
        is_blob = cls.blobfile(prop, value)
        if is_blob:
           single = False
           if not prop._repeated:
              single = True
              value = [value]
           for v in value:
               info = blobstore.parse_file_info(v)
               meta_required = ('image/jpeg', 'image/jpg', 'image/png')
               if info.content_type not in meta_required:
                  raise DescriptiveError('invalid_file_type')
               else:
                   
                  try:
                      BlobManager.field_storage_get_image_sizes(v)
                  except Exception as e:
                      raise DescriptiveError('invalid_image: %s' % e)
           
        return is_blob
 
  
property_types_formatter = {
  'SuperStringProperty' : Formatter.string,
  'SuperIntegerProperty' : Formatter.int,
  'SuperLocalStructuredProperty' : False,
  'SuperStructuredProperty' : False,
  'SuperPickleProperty' : False,
  'SuperTextProperty' : Formatter.string,
  'SuperFloatProperty' : Formatter.float,
  'SuperDateTimeProperty' : False,
  'SuperKeyProperty' : Formatter.ndb_key,
  'SuperBooleanProperty' : Formatter.bool,
  'SuperBlobKeyProperty' : Formatter.blobfile,
  'SuperImageKeyProperty' : Formatter.imagefile,
  'SuperDecimalProperty' : Formatter.decimal,
  'SuperReferenceProperty' : Formatter.ndb_key,
}


   
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
    
    def process_input(self, values, obj, **kwargs):
        
        """
          This method is used to format, and validate the provided input based on the model property definition. 
          Accepts:
          values: dict with unformatted data. note that this data will mutate into the values that are defined by model,
          or the `convert` keyword argument.
          obj: definition of the model from which the properties will be prospected
          **kwargs: skip: skips the processing on specified field names
                    only: only does processing on specified field names
                    convert: converts `values` into specified data type. for example:
                        values = {'catalog' : 'large key...'}
                        response.process_input(values, obj, convert=[ndb.SuperKeyProperty('catalog', kind=Catalog, required=create)])
                        
                        
                        it will convert values['catalog'] into ndb.Key(...) and also perform checks wether the 
                        catalog exists and if its usable
                        
                        note: the third argument in tuple renders if the value will be converted or not if its not present.
                    
          Example:
          
          class Test(ndb.BaseModel):
                name = ndb.SuperStringProperty(required=True)
                number = ndb.SuperIntegerProperty(required=True)     
                
          ....
          
          data = {'name' : 52}
          response.process_input(data, Test)
    
          if the "number" is required will be placed in response:
          
          response['errors'] = {'number' : ['required']}
          ...
          
        """
        
        skip = kwargs.pop('skip', None)
        only = kwargs.pop('only', None)
        convert = kwargs.pop('convert', None)
        create = kwargs.pop('create', True)
        prefix = kwargs.pop('prefix', '')
        fields = dict([(prop._code_name, prop) for prop in obj.get_fields()])
    
        if convert:
           for i in convert:
               if issubclass(i.__class__, ndb.Property):
                  name = i._name
                  value = values.get(i._name, False) 
                  if i._required:
                     if value is False:
                        self.required('%s%s' % (prefix, name))
                     else:
                        formatter = property_types_formatter.get(i.__class__.__name__)
                        if formatter:
                           try: 
                               values[name] = formatter(i, value)
                           except DescriptiveError as e:
                               self.error('%s%s' % (prefix, name), e)         
                           except Exception as e:#-- usually the properties throw these types of exceptions
                               util.logger(e, 'exception')
                               self.invalid('%s%s' % (prefix, name))
                  continue  
  
        for k,v in fields.items():
            
            if skip and k in skip:
               continue
           
            if only is False:
               break
           
            if only:
               if k not in only:
                  continue
                    
            value = values.get(k, False)
            
            if value is False and not create:
               continue
            
            if value == '':
               # if value is empty its considered as `None` 
               value = None
            
            if value is (None or False):
               if v._required:
                  self.required('%s%s' % (prefix, k))
                  
            if value is False and not v._required:
               continue
   
            formatter = property_types_formatter.get(v.__class__.__name__)
            
            if formatter: 
               try: 
                   values[k] = formatter(v, value)
               except DescriptiveError as e:
                   self.error('%s%s' % (prefix, k), e)    
               except Exception as e:#-- usually the properties throw these types of exceptions
                   util.logger(e, 'exception')
                   self.invalid('%s%s' % (prefix, k))
                   
        return values
 
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
        
    
    def group_values(self, start, kwds, **kwargs):
        
        prefix = kwargs.pop('prefix', '')
        only = kwargs.pop('only', None)
         
        values = self.group_by_prefix(prefix, kwds, multiple=True)
        group_values = list()
        
        start = values.get(start)
        
        if start is None:
           return group_values
 
        x = 0
        for i in start:
            new = dict()
            for k in values.keys():
                if only:
                   if k not in only:
                      continue
                  
                o = values.get(k)
                try:
                  o = o[x]
                except IndexError as e:
                  o = None
                new[k] = o
            
            group_values.append(new)
            x += 1
            
        return group_values 
        
    def group_by_prefix(self, prefix, kwds, **kwargs):
        
        multiple = kwargs.pop('multiple', None)
        
        new_dict = dict()
        for i,v in kwds.items():
            if i.startswith(prefix):
               new_key = i[len(prefix):] 
               if multiple:
                  if not isinstance(v, (list, tuple)):
                     v = [v]
               new_dict[new_key] = v
 
        return new_dict  
  
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