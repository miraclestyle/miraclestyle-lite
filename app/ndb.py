# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import decimal

from google.appengine.ext.db import datastore_errors 
from google.appengine.ext.ndb import *

from app import pyson, util
 
ctx = get_context()

# memory policy for google app engine ndb calls is set to false, instead we decide per `get` wether to use memcache or not
ctx.set_memcache_policy(False)

# We always put double underscore for our private functions in order to avoid ndb library from clashing with our code
# see https://groups.google.com/d/msg/appengine-ndb-discuss/iSVBG29MAbY/a54rawIy5DUJ

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
    def ndb_key(cls, prop, value):
        value = cls._value(prop, value)
        if prop._repeated:
           return [Key(urlsafe=v) for v in value]
        else:
           return Key(urlsafe=value)
       
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
    def decimal(cls, prop, value):
        value = cls._value(prop, value)
        if prop._repeated:
           return [decimal.Decimal(v) for v in value]
        else:
           return decimal.Decimal(value)
 
  
property_types_validator = {
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
  'SuperBlobKeyProperty' : False,
  'SuperDecimalProperty' : Formatter.decimal,
  'SuperReferenceProperty' : Formatter.ndb_key,
}

def factory(module_model_path):
    """
     Retrieves model by its module path. e.g.
     model = factory('app.core.misc.Country')
     
     will load Country class.
     
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
  
  __original_values = {}
  
  def __init__(self, *args, **kwds):
      self.__original_values = {}
      super(_BaseModel, self).__init__(*args, **kwds)
  
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
  
  @classmethod
  def get_current_user(cls):
      if hasattr(cls, 'current_user'):
         # if the model is user, well call his function to prevent loop imports 
         return cls.current_user()
      # Shorthand for getting the current user
      from app.core.acl import User
      return User.current_user()
  
  def loaded(self):
      return self.key != None and self.key.id()
  
  @classmethod
  def get_or_prepare(cls, dataset, **kwds):
      """
        This function prepares the object from the provided data, or gets the object if the `id` is provided in dataset.
        If the id is provided, and the key.get does not find any data for the specified id, it will return None (@todo maybe raise Exception instead?).
        
        However, if the id is provided, and kwd param `get` is set to False, it will return populated entity in format:
        Entity(key=ndb.Key(urlsafe=id), **dataset)
        
        By default it will strip away all keys that is not in the list of fields for the model,
        unless you provide "only" param with the list of fields that the function will retrieve.
        
        Kwds are arguments passed to __init__ for models. They can be namespace, parent etc..
      """
      use_get = kwds.pop('get', True)
      expect = kwds.pop('only', cls.get_property_names() + ['id'])
      ctx_options = kwds.pop('ctx_options', {})
      populate = kwds.pop('populate', True)
      
      datasets = dict()
      
      _id = dataset.pop('key', None)
 
      create = True
      if _id:
         try:
             load = Key(urlsafe=_id)
             create = False
         except:
             pass
         
      if expect is not False:   
          for i in expect:
              datasets[i] = dataset.get(i)
      else:
          datasets = dataset.copy()
     
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
 
  @staticmethod
  def from_multiple_values(data):
      """ 
        Formats dict from format:
        dict = {
           'id' : [1,3,4],
           'name' : ['foo', 'bar', ['baz', 'foo']],
        }
        
        into
        
        list = [ {'id' : 1, 'name' : 'foo'}, 
                 {'id' : 3, 'name' : 'bar'},
                 {'id' : 4, 'name' : ['baz', 'foo']}]
      """
      out = []
      keys = data.keys()
      i = -1
      for _id in data.get('id', []):
          i += 1
          pdict = dict(id=_id)
          for k in keys:
              d = data.get(k)
              if (len(d)-1) == i:
                  pdict[k] = d[i]
              else:
                  pdict[k] = None
                  
          out.append(pdict)
                  
      return out
  
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
            prop._set_value(self, self.__original_values.get(prop._name))
    
  def set_original_values(self):
      for p in self._properties:
          self.__original_values[p] = self._properties[p]._get_value(self)
 
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
  def delete(cls, **kwds):
 
        response = Response()
 
        @transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds, only=False, populate=False)
               
               if entity and entity.loaded():
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response 

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
  
class SuperDecimalProperty(SuperStringProperty):
    """Decimal property that accepts only `decimal.Decimal`"""
    
    def _validate(self, value):
      if not isinstance(value, (decimal.Decimal)):
        raise TypeError('expected an decimal, got %s' % repr(value)) # explicitly allow only decimal
    
    def _to_base_type(self, value):
        return str(value) # Doesn't matter which type, always return in string format
    
    def _from_base_type(self, value):
        return decimal.Decimal(value)  # Always return a decimal

      
class SuperReferenceProperty(SuperKeyProperty):
      
    """Replicated property from `db` module"""
      
    def _validate(self, value):
        if not isinstance(value, Model):
           raise TypeError('expected an ndb.Model, got %s' % repr(value))
    
    def _to_base_type(self, value):
        return value.key
    
    def _from_base_type(self, value):
        return value.get()

class SuperRelationProperty(dict):
    """
      ################################################################################################   
      ##### This property is not yet tested and yet to be decided whether should be used anyway! #####
      ################################################################################################
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
      
      __record_action = []
      
      def __init__(self, *args, **kwds):
          self.__record_action = []
          super(Workflow, self).__init(*args, **kwds)
          
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
          raise WorkflowBadActionCodeError('Bad action coded provided %s, possible names %s' % (code, cls.OBJECT_ACTIONS.keys()))  
      
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
          puts = kwargs.pop('put', None)
          
          if agent is None:
             agent = self.get_current_user()
             kwargs['agent'] = agent.key
          else:
             kwargs['agent'] = agent
 
          objlog = log.ObjectLog(action=action, parent=self.key, **kwargs)
 
          if obj is True:
             obj = self
              
          if obj:
             objlog.log_object(obj)
          
          self.__record_action.append(objlog)
 
          return objlog
      
      
      def record_action(self, skip_check=False):
          # records any actions that are stored by `new_action`
          any_actions = len(self.__record_action)
          if not any_actions and not skip_check:
             raise WorkflowActionNotReadyError('This entity did not have any self.new_action() called')
          
          if any_actions:
             recorded = put_multi(self.__record_action)
             self.__record_action = []
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
    
    def validate_input(self, kwds, obj, **kwargs):
        
        """
          This method is used to format, and validate the user input based on the model property definition. 
          Accepts:
          kwds: dict with unformatted data. This dict must be mutable in order for kwds to be formatted.
          obj: `cls` or model class
          **kwargs: skip: skips only the defined field names for validation
                    only: only formats specified field names for validation
                    convert: converts into specified data type. for example:
                        kwds = {'domain' : 'large key...'}
                        response.validate_input(kwds, obj, convert=[('domain', ndb.Key)])
                        
                        it will convert kwds['domain'] into ndb.Key(...)
                    
          Example:
          
          class Test(ndb.BaseModel):
                name = ndb.SuperStringProperty(required=True)
                number = ndb.SuperIntegerProperty(required=True)     
                
          ....
          
          data = {'name' : 52}
          response.validate_input(data, Test)
   
          the formatter will adjust the dict to
          
          data = {'name' : '52'}
          
          also the error that the "number" is required will be placed in response:
          
          response['errors'] = {'number' : ['required']}
          ...
          
        """
        
        skip = kwargs.pop('skip', None)
        only = kwargs.pop('only', None)
        convert = kwargs.pop('convert', None)
        fields = obj.get_mapped_properties()
        
        if convert:
           for i in convert:
               name = i[0]
               _type = i[1]
               try:
                   can_skip = i[2]
               except IndexError as e:
                   can_skip = False
                   
               value = kwds.get(name)
               if value is None and can_skip:
                  continue
              
               try:
                    if isinstance(value, _type):
                          continue
                    if _type.__name__ == 'bool':
                       kwds[name] = bool(int(value))
                    elif _type.__name__ in ('int', 'long'):
                       if isinstance(value, (int, long)):
                          continue  
                       kwds[name] = _type(value)
                    elif _type == Key:
                       if isinstance(value, Key):
                          continue 
                       kwds[name] = _type(urlsafe=value)
                    else:
                       kwds[name] = _type(value)
               except Exception as e:
                    self.invalid(name)
                  
        
        for k,v in fields.items():
            
            if skip and k in skip:
               continue
           
            if only is False:
               break
           
            if only:
               if k not in only:
                  continue
                    
            value = kwds.get(k)
            if value is None:
               if v._required:
                  self.required(k)
                  
            if value is None and not v._required:
               continue
   
            valid = property_types_validator.get(v.__class__.__name__)
            
            if valid: 
               try: 
                   kwds[k] = valid(v, value)
               except (ValueError, TypeError) as e:
                   self.invalid(k)
                   
        return self
               
               
    def are_valid_types(self, kwds, configs):
        """
          Validates input, and converts the values into proper type
          :param kwds - data filtered
          :param config - tuple with config, example: (('name', unicode), ('number', int), ('is_true', bool)) etc.
        """
        for config in configs:
            k = config[0]
            _type = config[1]
            not_required = False
            try:
                not_required = config[2]
            except IndexError as e:
                pass
            
            value = kwds.get(k)
            
            if not_required and value is None:
               continue
            
            try:
                if isinstance(value, _type):
                   continue 
                
                if _type.__name__ == 'bool':
                   kwds[k] = bool(int(value))
                elif _type.__name__ == 'int':
                   kwds[k] = int(value)
                elif _type == Key:
                   kwds[k] = _type(urlsafe=value)
                else:
                   kwds[k] = _type(value)
            except Exception as e:
                self.invalid(k)
                
        return kwds
  
  
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
