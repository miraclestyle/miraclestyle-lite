# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

class Role(ndb.BaseModel):
    
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
  def run(cls, context):
    
    # datastore system
    
    entity = context.entity
    if hasattr(entity, '_global_role') and isinstance(entity._global_role, Role):
       entity._global_role.run(context)
    
    cls.final_check(context) # ova funkcija proverava sva polja koja imaju vrednosti None i pretvara ih u False
 

class GlobalRole(Role):
  
  overide = ndb.BooleanProperty('2', default=True)
  

class LocalRole(Role):
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
    