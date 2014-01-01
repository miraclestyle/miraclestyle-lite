# -*- coding: utf-8 -*-
'''
Created on Jan 1, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import collections
from decimal import Decimal

from app import ndb

__SYSTEM_UNITS = collections.OrderedDict()

def get_system_units(unit_key):

    global __SYSTEM_UNITS
    
    return __SYSTEM_UNITS.get(unit_key.urlsafe())
  
def register_system_units(*args):
  
    global __SYSTEM_UNITS
    
    for unit in args:
       __SYSTEM_UNITS[unit.key.urlsafe()] = unit
 
def format_value(value, uom):
    if (uom):
        if (isinstance(uom, str)):
            return Decimal(format(Decimal(value), uom))
        else:
            return Decimal(format(Decimal(value), '.' + uom.digits + 'f'))
    else:
        return Decimal(value)
  
def convert_value(value, from_uom, to_uom):
    pass
 
# done!
class Unit(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 19
    
    # ancestor ProductUOMCategory
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l28
    # http://hg.tryton.org/modules/product/file/tip/uom.xml#l63 - http://hg.tryton.org/modules/product/file/tip/uom.xml#l312
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L89
    # mozda da ovi entiteti budu non-deletable i non-editable ??
    # composite index: ancestor:no - active,name
    name = ndb.SuperStringProperty('1', required=True)
    symbol = ndb.SuperStringProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    rate = ndb.SuperDecimalProperty('3', required=True, indexed=False)# The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12)
    factor = ndb.SuperDecimalProperty('4', required=True, indexed=False)# The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12)
    rounding = ndb.SuperDecimalProperty('5', required=True, indexed=False)# Rounding Precision - digits=(12, 12)
    digits = ndb.SuperIntegerProperty('6', required=True, indexed=False)
    active = ndb.SuperBooleanProperty('7', default=True)
    
    EXPANDO_FIELDS = {
        'code' : ndb.SuperStringProperty('8', required=True, indexed=False),# ukljuciti index ako bude trebao za projection query
        'numeric_code' : ndb.SuperStringProperty('9', indexed=False),
        'grouping' : ndb.SuperStringProperty('10', required=True, indexed=False),
        'decimal_separator' : ndb.SuperStringProperty('11', required=True, indexed=False),
        'thousands_separator' : ndb.SuperStringProperty('12', indexed=False),
        'positive_sign_position' : ndb.SuperIntegerProperty('13', required=True, indexed=False),
        'negative_sign_position' : ndb.SuperIntegerProperty('14', required=True, indexed=False),
        'positive_sign' : ndb.SuperStringProperty('15', indexed=False),
        'negative_sign' : ndb.SuperStringProperty('16', indexed=False),
        'positive_currency_symbol_precedes' : ndb.SuperBooleanProperty('17', default=True, indexed=False),
        'negative_currency_symbol_precedes' : ndb.SuperBooleanProperty('18', default=True, indexed=False),
        'positive_separate_by_space' : ndb.SuperBooleanProperty('19', default=True, indexed=False),
        'negative_separate_by_space' : ndb.SuperBooleanProperty('20', default=True, indexed=False),
    }
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @classmethod
    def list(cls, values, **kwds):
        response = ndb.Response()
        response['items'] = cls.query().fetch()
        return response

    
    @classmethod
    def delete(cls, values):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
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

    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls, convert=[ndb.SuperKeyProperty('measurement', kind=Measurement, required=create)])
            
            if response.has_error():
               return response
             
            entity = cls.prepare(create, values, parent=values.get('measurement'))
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response
    

    
# done!
class Measurement(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 18
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l16
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L81
    # mozda da ovi entiteti budu non-deletable i non-editable ??
    name = ndb.SuperStringProperty('1', required=True)
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }

    @classmethod
    def delete(cls, values):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
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

    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls, only=('name',))
            
            if response.has_error():
               return response
             
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response
      

class UOM(ndb.BaseExpando):
 
    
    # Local structured
    measurement = ndb.SuperStringProperty('1', required=True)
    name = ndb.SuperStringProperty('2', required=True)
    symbol = ndb.SuperStringProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    rate = ndb.SuperDecimalProperty('4', required=True, indexed=False)# The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12)
    factor = ndb.SuperDecimalProperty('5', required=True, indexed=False)# The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12)
    rounding = ndb.SuperDecimalProperty('6', required=True, indexed=False)# Rounding Precision - digits=(12, 12)
    digits = ndb.SuperIntegerProperty('7', required=True, indexed=False)
    
    EXPANDO_FIELDS = {
        'code' : ndb.SuperStringProperty('8', required=True, indexed=False),# ukljuciti index ako bude trebao za projection query
        'numeric_code' : ndb.SuperStringProperty('9', indexed=False),
        'grouping' : ndb.SuperStringProperty('10', required=True, indexed=False),
        'decimal_separator' : ndb.SuperStringProperty('11', required=True, indexed=False),
        'thousands_separator' : ndb.SuperStringProperty('12', indexed=False),
        'positive_sign_position' : ndb.SuperIntegerProperty('13', required=True, indexed=False),
        'negative_sign_position' : ndb.SuperIntegerProperty('14', required=True, indexed=False),
        'positive_sign' : ndb.SuperStringProperty('15', indexed=False),
        'negative_sign' : ndb.SuperStringProperty('16', indexed=False),
        'positive_currency_symbol_precedes' : ndb.SuperBooleanProperty('17', default=True, indexed=False),
        'negative_currency_symbol_precedes' : ndb.SuperBooleanProperty('18', default=True, indexed=False),
        'positive_separate_by_space' : ndb.SuperBooleanProperty('19', default=True, indexed=False),
        'negative_separate_by_space' : ndb.SuperBooleanProperty('20', default=True, indexed=False),
    }

