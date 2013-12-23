# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

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
  def final_check(cls, context):
      pass
  
  @classmethod
  def decide(cls, permissions, strict):
    calc = {}
    for action, properties in permissions.items():
          for prop, value in properties.items():
            if len(value):
              if (strict):
                if all(value):
                   calc[action][prop] = True
                else:
                   calc[action][prop] = False
              elif any(value):
                calc[action][prop] = True
              else:
                calc[action][prop] = False
            else:
              calc[action][prop] = None
              
    return calc
  
  @classmethod
  def run(cls, context, strict=False):
    
    # datastore system
    
    #example
    
    roles = Role.query() # gets some roles
    for role in roles:
        role.run(context)
        
    # copy 
    local_permissions = context.entity._rule_action_permissions.copy()
    
    # empty
    context.entity._rule_action_permissions = {}
 
    entity = context.entity
    if hasattr(entity, '_global_role') and isinstance(entity._global_role, Role):
       entity._global_role.run(context)
    
    # copy   
    global_permissions = context.entity._rule_action_permissions.copy()
    
    # empty
    context.entity._rule_action_permissions = {}
     
    global_permissions_calc = cls.decide(global_permissions, strict)
    
    # if any local perms, process them
    if local_permissions:
       local_permissions_calc = cls.decide(local_permissions, strict)
       
       # iterate over local permissions, and override them with the global permissions, if any
       for action, properties in local_permissions_calc.items():
          for prop, value in properties.items():
              if action in global_permissions_calc:
                 if prop in global_permissions_calc[action]:
                    gc = global_permissions_calc[action][prop]
                    if gc is not None and gc != value:
                          local_permissions_calc[action][prop] = gc
                  
              if local_permissions_calc[action][prop] is None:
                 local_permissions_calc[action][prop] = False
                 
       # make sure that global perms are always present
       for action, properties in global_permissions_calc.items():
          if action not in local_permissions_calc:
            for prop, value in properties.items():
              if prop not in local_permissions_calc[action]:
                 local_permissions_calc[action][prop] = value
            
       finals = local_permissions_calc
    
    # otherwise just use global permissions    
    else:
       for action, properties in global_permissions_calc.items():
          for prop, value in properties.items():
            if value is None:
               value = False
            global_permissions_calc[action][prop] = value
            
       finals = global_permissions_calc
       
    # finals variable contains mapped final[action]['executable'] flag
           
    cls.final_check(context) # ova funkcija proverava sva polja koja imaju vrednosti None i pretvara ih u False
 

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
    
    if not hasattr(context.entity, '_rule_action_permissions'):
       context.entity._rule_action_permissions = {} 
    
    if (self.kind == context.entity.get_rule_kind()) and (self.action in context.entity._rule_actions) and (eval(self.condition)) and (self.executable != None):
       
       if self.action not in context.entity._rule_action_permissions:
          context.entity._rule_action_permissions[self.action] = {'executable' : []}
          
       context.entity._rule_action_permissions[self.action]['executable'].append(self.executable)


class FieldPermission(Permission):
  
  
  def __init__(self, kind, field, writable=None, visible=None, required=None, condition=None):
    
    self.kind = kind
    self.field = field
    self.writable = writable
    self.visible = visible
    self.required = required
    self.condition = condition
    
  def run(self, context):
    
    if not hasattr(context.entity, '_rule_field_permissions'):
       context.entity._rule_field_permissions = {} 
       
    if self.field not in context.entity._rule_field_permissions:
       context.entity._rule_field_permissions[self.field] = {'writable' : [], 'visible' : [], 'required' : []}
          
    if (self.kind == context.entity.get_rule_kind()) and (self.field in context.entity._rule_properties) and (eval(self.condition)):
      if (self.writable != None):
        context.entity._rule_field_permissions[self.field]['writable'].append(self.writable)
      if (self.visible != None):
        context.entity._rule_field_permissions[self.field]['visible'].append(self.visible)
      if (self.required != None):
        context.entity._rule_field_permissions[self.field]['required'].append(self.required)
 
          