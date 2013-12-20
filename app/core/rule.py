# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

class Context:
  
  def __init__(self, action, entity):
    
      self.action = action
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
 

class Rule():
  
  def __init__(self, permissions):
    for perm in permissions:
        if not isinstance(perm, Permission):
           raise ValueError('Expected instance of Permission, got %r' % perm)
   
    self.permissions = permissions
    
  def run(self, context):
 
    for permission in self.permissions:
        permission.run(self, context)
 

class GlobalRule(Rule):
  
  def __init__(self, *args, **kwargs):
      self.override = True
      super(Rule, self).__init__(*args, **kwargs)


class LocalRule(Rule):
  pass

    
class Permission():
  pass

  
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
    