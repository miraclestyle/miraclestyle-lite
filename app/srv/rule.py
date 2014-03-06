# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import collections

from app import ndb, util
from app.lib.safe_eval import safe_eval
from app.srv import event, log, callback

"""
This file is used to control input, and output trough the application Model actions.

Examples:
 

from app.srv import rule, event

class OtherModel2(ndb.BaseModel):

   name = ndb.SuperStringProperty()


class OtherModel(ndb.BaseModel):

   name = ndb.SuperStringProperty()
   other = ndb.SuperStructuredProperty(OtherModel2)

class Model(ndb.BaseModel):

   foo = ndb.SuperStringProperty()
   bar = ndb.SuperStructuredProperty(OtherModel)

   _virtual_fields = {
     'my_magic_field' : ndb.ComputedProperty(lambda self: 'this field does magic!')
   }
 
   
   _global_role = rule.GlobalRole(permissions=[
                                  
                                  Action permissions:
                                  
                                  work very simple, its a key-value checking system with conditions
                                  rule.ActionPermission('0', event.Action.build_key('0-0').urlsafe(), True, "context variable available, valid any `simple` python expression"),
                                  
                                  
                                  Field permissions:
                              
                                  rule.FieldPermission('0', 'bar', True, True, True, 'True'), 
                                  
                                  This field permission definition would generate:
                                  
                                   bar : {
                                     writable : True,
                                     required : True,
                                     visible : True,
                                     name : {
                                         writable : True,
                                         required : True,
                                         visible : True,
                                     },
                                     
                                     other : {
                                        writable : True,
                                        required : True,
                                        visible : True,
                                        name : {
                                          writable : True,
                                          required : True,
                                          visible : True,
                                        }
                                        
                                     }
                                  }
                                  
                                  If you specify rule like this
                                  
                                  rule.FieldPermission('0', 'bar.other.name', False, False, False, 'True'),
                                  
                                  This field permission definition would generate:
                                  
                                   bar : {
                                     writable : True,
                                     required : True,
                                     visible : True,
                                     name : {
                                         writable : True,
                                         required : True,
                                         visible : True,
                                     },
                                     
                                     other : {
                                        writable : True,
                                        required : True,
                                        visible : True,
                                        name : {
                                          writable : False,
                                          required : False,
                                          visible : False,
                                        }
                                      
                                     }
                                  }
                                   
                                  rule.FieldPermission('0', ['my_magic_field', 'foo', 'bar'])
                                  
  _actions = {
     'friendly_action_name' : event.Action(id='0-0',
                                           arguments={
                                             'my_input_name' : ndb.<Any NDB property that begins with `Super`>
                                           })
    
  }
  
  @classmethod
  def friendly_action_name(context):
      
      Now, rule engine will only work if the entity is set into the context like so
      
      context.rule.entity = entity
      
      `entity` must be an instance of any subclass of ndb.Base<Type> 
        and it should have _global_role if its not part of domain
        
      By default all actions and field permissions are False, only way to override that is to define rules for each of 
      the types, either field or action
      
      
      
      .....
      
      
      rule.write function should be used before doing entity.put()
      
      the rule.write will ensure that there wont be illegal property changes to the entity before putting.
      
      the rule.write will only set the value(s) if the conditions are met from the rule engine - entity._field_permissons
      
      there is a problem that comes with repeated Structured properties:
 
      when the rule.write is fired it wont be a problem to update existing properties in the list (respecting the field perms)
      
      the problem is if the additional item is added into the list, in that case if the structured property permission is not
      set to writable that item will not get appended into the list
      
      
      ....
      
      rule.read works on system of elimination, if the property is not visible, it will be hidden from output,
      
      if the property is structured, it will check its fields recursively until they are all hidden if needed.
          
"""

class ActionDenied(Exception):
    
    def __init__(self, context):
       self.message = {'action_denied' : context.action}
       
def is_structured_property(field):
    # checks if the provided value is instance of one of the structured properties, and also checks if the model class is set
    return isinstance(field, (ndb.SuperStructuredProperty, ndb.SuperLocalStructuredProperty)) and field._modelclass
    
def parse_property(values, field):
  
    # digs trough path provided for the "values" provided - values recognizes dict, and objects with __getattr__
  
    field_path = field.split('.')
    
    is_dict = isinstance(values, dict)
    
    for path in field_path:
       if is_dict:
         try:
           values = values[path]
         except KeyError as e:
           return None
       else:
          try:
             values = getattr(values, path)
          except ValueError as e:
             return None
       
    return values
       

def _check_field(context, name, key):
    # internal helper to check if the field for provided rule context is either writable, invisible, or required
 
    if context.rule.entity:
      # this is like this because we can use it like writable(context, ('field1', 'field2'))
      if not isinstance(key, (tuple, list)):
         key = (key, )
      checks = []
      for k in key:
          dig = parse_property(context.rule.entity._field_permissions, name)
          checks.append(dig[k])
      return all(checks)
    else:
      return False

def writable(context, name):
  # checks if the field is writable for provided rule context
  return _check_field(context, name, 'writable')

def visible(context, name):
  # checks if the field is visible for provided rule context
  return _check_field(context, name, 'visible')

def required(context, name):
  # checks if the field is required for provided rule context
  return _check_field(context, name, 'required')

def executable(context):
  # checks if the action is executable for the provided rule context
  if context.rule.entity:
     return context.rule.entity._action_permissions[context.action.key.urlsafe()]['executable']
  else:
     return False
   
def _write_helper(initial_value, field_permissions, supplied_structured_key, supplied_structured_field, 
                  supplied_structured_value, structured_field_key, structured_field, is_writable):
    # recursive function
    
    if is_structured_property(structured_field):
       for _field_key, _field in structured_field._modelclass.get_fields().items():
 
           value_value = None
           
           if initial_value is not None:
              initial_value = getattr(initial_value, supplied_structured_key)
              
           if supplied_structured_value is not None:
              value_value = getattr(supplied_structured_value, _field_key)
 
           _write_helper(initial_value, field_permissions[structured_field_key], 
                        structured_field_key, supplied_structured_field, value_value, _field_key, _field,
                        field_permissions[structured_field_key]['writable'])
    else:
       if field_permissions[structured_field_key]['writable']:
          # if the property inside a structured class is not writable, we set the initial value
          # into a newly constructed structured property, therefore overriding whatever the user set 
          if supplied_structured_field._repeated:
             if supplied_structured_value is None or not len(supplied_structured_value):
                if is_writable:
                   util.logger('found nothing, setting %s.%s=%s' % (initial_value, supplied_structured_key, supplied_structured_value))
                   setattr(initial_value, supplied_structured_key, supplied_structured_value)
             else:
                 for i,supplied_structured_value_item in enumerate(supplied_structured_value):
                     # gets the unchanged structured value
                     initial = None
                     initial_structured = getattr(initial_value, supplied_structured_key)
                     if not initial_structured: # if it isnt there it must be a list then
                       initial_structured = []
                     try:
                       initial = initial_structured[i] # attempt to edit 
                     except IndexError as e:
                       # doesnt exist, this is a new item in the list?
                       # now only way to be in able to ADD a new item is to have "writable" permssion on the entire structured field
                       # in that case setting writable false on those fields doesnt make sense
                       if is_writable:
                         util.logger('creating a new %s' % supplied_structured_value_item) 
                         initial = supplied_structured_value_item
                         initial_structured.append(initial)
                       
                     if initial is not None:
                        supplied_structured_value_item_far = getattr(supplied_structured_value_item, structured_field_key)
                        setattr(initial, structured_field_key, supplied_structured_value_item_far) # this here changes the unstructured property value
                        util.logger('wrote %s.%s=%s' % (initial.__class__.__name__, structured_field_key, supplied_structured_value_item_far))            
          else:
             initial = getattr(initial_value, supplied_structured_key)
             if initial is not None:
                supplied_structured_value_far = getattr(supplied_structured_value, structured_field_key)
                setattr(initial, structured_field_key, supplied_structured_value_far)
                util.logger('wrote %s.%s=%s' % (initial.__class__.__name__, structured_field_key, supplied_structured_value_far))

def write(entity, values):
  
    # writes property values with respect to rule engine, im not sure if the provided value should be entity or context?
    
    entity_fields = entity.get_fields()
  
    for value_key, value in values.items():
        if value_key in entity_fields: # check if the value is in entities field list
          prop = entity_fields.get(value_key)
          is_writable = entity._field_permissions[value_key]['writable']
          
          if is_structured_property(prop): # if the property is structured, iterate over its fields and determine what can be written
             for field_key, field in prop._modelclass.get_fields().items():
                 _write_helper(entity, entity._field_permissions[value_key], value_key, prop, value, field_key, field, is_writable) # recursive
          else:
             if is_writable:  # if the entire property is writable
                setattr(entity, value_key, value) 
                util.logger('wrote %s.%s=%s' % (entity.__class__.__name__, value_key, value))
                
def _read_helper(field_permissions, entity_structured_field_key, entity_structured_field, entity_structured_value,
                  structured_field_key, structured_field):
    # recursive function

    if is_structured_property(structured_field):
       for _field_key, _field in structured_field._modelclass.get_fields().items():
           if entity_structured_value is not None:
              entity_structured_value = getattr(entity_structured_value, _field_key)
           _read_helper(field_permissions[structured_field_key], structured_field_key, structured_field, entity_structured_value, _field_key, _field)
    else:
       if not field_permissions[structured_field_key]['visible']:
          if entity_structured_field._repeated:
             for entity_structured_value_item in entity_structured_value:
                 if entity_structured_value_item is not None:
                    entity_structured_value_item.remove_field(structured_field_key)
          else:
             if entity_structured_value is not None:
                entity_structured_value.remove_field(structured_field_key)
                      
def read(entity):
  
    # configures output variables for the provided entity with respect to rule engine. should the param be entity or context?
 
    entity_fields = entity.get_fields()
 
    for field_key, field in entity_fields.items():
 
        if is_structured_property(field):
          # if the field is structured, check for its sub-fields recursively
          for _field_key, _field in field._modelclass.get_fields().items():
              structured_entity = getattr(entity, field_key)
              _read_helper(entity._field_permissions[field_key], field_key, field, structured_entity, _field_key, _field) # recursive     
        else:
           if not entity._field_permissions[field_key]['visible']:
              entity.remove_field(field_key) # if the field is not visible, remove it completely from output

class Context():
  
  def __init__(self):
    self.entity = None

    
class Permission():
  """ Base class for all permissions """


class ActionPermission(Permission):
   
   
  def __init__(self, kind, action, executable=None, condition=None):
    
    self.kind = kind # entity kind identifier (entity._kind)
    self.action = action # action id (action.key.id()), or action key (action.key) ? ----- this could be a list
    self.executable = executable
    self.condition = condition
    
  def __todict__(self):
     return {'kind' : self.kind, 'action' : self.action,
             'executable' : self.executable, 'condition' : self.condition}
    
  def run(self, role, context):
    
    if not isinstance(self.action, (tuple, list)):
       self.action = [self.action]
    
    for action in self.action:
        if (self.kind == context.rule.entity.get_kind()) and (action in context.rule.entity.get_actions()) and (safe_eval(self.condition, {'context' : context, 'action' : action})) and (self.executable != None):
           context.rule.entity._action_permissions[action]['executable'].append(self.executable)


class FieldPermission(Permission):
  
  
  def __init__(self, kind, field, writable=None, visible=None, required=None, condition=None):
    
    self.kind = kind # entity kind identifier (entity._kind)
    self.field = field # this must be a field code name from ndb property (field._code_name) ---- This could be a list?
    self.writable = writable
    self.visible = visible
    self.condition = condition
    
  def __todict__(self):
     return {'kind' : self.kind, 'field' : self.field, 'writable' : self.writable,
             'visible' : self.visible, 'condition' : self.condition}
    
    
  def run(self, role, context):
    
    if not isinstance(self.field, (tuple, list)):
       self.field = [self.field]
    
    for field in self.field:
        dig = parse_property(context.rule.entity._field_permissions, field) # retrieves field value from foo.bar.far
        
        # added in safe eval `field` - the field that is currently in the loop 
        if (self.kind == context.rule.entity.get_kind()) and dig and (safe_eval(self.condition, {'context' : context, 'field' : field})):
          if (self.writable != None):
            dig['writable'].append(self.writable)
          if (self.visible != None):
            dig['visible'].append(self.visible)
 

class Role(ndb.BaseExpando):
    
    # root (namespace Domain)
    # ovaj model ili LocalRole se jedino mogu koristiti u runtime i cuvati u datastore, dok se GlobalRole moze samo programski iskoristiti
    # ovo bi bilo tlacno za resurse ali je jedini preostao feature sa kojim 
    # bi ovaj rule engine koncept prevazisao sve ostale security modele
    # parent_record = ndb.SuperKeyProperty('1', kind='44', indexed=False) 
    # complete_name = ndb.SuperTextProperty('3')
    name = ndb.SuperStringProperty('1', required=True)
    active = ndb.SuperBooleanProperty('2', default=True)
    permissions = ndb.SuperPickleProperty('3', required=True, compressed=False) # [permission1, permission2,...]
    
    ### za ovo smo rekli da svakako treba da se radi validacija pri inputu 
    # treba da postoji validator da proverava prilikom put()-a da li su u permissions listi instance Permission klase
 
    def run(self, context):
        for permission in self.permissions:
            permission.run(self, context)
 


class Engine:
  
    
  @classmethod
  def _prepare_fields_helper(cls): # it must be a function that makes this dictionary, dry
      # this must build orderedDict because writable, visible, required NEEDS to be `decide()` 
      # first in order to allow inheritence of permissions - like folder structure
      return collections.OrderedDict([('writable', []), ('visible', [])])
  
  @classmethod
  def prepare_fields(cls, props, fields, _props=None):
    # recursive method
 
    for field_key, field in fields.items():
        if is_structured_property(field): # isinstance(Struct, Local)
           aprops = _props
           if aprops is None:
              aprops = props
           if field_key not in aprops:
              aprops[field_key] = cls._prepare_fields_helper()
           cls.prepare_fields(props, field._modelclass.get_fields(), aprops[field_key])
        else:
           aprops = _props
           if aprops is None:
              aprops = props
           aprops[field_key] = cls._prepare_fields_helper()

  @classmethod
  def prepare(cls, context):
    
    context.rule.entity._field_permissions = {} 
    context.rule.entity._action_permissions = {} 
 
    fields = context.rule.entity.get_fields()
 
    cls.prepare_fields(context.rule.entity._field_permissions, fields)
 
    actions = context.rule.entity.get_actions()
       
    for action_key in actions:
       context.rule.entity._action_permissions[action_key] = {'executable' : []}
  
  @classmethod
  def _decide_helper(cls, calc, element, prop, value, strict, parent=None):
        # recursive function
 
        if element not in calc:
            calc[element] = {}
            
        if isinstance(value, dict):
           for _value_key, _value in value.items():
               cls._decide_helper(calc[element], prop, _value_key, _value, strict, element)
        else:
          if len(value):
            if (strict):
              if all(value):
                 calc[element][prop] = True
              else:
                 calc[element][prop] = False
            elif any(value):
              calc[element][prop] = True
            else:
              calc[element][prop] = False
          else:
            calc[element][prop] = None
            
            if parent and not len(value):
                calc[element][prop] = calc[prop] 
 
  @classmethod
  def decide(cls, data, strict):
    calc = {}
  
    for element, properties in data.items():
          for prop, value in properties.items():
              cls._decide_helper(calc, element, prop, value, strict)
    return calc
  
  @classmethod
  def _compile_local_data_helper(cls, global_data_calc, local_data_calc, element, prop, value):
      # recursive function
      
      if isinstance(value, dict):
         for _value_key,_value in value.items():
             cls._local_data_helper(global_data_calc[element], local_data_calc[element], prop, _value_key, _value)
      else:   
        if element in global_data_calc:
           if prop in global_data_calc[element]:
              gc = global_data_calc[element][prop]
              if gc is not None and gc != value:
                    cls._local_data_calc[element][prop] = gc
            
        if local_data_calc[element][prop] is None:
           local_data_calc[element][prop] = False
           
  
  @classmethod       
  def _compile_global_data_calc_helper(cls, local_data_calc, element, prop, value):
      # recursive function
      
      if isinstance(value, dict):
         for _value_key,_value in value.items():
             cls._compile_global_data_calc_helper(local_data_calc[element], prop, _value_key, _value)
      else:
        if prop not in local_data_calc[element]:
           local_data_calc[element][prop] = value
           
  @classmethod
  def _compile_just_global_data_calc_helper(cls, global_data_calc, element, prop, value):
    # recursive function
    
    if isinstance(value, dict):
       for _value_key,_value in value.items():
          cls._compile_just_global_data_calc_helper(global_data_calc[element], prop, _value_key, _value)
    else:
      if value is None:
         value = False
      global_data_calc[element][prop] = value
  
  @classmethod
  def compile(cls, local_data, global_data, strict=False):
    
    global_data_calc = cls.decide(global_data, strict)
 
    # if any local data, process them
    if local_data:
       local_data_calc = cls.decide(local_data, strict)
        
       # iterate over local data, and override them with the global data, if any
       for element, properties in local_data_calc.items():
          for prop, value in properties.items():
              cls._compile_local_data_helper(global_data_calc, local_data_calc, element, prop, value)
        
       # make sure that global data are always present
       for element, properties in global_data_calc.items():
          if element not in local_data_calc:
            for prop, value in properties.items():
              cls._compile_global_data_calc_helper(local_data_calc, element, prop, value)
            
       finals = local_data_calc
    
    # otherwise just use global data    
    else:
 
       for element, properties in global_data_calc.items():
          for prop, value in properties.items():
            cls._compile_just_global_data_calc_helper(global_data_calc, element, prop, value)
            
       finals = global_data_calc
    return finals
  
  @classmethod
  def run(cls, context, skip_user_roles=False, strict=False):
    
    # datastore system
    
    if context.rule.entity:
 
      # call prepare first, populates required dicts into the entity instance
      cls.prepare(context)
      local_action_permissions = {}
      local_field_permissions = {}
      
      if not skip_user_roles:
        domain_user_key = DomainUser.build_key(context.auth.user.key_id_str, namespace=context.rule.entity.key_namespace)
        domain_user = domain_user_key.get()
        clean_roles = False
        
        if domain_user and domain_user.state == 'accepted':
            roles = ndb.get_multi(domain_user.roles)
            for role in roles:
              if role is None:
                clean_roles = True
              else:   
                if role.active:
                   role.run(context)
                   
            if clean_roles:
              context.callbacks.inputs.append({'action_key' : 'clean_roles', 'key' : domain_user.key.urlsafe(), 'action_model' : 'srv.rule.DomainUser'})
              callback.Engine.run(context)
            
        # copy 
        local_action_permissions = context.rule.entity._action_permissions.copy()
        local_field_permissions = context.rule.entity._field_permissions.copy()
      
        # empty
        cls.prepare(context)
   
      entity = context.rule.entity
      if hasattr(entity, '_global_role') and isinstance(entity._global_role, GlobalRole):
         entity._global_role.run(context)
      
      # copy   
      global_action_permissions = context.rule.entity._action_permissions.copy()
      global_field_permissions = context.rule.entity._field_permissions.copy()
      
      # empty
      cls.prepare(context)
     
      context.rule.entity._action_permissions = cls.compile(local_action_permissions, global_action_permissions, strict)
      context.rule.entity._field_permissions = cls.compile(local_field_permissions, global_field_permissions, strict)
      
      context.rule.entity.add_field('_action_permissions')
      context.rule.entity.add_field('_field_permissions')
   

class GlobalRole(Role):
      pass

class DomainRole(Role):
  
    _kind = 60
  
    _global_role = GlobalRole(permissions=[
                                            ActionPermission('60', event.Action.build_key('60-0').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            ActionPermission('60', event.Action.build_key('60-3').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            ActionPermission('60', event.Action.build_key('60-1').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            ActionPermission('60', event.Action.build_key('60-2').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            
                                            ActionPermission('60', event.Action.build_key('60-0').urlsafe(), False, "not context.rule.entity.key_id_str == 'admin'"),
                                            ActionPermission('60', event.Action.build_key('60-3').urlsafe(), False, "not context.rule.entity.key_id_str == 'admin'"),
                                            ActionPermission('60', event.Action.build_key('60-1').urlsafe(), False, "not context.rule.entity.key_id_str == 'admin'"),
                                          ])
    # unique action naming, possible usage is '_kind_id-manage'
    _actions = {
       'create' : event.Action(id='60-0',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'permissions' : ndb.SuperJsonProperty(required=True),
                                 'active' : ndb.SuperBooleanProperty(default=True),
                              }
                             ),
                
       'update' : event.Action(id='60-3',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='60', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'permissions' : ndb.SuperJsonProperty(required=True),
                                 'active' : ndb.SuperBooleanProperty(default=True),
                              }
                             ),
                
       'delete' : event.Action(id='60-1',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='60', required=True),
                              }
                             ),
                
       'list' : event.Action(id='60-2',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                              }
                             ),
    }
 
    @classmethod
    def delete(cls, context):
             
        entity_key = context.input.get('key')
        entity = entity_key.get()
        
        context.rule.entity = entity
        Engine.run(context)
          
        if not executable(context):
           raise ActionDenied(context)
 
        @ndb.transactional(xg=True)
        def transaction():

          if entity and entity.loaded():
             # log & delete
             context.log.entities.append((entity, ))
             entity.key.delete()
             log.Engine.run(context)
        
          else:
             context.not_found()      
           
        transaction()
           
        return context
      
    @classmethod
    def complete_save(cls, entity, context):
      
        context.rule.entity = entity
        Engine.run(context)
        
        if not executable(context):
           raise ActionDenied(context)
         
        entity.name = context.input.get('name')
        entity.active = context.input.get('active')
            
      
        permissions = context.input.get('permissions')
        set_permissions = []
        for permission in permissions:
          
            if 'action' not in permission:
               set_permissions.append(FieldPermission(permission.get('kind'),
                                                       permission.get('field'),
                                                       permission.get('writable'),
                                                       permission.get('visible'), 
                                                       permission.get('required'),
                                                       permission.get('condition')))
               
            else:
              set_permissions.append(ActionPermission(permission.get('kind'),
                                                      permission.get('action'),
                                                      permission.get('executable'),
                                                      permission.get('condition')))
        entity.permissions = set_permissions  
        
        entity.put()
        
        context.log.entities.append((entity,))
        log.Engine.run(context)
 
      
    @classmethod
    def create(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
          
            domain_key = context.input.get('domain')
      
            domain = domain_key.get()
            entity = cls(namespace=domain.key_namespace)
           
            cls.complete_save(entity, context)  
               
        transaction()
            
        return context
    
    @classmethod
    def update(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
        
            entity_key = context.input.get('key')
            entity = entity_key.get()
          
            cls.complete_save(entity, context)
           
        transaction()
            
        return context

    @classmethod
    def list(cls, context):
  
       domain_key = context.input.get('domain')
       domain = domain_key.get()
       
       context.rule.entity = domain
       
       Engine.run(context)
       
       if not executable(context):
          raise ActionDenied(context)
       
       context.output['roles'] = cls.query(namespace=domain.key_namespace).fetch()
  
       return context
 
class DomainUser(ndb.BaseModel):
    
    _kind = 8
    
    # root (namespace Domain) - id = str(user_key.id())
    # mozda bude trebalo jos indexa u zavistnosti od potreba u UIUX
    # composite index: ancestor:no - name
    name = ndb.SuperStringProperty('1', required=True)# ovo je deskriptiv koji administratoru sluzi kako bi lakse spoznao usera
    roles = ndb.SuperKeyProperty('2', kind=DomainRole, indexed=True, repeated=True)# vazno je osigurati da se u ovoj listi ne nadju duplikati rola, jer to onda predstavlja security issue!!
    state = ndb.SuperStringProperty('3', required=True)# invited/accepted
    
    _default_indexed = False
    
    _global_role = GlobalRole(permissions=[
                                            ActionPermission('8', event.Action.build_key('8-0').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            
                                            ActionPermission('8', event.Action.build_key('8-1').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            ActionPermission('8', event.Action.build_key('8-1').urlsafe(), True, "(context.rule.entity.namespace_entity.state == 'active' and context.auth.user.key_id_str == context.rule.entity.key_id_str) and not (context.auth.user.key_id_str == context.rule.entity.namespace_entity.primary_contact.entity.key_id_str)"),
                                            ActionPermission('8', event.Action.build_key('8-1').urlsafe(), False, "(context.auth.user.key_id_str == context.rule.entity.namespace_entity.primary_contact.entity.key_id_str)"),

                                            
                                            ActionPermission('8', event.Action.build_key('8-2').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active' or context.auth.user.key_id_str != context.rule.entity.key_id_str"),
                                            ActionPermission('8', event.Action.build_key('8-2').urlsafe(), True, "context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'invited' and context.auth.user.key_id_str == context.rule.entity.key_id_str"),
                                            ActionPermission('8', event.Action.build_key('8-3').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            ActionPermission('8', event.Action.build_key('8-4').urlsafe(), True, "context.auth.user.is_taskqueue"),
                                            ActionPermission('8', event.Action.build_key('8-4').urlsafe(), False, "not context.auth.user.is_taskqueue"),

                                          ])
    # unique action naming, possible usage is '_kind_id-manage'
    _actions = {
       'invite' : event.Action(id='8-0',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6'),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'user' : ndb.SuperKeyProperty(kind='0'),
                                 'roles' : ndb.SuperKeyProperty(kind=DomainRole, repeated=True),
                              }
                             ),
                
       'remove' : event.Action(id='8-1',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='8', required=True),
                              }
                             ),
                
       'accept' : event.Action(id='8-2',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='8', required=True),
                              }
                             ),
                
       'update' : event.Action(id='8-3',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='8', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'roles' : ndb.SuperKeyProperty(kind=DomainRole, repeated=True),
                              }
                             ),
                
       'clean_roles' : event.Action(id='8-4',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='8', required=True),
                              }
                             ),
    }
    
    @classmethod
    def clean_roles(cls, context):
      
        @ndb.transactional(xg=True)
        def transaction():
          
            entity_key = context.input.get('key')
            entity = entity_key.get()
            
            context.rule.entity = entity
            
            Engine.run(context, True)
            
            if not executable(context):
               raise ActionDenied(context)
            
            roles = ndb.get_multi(entity.roles)
            
            for i,role in enumerate(roles):
                if role is None:
                   entity.roles.pop(i)
            entity.put()
            
            context.log.entities.append((entity,))
            log.Engine.run(context)
                
        transaction()
        
        return context
 
    # Poziva novog usera u domenu
    @classmethod
    def invite(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
           
           name = context.input.get('name')            
           user_key = context.input.get('user')
           role_keys = context.input.get('roles')
 
           get_roles = ndb.get_multi(role_keys)
           user = user_key.get()
           
           domain_key = context.input.get('domain')
           domain = domain_key.get()
           
           domain_user = cls(id=user.key_id_str, namespace=domain.key_namespace)

           context.rule.entity = domain_user
           Engine.run(context)
             
           if not executable(context):
              raise ActionDenied(context)
            
           already_invited = cls.build_key(user.key_id_str, namespace=domain.key_namespace).get()
           
           if already_invited:
             # raise custom exception!!!
              return context.error('user', 'already_invited')
            
           domain_key = context.input.get('domain')
           domain = domain_key.get()
           
           if user.state == 'active':
              roles = []
              for role in get_roles:
                  # avoid rogue roles
                  if role.key.namespace() == domain.key_namespace:
                     roles.append(role.key)
                     
              domain_user.populate(name=name, user=user.key, state='invited', roles=roles)
           
              user.domains.append(domain.key)
              
              # write both domain_user, and user
              
              ndb.put_multi([domain_user, user])
              
              context.log.entities.append((domain_user,), (user,)) # log user as well
              log.Engine.run(context)
 
           else:
             # raise custom exception!!!
              return context.error('user', 'user_not_active')      
            
        transaction()
         
        return context
      
    # Uklanja postojeceg usera iz domene
    @classmethod
    def remove(cls, context):
  
       @ndb.transactional(xg=True)
       def transaction():
          
          entity_key = context.input.get('key')            
          entity = entity_key.get()
          
          from app.srv import auth
          
          user = auth.User.build_key(entity.key.id()).get()
          
          context.rule.entity = entity
          Engine.run(context)
          
          # if user can remove, or if the user can remove HIMSELF from the user role  
          if not executable(context):
             raise ActionDenied(context)
          
          entity.key.delete()
          
          user.domains.remove(ndb.Key(urlsafe=entity.key_namespace()))
          user.put() # should we log this removal of domains?
          
          context.log.entities.append((entity,), (user, ))
          log.Engine.run(context)
 
       transaction()
        
       return context
 
    # Prihvata poziv novog usera u domenu
    @classmethod
    def accept(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
           
           entity_key = context.input.get('key')            
           entity = entity_key.get()
           
           context.rule.entity = entity
           Engine.run(context)
           
           if not executable(context):
              raise ActionDenied(context)
           
           entity.state = 'accepted'
           entity.put()
           context.log.entities.append((entity,))
           log.Engine.run(context)
   
        transaction()
         
        return context
    
    # Azurira postojeceg usera u domeni
    @classmethod
    def update(cls, context):
       
          @ndb.transactional(xg=True)
          def transaction():
             
             entity_key = context.input.get('key')            
             entity = entity_key.get()
             
             context.rule.entity = entity
             Engine.run(context)
             
       
             if not executable(context):
                raise ActionDenied(context)
              
             domain_key = context.input.get('domain')
             domain = domain_key.get()
             
             get_roles = ndb.get_multi(context.input.get('roles')) 
             roles = []
             for role in get_roles:
                # avoid rogue roles
                if role.key.namespace() == domain.key_namespace:
                   roles.append(role.key) 
             
             entity.name = context.input.get('name')
             entity.roles = roles
             entity.put()
             
             context.log.entities.append((entity,))
             log.Engine.run(context)
       
          transaction()
           
          return context