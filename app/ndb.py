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

def factory(module_model_path):
    
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
  
  def __json__(self):
      """ This magic method is called by json encoder. 
          The values that this method returns must be json compliant
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
         return cls.current_user()
      # Shorthand for getting the current user
      from app.core.acl import User
      return User.current_user()
  
  def loaded(self):
      return self.key != None
 
  
  @classmethod
  def load_from_values(cls, dataset, **kwds):
      single = False
      items = []
      only = kwds.pop('only', None)
      get = kwds.pop('get', None)
      if not isinstance(dataset, (list, tuple)):
          dataset = (dataset, )
          single = True
          
      for data in dataset:    
          try:
            key = Key(urlsafe=data['id'])
          except:
            create = True
            
          if not create:      
            data['key'] = key
            
          if only is not None:
             new_data = {}
             for i in only:
                 if data.get(i):
                    new_data[i] = data[i]
             data = new_data
                    
          if create:
             items.append(cls(**data))
          elif get is not None:
             items.append(key.get())
          else:
             items.append(cls(**data))
 
      if single:
        return items[0]
      else:
        return items
  
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
  def get_property_names(cls):
      out = []
      for prop in cls._properties:
          out.append(prop._code_name)
          
      if hasattr(cls, 'has_expando_fields'):
         for prop in cls.has_expando_fields():
             out.append(prop._code_name)
      return out  
 
      

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
    def has_expando_fields(cls):
        if hasattr(cls, 'EXPANDO_FIELDS'):
           return cls.EXPANDO_FIELDS
        else:
           return False
        
    def __getattr__(self, name):
       ex = self.has_expando_fields()
       if ex:
          vf = ex.get(name) 
          if vf:
             if not hasattr(vf, '_code_name'):
                vf._code_name = name
             return vf._get_value(self)
       return super(BaseExpando, self).__getattr__(name)
      
    def __setattr__(self, name, value):
        ex = self.has_expando_fields()
        if ex:
           vf = ex.get(name) 
           if vf:
              vf._code_name = name
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
                     v._code_name = k
                     prop = v
                     self._properties[v._name] = v
                     break        
  
        if prop is None:
          prop = self._fake_property(p, next, indexed)
        return prop

class _BaseProperty(object):
    
    _writable = False
    _visible = False
    
    def __init__(self, *args, **kwds):
        self._writable = kwds.pop('writable', self._writable)
        self._visible = kwds.pop('visible', self._visible)
        
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
          
          if self.state not in transitions['from'] or state not in transitions['to']:
             raise WorkflowTransitionError('This object cannot go from state `%s` to state `%s`. It can only go from states `%s` to `%s`'
                                           % (self.state, state, transitions['from'], transitions['to']))
      
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
              self.set_state(state)
              self.check_transition(state, action)
              
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
      Response dict object used for preparing data which is returned to clients for parsing.
      Usually every model method should return this type of response object.
    """
    def transaction_error(self, e):
        
        if isinstance(e, datastore_errors.Timeout):
           return self.transaction_timeout()
        if isinstance(e, datastore_errors.TransactionFailedError):
           return self.transaction_failed()
        
        raise e
 
    def transaction_timeout(self):
        return self.error('transaction_error', 'timeout')
    
    def transaction_failed(self):
        return self.error('transaction_error', 'failed')
    
    def required(self, k):
        return self.error(k, 'required')
        
    def invalid(self, k):
        return self.error(k, 'invalid_input')
    
    def status(self, m):
        # generic `status` of the response. 
        # It informs most usual errors that might ocurr. E.g. object not found, etc.
        self['status'] = m
        return self
    
    def not_found(self):
        self['status'] = 'not_found'
        return self
    
    def not_authorized(self):
        return self.error('user', 'not_authorized')
        
    def not_logged_in(self):
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