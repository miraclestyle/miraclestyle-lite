# neke klase u transaction.py nisu fixane, tipa umesto ndb.BaseExpando stoji ndb.BaseModel pa to na kraju fixati
# danas trebamo da zavrsimo funkcionalne engine, da bi sutra mogli da pocnemo da pravimo pluginove i permissije

# i ovaj field se treba za sada drzati u transaction.py
# done!
class Address(ndb.Expando):
    
    # LocalStructuredProperty model
    name = ndb.StringProperty('1', required=True, indexed=False)
    country = ndb.StringProperty('2', required=True, indexed=False)
    country_code = ndb.StringProperty('3', required=True, indexed=False)
    region = ndb.StringProperty('4', required=True, indexed=False)
    region_code = ndb.StringProperty('5', required=True, indexed=False)
    city = ndb.StringProperty('6', required=True, indexed=False)
    postal_code = ndb.StringProperty('7', required=True, indexed=False)
    street_address = ndb.StringProperty('8', required=True, indexed=False)
    _default_indexed = False
    pass
    # Expando
    # street_address2 = ndb.StringProperty('9') # ovo polje verovatno ne treba, s obzirom da je u street_address dozvoljeno 500 karaktera 
    # email = ndb.StringProperty('10')
    # telephone = ndb.StringProperty('11')
    

# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

class Engine:
  
  @classmethod
  def final_check(cls, context):
    pass
  
  @classmethod
  def run(cls, context):
    
    # datastore system
    #for role in context.user.roles:
      #if role.namespace() == namespace or role.kind() == Role._get_kind() and role.active:
        #rules.append(role)
    
    entity = context.entity
    if hasattr(entity, '_rule') and isinstance(entity._rule, Rule):
       entity._rule.run(context)
    
    cls.final_check(context) # ova funkcija proverava sva polja koja imaju vrednosti None i pretvara ih u False
 
# done!
class Role(ndb.Model):
    
    # root (namespace Domain)
    # ovaj model ili LocalRole se jedino mogu koristiti u runtime i cuvati u datastore, dok se GlobalRole moze samo programski iskoristiti
    # ovo bi bilo tlacno za resurse ali je jedini preostao feature sa kojim 
    # bi ovaj rule engine koncept prevazisao sve ostale security modele
    # parent_record = ndb.SuperKeyProperty('1', kind='44', indexed=False) 
    # complete_name = ndb.SuperTextProperty('3')
    name = ndb.StringProperty('1', required=True)
    active = ndb.BooleanProperty('2', default=True)
    permissions = ndb.PickleProperty('3', required=True, compressed=False) # [permission1, permission2,...]
    
    # treba da postoji validator da proverava prilikom put()-a da li su u permissions listi instance Permission klase
    # napr:
    #def _pre_put_hook(self):
    #for perm in self.permissions:
        #if not isinstance(perm, Permission):
           #raise ValueError('Expected instance of Permission, got %r' % perm)
    
    def run(self, context):
 
    for permission in self.permissions:
        permission.run(self, context)
        

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
    
    