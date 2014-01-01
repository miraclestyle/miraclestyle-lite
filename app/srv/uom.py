# -*- coding: utf-8 -*-
'''
Created on Jan 1, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import collections
from decimal import Decimal

from app import ndb

__SYSTEM_UNITS = collections.OrderedDict()
__SYSTEM_MEASUREMENTS = collections.OrderedDict()

def get_uom(unit_key):
  
  measurement = get_system_measurements(unit_key.parent())
  
  data = {'measurement' : measurement.name}
  
  unit = get_system_units(unit_key)
  
  for unit_property_name, unit_property in unit._properties.items():
      data[unit_property._code_name] = unit_property._get_value(unit)
  
  return UOM(**data)
    
def get_system_measurements(measurement_key):

    global __SYSTEM_MEASUREMENTS
    
    return __SYSTEM_MEASUREMENTS.get(measurement_key.urlsafe())
  
def register_system_measurements(*args):
  
    global __SYSTEM_MEASUREMENTS
    
    for measurement in args:
       __SYSTEM_MEASUREMENTS[measurement.key.urlsafe()] = measurement

def get_system_units(unit_key):

    global __SYSTEM_UNITS
    
    return __SYSTEM_UNITS.get(unit_key.urlsafe())
  
def register_system_units(*args):
  
    global __SYSTEM_UNITS
    
    for unit in args:
       __SYSTEM_UNITS[unit.key.urlsafe()] = unit
 
def format_value(value, uom):
    if not isinstance(uom, UOM):
       raise Exception('Expected instance of UOM got %r' % uom)
    return Decimal(format(Decimal(value), '.' + uom.digits + 'f'))
  
def convert_value(value, from_uom, to_uom):
    pass
 
# done!
class Unit(ndb.BaseExpando):
    
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
 

    
# done!
class Measurement(ndb.BaseModel):
    
    KIND_ID = 18
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l16
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L81
    # mozda da ovi entiteti budu non-deletable i non-editable ??
    name = ndb.SuperStringProperty('1', required=True)
 
      

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

