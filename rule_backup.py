# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import collections

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, util, settings
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
     'my_magic_field' : ndb.SuperComputedProperty(lambda self: 'this field does magic!')
   }
 
   
   _global_role = rule.GlobalRole(permissions=[
                                  
                                  Action permissions:
                                  
                                  work very simple, its a key-value checking system with conditions
                                  rule.ActionPermission('0', event.Action.build_key('0-0').urlsafe(), True, "context variable available, valid any `simple` python expression"),
                                  
                                  
                                  Field permissions:
                              
                                  rule.FieldPermission('0', 'bar', True, True, 'True'), 
                                  
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
                                  
                                  rule.FieldPermission('0', 'bar.other.name', False, False, 'True'),
                                  
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


class DomainUserError(Exception):
  
  def __init__(self, message):
    self.message = {'domain_user': message}


class ActionDenied(Exception):
  
  def __init__(self, context):
    self.message = {'action_denied': context.action}


def _is_structured_field(field):
  """Checks if the provided field is instance of one of the structured properties,
  and if the '_modelclass' is set.
  
  """
  return isinstance(field, (ndb.SuperStructuredProperty, ndb.SuperLocalStructuredProperty)) and field._modelclass

def _parse_field(values, field):
  """Digs through the path for the "values" provided.
  It is assumed that "values" is either dictionary or object from which value can be obtained using __getattr__.
  
  """
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

def _check_field(context, field, properties):  # Not sure if 'properties' cause confusion, 'property' in this case is propetry of the field itself!
  """Internal helper to check if the field for provided rule context is
  either writable or invisible.
  
  """
  if context.rule.entity:
    # This arangement allows us to call parent functions in the manner like this: writable(context, ('field1', 'field2')).
    if not isinstance(properties, (tuple, list)):
      properties = (properties, )
    results = []
    for prop in properties:
      result = _parse_field(context.rule.entity._field_permissions, field)
      results.append(result[prop])
    return all(results)
  else:
    return False

def writable(context, field):
  """Checks if the field is writable for given context."""
  return _check_field(context, name, 'writable')

def visible(context, field):
  """Checks if the field is visible for given context."""
  return _check_field(context, name, 'visible')

def executable(context):
  """Checks if the action is executable for given context."""
  if context.rule.entity:
    return context.rule.entity._action_permissions[context.action.key.urlsafe()]['executable']
  else:
    return False

def write(entity, values):
  entity_fields = entity.get_fields()
  for field_key, field_value in values.items():
    if field_key in entity_fields:  # Check if the value is in entities field list.
      field = entity_fields.get(field_key)
      writable = entity._field_permissions[field_key]['writable']
      _write_helper(entity._field_permissions, entity, field_key, field, field_value, is_writable=writable)

# revision stop!
def _write_helper(field_permissions, entity, field_key, field, field_value, parent_field_key=None, parent_field=None, is_writable=None):
  
  if is_structured_property(field):
  
     util.logger('is structured - recursion %s.%s' % (entity.__class__.__name__, field_key))
     
     if field._repeated and isinstance(entity, list):
        util.logger('got list as entity, recurse it' % entity)
        for ent in entity:
           for new_field_key, new_field in field.get_model_fields().items():
               new_field_value = getattr(ent, field_key)
               _write_helper(field_permissions[field_key], ent, new_field_key, new_field, new_field_value, field_key, field, field_permissions[field_key]['writable'])
        return
      
     structured_value = getattr(entity, field_key)
 
     for new_field_key, new_field in field.get_model_fields().items():
         _write_helper(field_permissions[field_key], structured_value, new_field_key, new_field, field_value, field_key, field, field_permissions[field_key]['writable'])
   
  else:
    if (field_key in field_permissions) and (field_permissions[field_key]['writable']):
       
       if parent_field and parent_field._repeated:
          if isinstance(entity, list):
             for i,field_value_item in enumerate(field_value):
                 try:
                   already = entity[i]
                   far_key = getattr(field_value_item, field_key)
                   setattr(already, field_key, far_key)
                   util.logger('repeated set - %s.%s=%s' % (already.__class__.__name__, field_key, far_key))
                 except IndexError:
                   entity.append(field_value_item)
                   util.logger('appending new %s to %s' % (field_value_item, entity.__class__.__name__))
                   
             return
           
       util.logger('not structured - setting %s.%s' % (entity.__class__.__name__, field_key))
       
       try:
         setattr(entity, field_key, field_value)
       except ndb.ComputedPropertyError:
         pass
              

def _read_helper(field_permissions, operator, field_key, field):
 
  if is_structured_property(field):
      
     structured_field_value = getattr(operator, field_key)
     
     if field._repeated and isinstance(structured_field_value, list):
        for op in structured_field_value:
           initial_fields = op.get_fields()
           initial_fields.update(dict([(p._code_name, p) for _, p in op._properties.items()]))
           for new_field_key, new_field in initial_fields.items():
              _read_helper(field_permissions[field_key], op, new_field_key, new_field)
     else:
        
       parent_structure = getattr(operator, field_key)
       
       if parent_structure is not None:
          initial_fields = parent_structure.get_fields()
          initial_fields.update(dict([(p._code_name, p) for _, p in parent_structure._properties.items()]))
         
          for new_field_key, new_field in initial_fields.items():
             _read_helper(field_permissions[field_key], parent_structure, new_field_key, new_field)
       
  else:
    if (not field_key in field_permissions) or (not field_permissions[field_key]['visible']):
       operator.remove_output(field_key) 
     
                      
def read(entity):
  
    # configures output variables for the provided entity with respect to rule engine. should the param be entity or context?
    entity_fields = entity.get_fields()
 
    for field_key, field in entity_fields.items():
        _read_helper(entity._field_permissions, entity, field_key, field)
        
    return entity

class Context():
  
  def __init__(self):
    self.entity = None

    
class Permission():
  """ Base class for all permissions """


class ActionPermission(Permission):
   
   
  def __init__(self, kind, action, executable=None, condition=None):
    
    if not isinstance(action, (tuple, list)):
      action = [action]
    
    self.kind = kind # entity kind identifier (entity._kind)
    self.action = action # action id (action.key.id()), or action key (action.key) ? ----- this could be a list
    self.executable = executable
    self.condition = condition
    
  def get_meta(self):
     return {'kind' : self.kind, 'action' : self.action,
             'executable' : self.executable, 'condition' : self.condition, 'type' : self.__class__.__name__}
    
  def run(self, role, context):
     
    for action in self.action:
        if (self.kind == context.rule.entity.get_kind()) and (action in context.rule.entity.get_actions()) and (safe_eval(self.condition, {'context' : context, 'action' : action})) and (self.executable != None):
           context.rule.entity._action_permissions[action]['executable'].append(self.executable)


class FieldPermission(Permission):
  
  
  def __init__(self, kind, field, writable=None, visible=None, condition=None):
    
    if not isinstance(field, (tuple, list)):
      field = [field]
    
    self.kind = kind # entity kind identifier (entity._kind)
    self.field = field # this must be a field code name from ndb property (field._code_name) ---- This could be a list?
    self.writable = writable
    self.visible = visible
    self.condition = condition
    
  def get_meta(self):
     return {'kind' : self.kind, 'field' : self.field, 'writable' : self.writable,
             'visible' : self.visible, 'condition' : self.condition, 'type' : self.__class__.__name__}
    
    
  def run(self, role, context):
     
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
  def prepare_fields(cls, field_permissions, fields, entity):
    # recursive method
 
    for field_key, field in fields.items():
        if is_structured_property(field): # isinstance(Struct, Local)
           if field_key not in field_permissions:
              field_permissions[field_key] = cls._prepare_fields_helper()
              
           new_fields = field.get_model_fields()
 
           if field._code_name in new_fields:
              new_fields.pop(field._code_name)
                
           cls.prepare_fields(field_permissions[field_key], new_fields, entity)
        else:
           field_permissions[field_key] = cls._prepare_fields_helper()

  @classmethod
  def prepare(cls, context):
    
    entity = context.rule.entity
    
    entity._field_permissions = {} 
    entity._action_permissions = {} 
 
    fields = entity.get_fields()
 
    cls.prepare_fields(entity._field_permissions, fields, entity)
 
    actions = entity.get_actions()
       
    for action_key in actions:
       entity._action_permissions[action_key] = {'executable' : []}
  
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
             cls._compile_local_data_helper(global_data_calc[element], local_data_calc[element], prop, _value_key, _value)
      else:   
        if element in global_data_calc:
           if prop in global_data_calc[element]:
              gc = global_data_calc[element][prop]
              if gc is not None and gc != value:
                    local_data_calc[element][prop] = gc
            
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
        if not context.auth.user._is_guest:
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
                context.callbacks.inputs.append({'action_key' : 'clean_roles', 'key' : domain_user.key.urlsafe(), 'action_model' : '8'})
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
      
      context.rule.entity.add_output('_action_permissions')
      context.rule.entity.add_output('_field_permissions')
   

class GlobalRole(Role):
      pass

class DomainRole(Role):
  
    _kind = 60
    
    _virtual_fields = {
     '_records': log.SuperLocalStructuredRecordProperty('60', repeated=True),                   
    }
  
    _global_role = GlobalRole(permissions=[
                                            ActionPermission('60', event.Action.build_key('60-0').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            ActionPermission('60', event.Action.build_key('60-3').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            ActionPermission('60', event.Action.build_key('60-1').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            ActionPermission('60', event.Action.build_key('60-2').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            
                                            ActionPermission('60', event.Action.build_key('60-3').urlsafe(), False, "context.rule.entity.key_id_str == 'admin'"),
                                            ActionPermission('60', event.Action.build_key('60-1').urlsafe(), False, "context.rule.entity.key_id_str == 'admin'"),
                                            
                                            ActionPermission('60', event.Action.build_key('60-3').urlsafe(), True, "not context.rule.entity.key_id_str == 'admin'"),
                                            ActionPermission('60', event.Action.build_key('60-1').urlsafe(), True, "not context.rule.entity.key_id_str == 'admin'"),
                                            ActionPermission('60', event.Action.build_key('60-6').urlsafe(), True, "context.auth.user._root_admin"),
                          
                                            FieldPermission('60', '_records.note', False, False, 'not context.auth.user._root_admin'),
                                            FieldPermission('60', '_records.note', True, True, 'context.auth.user._root_admin'),
                                            
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
                
       'search' : event.Action(id='60-2',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                              }
                             ),
                
       'read' : event.Action(id='60-4', 
                             arguments={
                               'key' : ndb.SuperKeyProperty(kind='60', required=True),
                             }),
       'prepare' : event.Action(id='60-5',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                              }
                             ),
       'read_records' : event.Action(id='60-6', 
                             arguments={
                               'key' : ndb.SuperKeyProperty(kind='60', required=True),
                               'next_cursor': ndb.SuperStringProperty(),
                             }),
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
  
          entity.key.delete()
          context.log.entities.append((entity, ))
          log.Engine.run(context)
          read(entity)
          context.output['entity'] = entity
  
        transaction()
           
        return context
      
    @classmethod
    def complete_save(cls, entity, context, create):
      
        context.rule.entity = entity
        Engine.run(context)
        
        if not executable(context):
           raise ActionDenied(context)
 
        permissions = context.input.get('permissions')
        set_permissions = []
        for permission in permissions:
          
            if permission.get('type') == 'FieldPermission':
               set_permissions.append(FieldPermission(permission.get('kind'),
                                                       permission.get('field'),
                                                       permission.get('writable'),
                                                       permission.get('visible'),
                                                       permission.get('condition')))
            elif permission.get('type') == 'ActionPermission':
              set_permissions.append(ActionPermission(permission.get('kind'),
                                                      permission.get('action'),
                                                      permission.get('executable'),
                                                      permission.get('condition')))
        
          
        values = {'name' : context.input.get('name'),
                  'active' : context.input.get('active'),
                  'permissions' : set_permissions,
                  }
        
        if create:
          entity.populate(**values)
        else:
          write(entity, values)
             
        entity.put()
        context.log.entities.append((entity,))
        log.Engine.run(context)
        read(entity)
        context.output['entity'] = entity
      
    @classmethod
    def create(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
          
            domain_key = context.input.get('domain')
      
            domain = domain_key.get()
            entity = cls(namespace=domain.key_namespace)
           
            cls.complete_save(entity, context, True)  
               
        transaction()
            
        return context
    
    @classmethod
    def update(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
        
            entity_key = context.input.get('key')
            entity = entity_key.get()
          
            cls.complete_save(entity, context, False)
           
        transaction()
            
        return context

    @classmethod
    def search(cls, context):
        
      domain_key = context.input.get('domain')
      domain = domain_key.get()
      
      context.rule.entity = cls(namespace=domain.key_namespace)
      Engine.run(context)
      
      if not executable(context):
        raise ActionDenied(context)
 
      urlsafe_cursor = context.input.get('next_cursor')
      cursor = Cursor(urlsafe=urlsafe_cursor)
      
      query = cls.query(namespace=domain.key_namespace).order(cls.name)
      
      entities, next_cursor, more = query.fetch_page(settings.DOMAIN_ADMIN_PER_PAGE, start_cursor=cursor)
   
      for entity in entities:
         context.rule.entity = entity
         Engine.run(context)
         read(entity)
      
      if next_cursor:
         next_cursor = next_cursor.urlsafe()
      
      context.output['entities'] = entities
      context.output['next_cursor'] = next_cursor
      context.output['more'] = more
   
      return context
    
    @classmethod
    def prepare(cls, context):
      
      domain_key = context.input.get('domain')
      domain = domain_key.get()
   
      entity = cls(namespace=domain.key_namespace)
      
      context.rule.entity = entity
      
      Engine.run(context)
      
      if not executable(context):
        raise ActionDenied(context)
   
      context.output['entity'] = entity
 
      return context
    
    @classmethod
    def read(cls, context):
      
      entity_key = context.input.get('key')
      entity = entity_key.get()
      
      context.rule.entity = entity
      
      Engine.run(context)
      
      if not executable(context):
        raise ActionDenied(context)
      
      read(entity)
      
      context.output['entity'] = entity
 
      return context
    
    @classmethod
    def read_records(cls, context):
      entity_key = context.input.get('key')
      next_cursor = context.input.get('next_cursor')
      entity = entity_key.get()
      context.rule.entity = entity
      Engine.run(context)
      if not executable(context):
        raise ActionDenied(context)
      entities, next_cursor, more = log.Record.get_records(entity, next_cursor)
      entity._records = entities
      read(entity)
      context.output['entity'] = entity
      context.output['next_cursor'] = next_cursor
      context.output['more'] = more
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
    
    _virtual_fields = {
     '_records': log.SuperLocalStructuredRecordProperty('8', repeated=True),                   
    }
    
    _global_role = GlobalRole(permissions=[
                                            ActionPermission('8', event.Action.build_key('8-0').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            
                                            ActionPermission('8', event.Action.build_key('8-1').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            ActionPermission('8', event.Action.build_key('8-1').urlsafe(), True, "(context.rule.entity.namespace_entity.state == 'active' and context.auth.user.key_id_str == context.rule.entity.key_id_str) and not (context.auth.user.key_id_str == context.rule.entity.namespace_entity.primary_contact.entity.key_id_str)"),
                                            ActionPermission('8', event.Action.build_key('8-1').urlsafe(), False, "(context.rule.entity.key_id_str == context.rule.entity.namespace_entity.primary_contact.entity.key_id_str)"),

                                            FieldPermission('8', 'roles', False, True, "(context.rule.entity.key_id_str == context.rule.entity.namespace_entity.primary_contact.entity.key_id_str)"),
                                         
                                            
                                            ActionPermission('8', event.Action.build_key('8-2').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active' or context.auth.user.key_id_str != context.rule.entity.key_id_str"),
                                            ActionPermission('8', event.Action.build_key('8-2').urlsafe(), True, "context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'invited' and context.auth.user.key_id_str == context.rule.entity.key_id_str"),
                                            
                                            ActionPermission('8', event.Action.build_key('8-3').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
                                            ActionPermission('8', event.Action.build_key('8-4').urlsafe(), True, "context.auth.user._is_taskqueue"),
                                            ActionPermission('8', event.Action.build_key('8-4').urlsafe(), False, "not context.auth.user._is_taskqueue"),
                                            ActionPermission('8', event.Action.build_key('8-8').urlsafe(), True, "context.auth.user._root_admin"),
                          
                                            FieldPermission('8', '_records.note', False, False, 'not context.auth.user._root_admin'),
                                            FieldPermission('8', '_records.note', True, True, 'context.auth.user._root_admin'),

                                          ])
    # unique action naming, possible usage is '_kind_id-manage'
    _actions = {
       'invite' : event.Action(id='8-0',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6'),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'email' : ndb.SuperStringProperty(required=True),
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
       'read' : event.Action(id='8-5', 
                             arguments={
                               'key' : ndb.SuperKeyProperty(kind='8', required=True),
                             }),
                
       'search' : event.Action(id='8-6',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6'),
                               }),
       'prepare' : event.Action(id='8-7',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6'),
                              }),
       'read_records' : event.Action(id='8-8', 
                             arguments={
                               'key' : ndb.SuperKeyProperty(kind='8', required=True),
                               'next_cursor': ndb.SuperStringProperty()
                             }),
                
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
      
    @classmethod
    def prepare(cls, context):
      
      domain_key = context.input.get('domain')
      domain = domain_key.get()
   
      entity = cls(namespace=domain.key_namespace)
      
      context.rule.entity = entity
      
      Engine.run(context)
      
      if not executable(context):
        raise ActionDenied(context)
   
      context.output['entity'] = entity
      context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
 
      return context
 
    # Poziva novog usera u domenu
    @classmethod
    def invite(cls, context):
        
        from app.srv import auth
        
        # operating on too many entity groups
        # All Datastore operations in a transaction must operate on entities in the same entity group 
        # This includes querying for entities by ancestor, retrieving entities by key, updating entities, and deleting entities.
        
        email = context.input.get('email')
        
        user = auth.User.query(auth.User.emails == email).get()
        
        if not user:
          raise DomainUserError('email_not_found')
        
        role_keys = context.input.get('roles')
        get_roles = ndb.get_multi(role_keys)
           
        domain_key = context.input.get('domain')
        domain = domain_key.get()
          
        already_invited = cls.build_key(user.key_id_str, namespace=domain.key_namespace).get()
           
        if already_invited:
          # raise custom exception!!!
          raise DomainUserError('already_invited') 
        
           
        entity = cls(id=user.key_id_str, namespace=domain.key_namespace)

        context.rule.entity = entity
        Engine.run(context)
             
        if not executable(context):
          raise ActionDenied(context)        
        
        @ndb.transactional(xg=True)
        def transaction():
 
           if user.state == 'active':
              roles = []
              for role in get_roles:
                  # avoid rogue roles
                  if role.key.namespace() == domain.key_namespace:
                     roles.append(role.key)
                     
              entity.populate(name=context.input.get('name'), state='invited', roles=roles)
           
              user.domains.append(domain.key)
              
              # write both entity, and user
              
              ndb.put_multi([entity, user])
              
              context.log.entities.append((entity,))
              context.log.entities.append((user,)) # log user as well
              
              log.Engine.run(context)
              read(entity)
              context.output['entity'] = entity
 
           else:
             # raise custom exception!!!
              raise DomainUserError('not_active')    
            
        transaction()
         
        return context
      
    # Uklanja postojeceg usera iz domene
    @classmethod
    def remove(cls, context):
       
       entity_key = context.input.get('key')            
       entity = entity_key.get()
      
       from app.srv import auth
      
       user = auth.User.build_key(long(entity.key.id())).get()
      
       context.rule.entity = entity
       Engine.run(context)    
 
       # if user can remove, or if the user can remove HIMSELF from the user role  
       if not executable(context):
         raise ActionDenied(context) 
  
       @ndb.transactional(xg=True)
       def transaction():
 
          entity.key.delete()
          
          user.domains.remove(ndb.Key(urlsafe=entity.key_namespace))
          user.put()
          
          context.log.entities.append((entity,))
          context.log.entities.append((user, ))
          
          log.Engine.run(context)
          read(entity)
          context.output['entity'] = entity
 
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
           Engine.run(context)
           
           domain = entity.namespace_entity
           
           entity.key.delete(use_datastore=False)
           
           context.rule.entity = domain
           Engine.run(context)
           
           read(entity)
           read(domain)
           
           context.output['entity'] = entity
           context.output['domain'] = domain
   
        transaction()
         
        return context
    
    # Azurira postojeceg usera u domeni
    @classmethod
    def update(cls, context):
      
          get_roles = ndb.get_multi(context.input.get('roles')) 
       
          @ndb.transactional(xg=True)
          def transaction():
             
             entity_key = context.input.get('key')            
             entity = entity_key.get()
             
             context.rule.entity = entity
             Engine.run(context)
              
             if not executable(context):
                raise ActionDenied(context)
              
            
             roles = []
             for role in get_roles:
                # avoid rogue roles
                if role.key.namespace() == entity.key_namespace:
                   roles.append(role.key) 
   
             values = {
              'name' : context.input.get('name'),
              'roles' : roles,
             }
             
             write(entity, values)
             
             entity.put()
             
             context.log.entities.append((entity,))
             log.Engine.run(context)
             read(entity)
             context.output['entity'] = entity
       
          transaction()
           
          return context
 
    
    @classmethod
    def read(cls, context):
      
      entity_key = context.input.get('key')
      entity = entity_key.get()
      
      context.rule.entity = entity
      
      Engine.run(context)
      
      if not executable(context):
        raise ActionDenied(context)
      
      read(entity)
      
      context.output['entity'] = entity
      context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
      
      return context
    
    
    @classmethod
    def search(cls, context):
        
      domain_key = context.input.get('domain')
      domain = domain_key.get()
      
      context.rule.entity = cls(namespace=domain.key_namespace)
      Engine.run(context)
      
      if not executable(context):
        raise ActionDenied(context)
 
      urlsafe_cursor = context.input.get('next_cursor')
      cursor = Cursor(urlsafe=urlsafe_cursor)
      
      query = cls.query(namespace=domain.key_namespace).order(cls.name)
      
      entities, next_cursor, more = query.fetch_page(settings.DOMAIN_ADMIN_PER_PAGE, start_cursor=cursor)
   
      for entity in entities:
         context.rule.entity = entity
         Engine.run(context)
         read(entity)
      
      if next_cursor:
         next_cursor = next_cursor.urlsafe()
      
      context.output['entities'] = entities
      context.output['next_cursor'] = next_cursor
      context.output['more'] = more
   
      return context
    
    @classmethod
    def read_records(cls, context):
      entity_key = context.input.get('key')
      next_cursor = context.input.get('next_cursor')
      entity = entity_key.get()
      context.rule.entity = entity
      Engine.run(context)
      if not executable(context):
        raise ActionDenied(context)
      entities, next_cursor, more = log.Record.get_records(entity, next_cursor)
      entity._records = entities
      read(entity)
      context.output['entity'] = entity
      context.output['next_cursor'] = next_cursor
      context.output['more'] = more
      return context
     
    @classmethod
    def selection_roles_helper(cls, namespace):
      return DomainRole.query(DomainRole.active == True, namespace=namespace).fetch()