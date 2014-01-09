# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.lib.safe_eval import safe_eval

def _check_field(context, name, key):
    if context.entity:
      # this is like this because we can use it like writable(context, ('field1', 'field2'))
      if not isinstance(key, (tuple, list)):
         key = (key, )
      checks = []
      for k in key:
          checks.append(context.entity._field_permissions[name][k])
      return all(checks)
    else:
      return False

def writable(context, name):
  return _check_field(context, name, 'writable')

def visible(context, name):
  return _check_field(context, name, 'visible')

def required(context, name):
  return _check_field(context, name, 'required')

def executable(context):
  if context.entity:
     return context.entity._action_permissions[context.event.key.id()]['executable']
  else:
     return False
  


class Context():
  
  def __init__(self):
    self.entity = None
    

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
    # napr:
    #def _pre_put_hook(self):
    #for perm in self.permissions:
        #if not isinstance(perm, Permission):
           #raise ValueError('Expected instance of Permission, got %r' % perm)
    
    def run(self, context):
        for permission in self.permissions:
            permission.run(self, context)
 


class Engine:
  
  @classmethod
  def prepare(cls, context):
    
    context.rule.entity._field_permissions = {} 
    context.rule.entity._action_permissions = {} 
 
    fields = context.rule.entity.get_fields()
 
    for field_key in fields:
       context.rule.entity._field_permissions[field_key] = {'writable' : [], 'visible' : [], 'required' : []}
    
    actions = context.rule.entity.get_actions()
       
    for action_key in actions:
       context.rule.entity._action_permissions[action_key] = {'executable' : []}
 
  @classmethod
  def decide(cls, data, strict):
    calc = {}
    for element, properties in data.items():
          for prop, value in properties.items():
            
            if element not in calc:
               calc[element] = {}
            
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
              
    return calc
  
  @classmethod
  def compile(cls, local_data, global_data, strict=False):
    
    global_data_calc = cls.decide(global_data, strict)
    
    # if any local data, process them
    if local_data:
       local_data_calc = cls.decide(local_data, strict)
       
       # iterate over local data, and override them with the global data, if any
       for element, properties in local_data_calc.items():
          for prop, value in properties.items():
              if element in global_data_calc:
                 if prop in global_data_calc[element]:
                    gc = global_data_calc[element][prop]
                    if gc is not None and gc != value:
                          local_data_calc[element][prop] = gc
                  
              if local_data_calc[element][prop] is None:
                 local_data_calc[element][prop] = False
                 
       # make sure that global data are always present
       for element, properties in global_data_calc.items():
          if element not in local_data_calc:
            for prop, value in properties.items():
              if prop not in local_data_calc[element]:
                 local_data_calc[element][prop] = value
            
       finals = local_data_calc
    
    # otherwise just use global data    
    else:
       for element, properties in global_data_calc.items():
          for prop, value in properties.items():
            if value is None:
               value = False
            global_data_calc[element][prop] = value
            
       finals = global_data_calc
       
    return finals
  
  @classmethod
  def run(cls, context, strict=False):
    
    # datastore system
    
    if context.rule.entity:
 
      # call prepare first, populates required dicts into the entity instance
      cls.prepare(context)
      
      # 
      roles = ndb.get_multi(context.auth.user.roles)
      for role in roles:
          role.run(context)
          
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
   

class GlobalRole(Role):
  
  overide = ndb.BooleanProperty('2', default=True)
  

class LocalRole(Role):
  pass

    
class Permission():
  pass


class ActionPermission(Permission):
  
  
  def __init__(self, kind, action, executable=None, condition=None):
    
    self.kind = kind
    self.action = action
    self.executable = executable
    self.condition = condition
    
  def run(self, role, context):
     
    if (self.kind == context.rule.entity.get_kind()) and (self.action in context.rule.entity.get_actions()) and (safe_eval(self.condition, {'context' : context})) and (self.executable != None):
       context.rule.entity._action_permissions[self.action]['executable'].append(self.executable)


class FieldPermission(Permission):
  
  
  def __init__(self, kind, field, writable=None, visible=None, required=None, condition=None):
    
    self.kind = kind
    self.field = field # this must be a field name from ndb.Property(name='this name')
    self.writable = writable
    self.visible = visible
    self.required = required
    self.condition = condition
    
  def run(self, context):
 
    if (self.kind == context.rule.entity.get_kind()) and (self.field in context.rule.entity.get_fields()) and (safe_eval(self.condition, {'context' : context})):
      if (self.writable != None):
        context.rule.entity._field_permissions[self.field]['writable'].append(self.writable)
      if (self.visible != None):
        context.rule.entity._field_permissions[self.field]['visible'].append(self.visible)
      if (self.required != None):
        context.rule.entity._field_permissions[self.field]['required'].append(self.required)
          