# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

class Context:
  
  def __init__(self, action, entity, args):
    
      self.action = action #-- not sure if this should be mapped with something to get `context.id` ? or use raw name
      self.entity = entity

class Engine:
  
  @classmethod
  def final_check(cls, context):
    pass
  
  @classmethod
  def run(cls, context):
    
    # datastore system
    
    entity = context.entity
    if hasattr(entity, '_rule') and isinstance(entity._rule, Rule):
       entity._rule.run(context)
    
    cls.final_check(context) # ova funkcija proverava sva polja koja imaju vrednosti None i pretvara ih u False
 
 
class Permission():
  pass


class Rule():
  
  def __init__(self, permissions):
    self.permissions = permissions
 

class GlobalRule(Rule):
  
  def __init__(self, *args, **kwargs):
      self.override = True
      super(Rule, self).__init__(*args, **kwargs)
  
  def run(self, context):
 
    for permission in self.permissions:
        if isinstance(permission, Permission):
           permission.run(self, context)


class LocalRule(Rule):
  
  def run(self, context):
 
    for permission in self.permissions:
      if isinstance(permission, Permission):
         permission.run(self, context)
  
  
class FieldPermission(Permission):
  
  
  def __init__(self, kind, field, writable=False, visible=False, condition=None):
    
    self.kind = kind
    self.field = field
    self.writable = writable
    self.visible = visible
    self.condition = condition
    
  def run(self, context):
    
    if (self.kind == context.entity._get_kind()) and (self.field in context.entity._properties) and (eval(self.condition)):
      if (context.overide):
        if (self.writable != None):
          context.entity._field_permissions[self.field] = {'writable': self.writable}
        if (self.visible != None):
          context.entity._field_permissions[self.field] = {'visible': self.visible}
      else:
        if (context.entity._field_permissions[self.field]['writable'] == None) and (self.writable != None):
          context.entity._field_permissions[self.field] = {'writable': self.writable}
        if (context.entity._field_permissions[self.field]['visible'] == None) and (self.visible != None):
          context.entity._field_permissions[self.field] = {'visible': self.visible}
    