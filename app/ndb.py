# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import cgi
import decimal
import cloudstorage

from google.appengine.api import images
from google.appengine.ext.db import datastore_errors
from google.appengine.ext import blobstore

from google.appengine.ext.ndb import *
 
from app import pyson, util, memcache
 
ctx = get_context()

# memory policy for google app engine ndb calls is set to false, instead we decide per `get` wether to use memcache or not
ctx.set_memcache_policy(False)
#ctx.set_cache_policy(False)

# We always put double underscore for our private functions in order to avoid ndb library from clashing with our code
# see https://groups.google.com/d/msg/appengine-ndb-discuss/iSVBG29MAbY/a54rawIy5DUJ

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
           returns = [Key(urlsafe=v) for v in value]
           single = False
        else:
           returns = [Key(urlsafe=value)]
           single = True
           
        for k in returns:
            if prop._kind and k.kind() != prop._kind:
               raise DescriptiveError('invalid_kind')
        
        items = get_multi(returns, use_cache=True)
        
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

def make_complete_name(entity, property_name, parent=None, separator=None):
    
    if separator is None:
       separator = unicode(' / ')
       
    gets_entity = entity
    names = []
    while True:
        
        if parent is None:
           parents = gets_entity.key.parent() 
           parents = parents.get()
        else:
           parents = getattr(gets_entity, parent)
           if parents:
              parents = parents.get()
 
        if not parents:
           names.append(getattr(gets_entity, property_name))
           break
        else:
           value = getattr(gets_entity, property_name)
           names.append(value)
           gets_entity = parents
 
    names.reverse()
    return separator.join(names)
           

def get_current_user():
    
    from app.core.acl import User
    return User.current_user()

def factory(module_model_path):
    """
     Retrieves model by its module path. e.g.
     model = factory('app.core.misc.Country')
     
     `model` will be a Country class.
     
    """
    custom_kinds = module_model_path.split('.')
    far = custom_kinds[-1] 
    del custom_kinds[-1] 
         
    return getattr(util.import_module(".".join(custom_kinds)), far)


def format_permission(action, obj):
    """ Formats the permission in format <kind>-<action> """
    return '%s-%s' % (obj._get_kind(), obj.resolve_action_code_by_name(action))
     
def compile_permissions(*args):
    """ Accepts list of models from which it will compile a list of permissions, based on 'public' and 'admin' param. """
    args = list(args)
    _type = args[0]
    del args[0]
    models = args
    
    out = []
    
    for model in models:
        perms = []
        if _type == 'public':
           if hasattr(model, 'generate_public_permissions'): 
              perms = model.generate_public_permissions()
        else:
           if hasattr(model, 'generate_admin_permissions'):  
              perms = model.generate_admin_permissions()
        
        for perm in perms:
            out.append(format_permission(perm, model))
    return out
    

def compile_public_permissions(*args):
    return compile_permissions('public', *args)

def compile_admin_permissions(*args):
    return compile_permissions('admin', *args)
  
  
class _BaseModel(Model):
 
  __tmp = {} #-- this property is used to store all values that will live inside one entity instance.
  
  def __init__(self, *args, **kwds):
      self.__tmp = {}
      self.register_tmp('original_values', {})
      
      super(_BaseModel, self).__init__(*args, **kwds)
      
  def set_key(self, **kwargs):
      self._key = Key(self._get_kind(), **kwargs)
      return self._key
  
  def __todict__(self):
      """
        This function can be used to make representation of the model into the dictionary.
        The dictionary can be then used to be translated into other understandable code to clients, e.g. JSON
        
        Currently, this method calls native Model.to_dict() method which converts the values into dictionary format.
      """
      dic = self.to_dict()
      
      if self.key:
         dic['id'] = self.key.urlsafe()
         
      for k,v in dic.items():
          if isinstance(v, Key):
             dic[k] = v.urlsafe()
         
      return dic
   
   
  def set_tmp(self, k, v):
      if k not in self.__tmp:
         raise Exception('%s key was not registered inside temp' % k)
      else:
        self.__tmp[k] = v
 
  def register_tmp(self, k, v=None):
      """
         Registers a variable by key
      """
      if k not in self.__tmp:
         if v is None:
             return None
         else:
             self.__tmp[k] = v
        
         
      return self.__tmp[k]
 
  
  def loaded(self):
      return self.key != None and self.key.id()
  
  @classmethod
  def prepare_create(cls, dataset, **kwds):
      return cls.prepare(True, dataset, **kwds)
  
  @classmethod
  def prepare_update(cls, dataset, **kwds):
      return cls.prepare(False, dataset, **kwds)
 
  @classmethod
  def prepare(cls, create, dataset, **kwds):
      
      use_get = kwds.pop('use_get', True)
      get_only = kwds.pop('get_only', False)
      expect = kwds.pop('only', cls.get_property_names() + ['id'])
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
  
  def _pre_put_hook(self):
      for p in self._properties:
          prop = self._properties.get(p)
          if prop._get_value(self) is None:
             cb = 'default_%s' % p
             if hasattr(self, cb):
                prop._set_value(self, getattr(self, cb)())
             
          if prop and hasattr(prop, '_writable') and prop._writable:
             self.__resolve_writable(prop)
 
  def __resolve_writable(self, prop):
      if isinstance(prop._writable, pyson.PYSON):
         environ = EvalEnvironment(self)
         encoded = pyson.PYSONEncoder(environ).encode(prop._writable)
         check = pyson.PYSONDecoder(environ).decode(encoded)
         if not check:
            # if the evaluation is not true, set the original values because new value is not allowed to be set
            prop._set_value(self, self.register_tmp('original_values').get(prop._name))
    
  def set_original_values(self):
      pack = dict()
      for p in self._properties:
          pack[p] = self._properties[p]._get_value(self)
      self.set_tmp('original_values', pack)
 
  @classmethod
  def _get_kind(cls):
    """Return the kind name for this class.

    This defaults to cls.__name__; users may overrid this to give a
    class a different on-disk name than its class name.
    """
    if hasattr(cls, 'KIND_ID'):
       if cls.KIND_ID < 0:
          raise TypeError('Invalid KIND_ID %s, for %s' % (cls.KIND_ID, cls.__name__)) 
       return str(cls.KIND_ID)
    return cls.__name__

  @classmethod
  def get_all_properties(cls):
      out = []
      for prop_key,prop in cls._properties.items():
          out.append(prop)
          
      if hasattr(cls, 'has_expando_fields'):
         expandos = cls.has_expando_fields()
         if expandos: 
             for prop_key,prop in expandos.items():
                 out.append(prop)
      return out
  
  @classmethod
  def get_mapped_properties(cls):
      return dict([(prop._code_name, prop) for prop in cls.get_all_properties()])
 
  @classmethod
  def get_property_names(cls):
      return [prop._code_name for prop in cls.get_all_properties()]
 
  @classmethod
  def create(cls, values, **kwargs):
        if not hasattr(cls, 'manage'):
           response = Response()
           return response.not_implemented()
        return cls.manage(True, values, **kwargs)
    
  @classmethod
  def update(cls, values, **kwargs):
        if not hasattr(cls, 'manage'):
           response = Response()
           return response.not_implemented()
        return cls.manage(False, values, **kwargs)
 
class BaseModel(_BaseModel):
    """
      Base class for all `ndb.Model` entities
    """
    @classmethod
    def _from_pb(cls, *args, **kwargs):
        """ Allows for model to get original values who get loaded from the protocol buffer  """
        entity = super(_BaseModel, cls)._from_pb(*args, **kwargs)
        entity.set_original_values()
        return entity
 
  
class BaseExpando(_BaseModel, Expando):
    """
     Base class for all `ndb.Expando` entities
    """
  
    @classmethod
    def _from_pb(cls, *args, **kwargs):
        """ Allows for model to get original values who get loaded from the protocol buffer  """
        entity = super(BaseExpando, cls)._from_pb(*args, **kwargs)
        entity.set_original_values()
        return entity
  
    @classmethod
    def has_expando_fields(cls):
        if hasattr(cls, 'EXPANDO_FIELDS'):
           for i,v in cls.EXPANDO_FIELDS.items():
               if not v._code_name:
                  v._code_name = i 
                  cls.EXPANDO_FIELDS[i] = v
                   
           return cls.EXPANDO_FIELDS
        else:
           return False
        
    def __getattr__(self, name):
       ex = self.has_expando_fields()
       if ex:
          vf = ex.get(name) 
          if vf:
             return vf._get_value(self)
       return super(BaseExpando, self).__getattr__(name)
      
    def __setattr__(self, name, value):
        ex = self.has_expando_fields()
        if ex:
           vf = ex.get(name) 
           if vf:
              self._properties[vf._name] = vf
              vf._set_value(self, value)
              return vf
        return super(BaseExpando, self).__setattr__(name, value)
      
    def __delattr__(self, name):
       ex = self.has_expando_fields()
       if ex:
          vf = ex.get(name) 
          if vf:
             vf._delete_value(self)
             pname = vf._name
             if vf in self.__class__._properties:
                 raise RuntimeError('Property %s still in the list of properties for the '
                                       'base class.' % name)
             del self._properties[pname]
       return super(BaseExpando, self).__delattr__(name)
   
    def _get_property_for(self, p, indexed=True, depth=0):
        """Internal helper to get the Property for a protobuf-level property."""
        name = p.name()
        parts = name.split('.')
        if len(parts) <= depth:
          # Apparently there's an unstructured value here.
          # Assume it is a None written for a missing value.
          # (It could also be that a schema change turned an unstructured
          # value into a structured one.  In that case, too, it seems
          # better to return None than to return an unstructured value,
          # since the latter doesn't match the current schema.)
          return None
        next = parts[depth]
    
        prop = self._properties.get(next)
        if prop is None:
           expando = self.has_expando_fields()
           if expando:
              for k,v in expando.items():
                  if v._name == next:
                     prop = v
                     self._properties[v._name] = v
                     break        
  
        if prop is None:
          prop = self._fake_property(p, next, indexed)
        return prop

class _BaseProperty(object):
    
    _writable = False
    _visible = False
    _max_size = False
 
    def __init__(self, *args, **kwds):
        self._writable = kwds.pop('writable', self._writable)
        self._visible = kwds.pop('visible', self._visible)
        self._max_size = kwds.pop('max_size', self._max_size)
         
        custom_kind = kwds.get('kind')
  
        if custom_kind and isinstance(custom_kind, basestring) and '.' in custom_kind:
           kwds['kind'] = factory(custom_kind)
            
        super(_BaseProperty, self).__init__(*args, **kwds)

class BaseProperty(_BaseProperty, Property):
   """
    Base property class for all properties capable of having writable, and visible options
   """
   
class SuperLocalStructuredProperty(_BaseProperty, LocalStructuredProperty):
    pass
  
class SuperStructuredProperty(_BaseProperty, StructuredProperty):
    pass
    
class SuperPickleProperty(_BaseProperty, PickleProperty):
    pass

class SuperTextProperty(_BaseProperty, TextProperty):
    pass
 
class SuperStringProperty(_BaseProperty, StringProperty):
    pass

class SuperFloatProperty(_BaseProperty, FloatProperty):
    pass

class SuperIntegerProperty(_BaseProperty, IntegerProperty):
    pass

class SuperDateTimeProperty(_BaseProperty, DateTimeProperty):
    pass

class SuperKeyProperty(_BaseProperty, KeyProperty):
    pass

class SuperBooleanProperty(_BaseProperty, BooleanProperty):
    pass

class SuperBlobKeyProperty(_BaseProperty, BlobKeyProperty):
    pass

class SuperImageKeyProperty(_BaseProperty, BlobKeyProperty):
    pass

class SuperJsonProperty(_BaseProperty, JsonProperty):
    pass
  
class SuperDecimalProperty(SuperStringProperty):
    
    """Decimal property that accepts only `decimal.Decimal`"""
    
    def _validate(self, value):
      if not isinstance(value, (decimal.Decimal)):
        raise TypeError('expected an decimal, got %s' % repr(value)) # explicitly allow only decimal
    
    def _to_base_type(self, value):
        return str(value) # Doesn't matter which type, always return in string format
    
    def _from_base_type(self, value):
        return decimal.Decimal(value)  # Always return a decimal
    
    """

    def _db_set_value(self, v, unused_p, value):
        value = str(value)
        return super(SuperDecimalProperty, self)._db_set_value(v, unused_p, value)
    
    def _db_get_value(self, v, unused_p):
        return decimal.Decimal(v.stringvalue())
        
    """    
 
      
class SuperReferenceProperty(SuperKeyProperty):
    
    """Replicated property from `db` module"""
      
    def _validate(self, value):
        if not isinstance(value, Model):
           raise TypeError('expected an ndb.Model, got %s' % repr(value))
    
    def _to_base_type(self, value):
        return value.key
    
    def _from_base_type(self, value):
        return value.get()
    
class SuperImageGCSProperty(SuperJsonProperty):
 
    def _validate(self, value):
        if not hasattr(value, 'read'):
           raise TypeError('expected an file-like object, got %s' % repr(value))
 
    def _to_base_type(self, value):
        return value.key
    
    def _from_base_type(self, value):
        return value.get()
    
     
class SuperRelationProperty(dict):
    
    """ 
      !!This property is not yet tested and yet to be decided whether should be used anyway!
 
      This is a fake property that will `not` be stored in datastore,
       it only represents on what one model can depend. Like so
       
       class UserChildEntity(ndb.BaseModel):
             user = ndb.SuperRelationProperty(User)
             name = ndb.StringProperty(required=True, writable=Eval('user.state') != 'active')
             
       foo = UserChildEntity(name='Edward', user=ndb.Key('User', 'foo').get())
       foo.save()     
       
       The `Eval` will evaluate: self.user.state != 'active' and therefore the property
       will validate itself to be read only
       
       This property only accepts model that needs validation, otherwise it will accept any value provided
    """
    
    def __get__(self, entity):
        """Descriptor protocol: get the value on the entity."""
        return self.model
        
    def __set__(self, entity, value):
        """Descriptor protocol: set the value on the entity."""
        if self.model_type:
           if not isinstance(value, self.model_type):
              raise TypeError('Expected %s, got %s' % (repr(self.model_type), repr(value)))
        self.model = value
    
    def __init__(self, model=None):
        self.model_type = model
    
    def __getitem__(self, item):
       return getattr(self.model, item)
        
    def __getattr__(self, item):
       try:
          return self.__getitem__(item)
       except KeyError, exception:
          raise AttributeError(*exception.args)
        
    def get(self, item, default=None):
       try:
          return self.__getitem__(item)
       except Exception:
          pass
       return super(SuperRelationProperty, self).get(item, default)     
 
# Workflow error exceptions 
class WorkflowTransitionError(Exception):
      pass
  
class WorkflowStateError(Exception):
      pass
  
class WorkflowActionError(Exception):
      pass
  
class WorkflowActionNotReadyError(Exception):
      pass
  
class WorkflowBadStateCodeError(Exception):
      pass

class WorkflowBadActionCodeError(Exception):
      pass

class Workflow():
    
      """
      Workflow is a class used for making the object capable of having
      actions, states and transitions and every other aspect of ObjectLog concept.
      
      Example: 
      
      class User(ndb.BaseModel, ndb.Workflow)  or for expando class Expando(ndb.BaseExpando, ndb.Workflow)
            ....
      """
    
      OBJECT_DEFAULT_STATE = False
      OBJECT_STATES = {}
      OBJECT_TRANSITIONS = {}
      OBJECT_ACTIONS = {}
        
      @classmethod
      def generate_public_permissions(cls):
        # by default it wont return permissions who start with `sudo`
        actions = cls.OBJECT_ACTIONS.keys()
        out = []
        for action in actions:
            if action.startswith('sudo'):
               continue
            
            out.append(action)
            
        return out
    
      @classmethod
      def generate_admin_permissions(cls):
        # by default it will return permissions who start with `sudo`
        actions = cls.OBJECT_ACTIONS.keys()
        out = []
        for action in actions:
            if not action.startswith('sudo'):
               continue
            out.append(action)
        return out
          
      @classmethod
      def default_state(cls):
        # returns default state for this model
        return cls.resolve_state_code_by_name(cls.OBJECT_DEFAULT_STATE)
  
      @classmethod
      def resolve_state_code_by_name(cls, state_code):
          """
          Resolves state code by name
          """
          codes = cls.OBJECT_STATES
          code = codes.get(state_code)
          if not code:
             raise WorkflowStateError('This model does not have state code %s, while available %s' % (state_code, codes))
          return code[0]
      
      @classmethod
      def resolve_action_code_by_name(cls, st):
          """
          Resolves action code by name
          """
          actions = cls.OBJECT_ACTIONS
          action = actions.get(st, None)
          if action == None:
             raise WorkflowActionError('Unexisting action called %s, while available %s' % (st, actions))
          return action
      
      @classmethod
      def resolve_action_name_by_code(cls, code):
          """
         Resolves action name by code provided
          """
          for k, v in cls.OBJECT_ACTIONS.items():
              if v == code:
                 return k
          raise WorkflowBadActionCodeError('Bad action code provided %s, possible names %s' % (code, cls.OBJECT_ACTIONS.keys()))  
      
      @classmethod
      def resolve_state_name_by_code(cls, code):
          """
           Resolves state name by provided code
          """
          for k, value in cls.OBJECT_STATES.items():
              if value[0] == code:
                 return k
          raise WorkflowBadStateCodeError('Bad state code provided %s, possible names %s' % (code, cls.OBJECT_STATES.keys()))  
      
      def check_transition(self, state, action):
          """
          Checks if the transition is valid based on state and action provided
          """
          transitions = self.OBJECT_TRANSITIONS[action]
          
          current_state = self.resolve_state_name_by_code(self.state)
          
          if current_state not in transitions['from'] or state not in transitions['to']:
             raise WorkflowTransitionError('This object cannot go from state `%s` to state `%s`. It can only go from states `%s` to `%s`'
                                           % (current_state, state, transitions['from'], transitions['to']))
      
      def set_state(self, state, check=False):
          self.state = self.resolve_state_code_by_name(state)
          
      @property
      def get_state(self):
          return self.resolve_state_name_by_code(self.state)
          
      def new_action(self, action, state=None, **kwargs):
          """
           This function prepares ObjectLog for recording. This function will by default:
           - set agent as current user if not provided
           - log `self` object if its not provided otherwise (log_object=False)
          """
          self.register_tmp('record_actions', [])
          
          if state is not None: # if state is unchanged, no checks for transition needed?
              self.check_transition(state, action)
              self.set_state(state)
               
          action = self.resolve_action_code_by_name(action)
 
          if hasattr(self, 'state') and self.state == None:
             state = self.default_state()
          
          # lower namespace for one step   
          from app.core import log
          
          obj = kwargs.pop('log_object', True) # if obj is set to True it will log `self`
          agent = kwargs.pop('agent', None) # if agent is none it will use current user
      
          if agent is None:
             agent = get_current_user()
             kwargs['agent'] = agent.key
          else:
             kwargs['agent'] = agent
 
          objlog = log.ObjectLog(action=action, parent=self.key, **kwargs)
 
          if obj is True:
             obj = self
              
          if obj:
             objlog.log_object(obj)
          
          self.register_tmp('record_actions').append(objlog)
 
          return objlog
      
      
      def record_action(self, skip_check=False):
          # records any actions that are stored by `new_action`
          records = self.register_tmp('record_actions')
          if records is None:
             return list()
         
          any_actions = len(records)
          if not any_actions and not skip_check:
             raise WorkflowActionNotReadyError('This entity did not have any self.new_action() called')
          
          if any_actions:
             recorded = put_multi(records)
             self.set_tmp('record_actions', [])
             return recorded
          else:
             return list()
 
   
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
        fields = obj.get_mapped_properties()
    
        if convert:
           for i in convert:
               if issubclass(i.__class__, Property):
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

  
class EvalEnvironment(dict):
    
  """
    Eval environment is helper class for pyson.Eval in which creates context that helps pyson.Eval  
    successfully evaluate expressions given trough its constructor.
  """  

  def __init__(self, record):
     super(EvalEnvironment, self).__init__()
     self._record = record
        
  def __getitem__(self, item):
     if item in self._record._properties:
        items = item.split('.') # if Eval('object.foo.bar') it will digg till it reaches to .bar
        g = None
        for i in items:
            if not g:
               g = self._record
            # this will throw AttributError if Eval() is not configured properly, or model does not posses the actual
            # object that will return the attribute, wether that be `None` or `False` the attribute must exist
            g = getattr(g, i)
        return g
     return super(EvalEnvironment, self).__getitem__(item)

  def __getattr__(self, item):
      try:
         return self.__getitem__(item)
      except KeyError, exception:
         raise AttributeError(*exception.args)

  def get(self, item, default=None):
      try:
        return self.__getitem__(item)
      except Exception:
        pass
      return super(EvalEnvironment, self).get(item, default)

  def __nonzero__(self):
      return bool(self._record)
  
  
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
         
        @non_transactional
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
        
