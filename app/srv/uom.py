# -*- coding: utf-8 -*-
'''
Created on Jan 1, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import collections
import os

from xml.etree import ElementTree
from decimal import Decimal, ROUND_HALF_EVEN

from app import ndb
 
__SYSTEM_UNITS = collections.OrderedDict()
__SYSTEM_MEASUREMENTS = collections.OrderedDict()
__GET_UOM_CACHE = {}

def search_units(query=None, limit=400):
  ## missing search logic
  items = get_system_unit().values()[:limit]
  return items

def get_uom(unit_key):
  global __GET_UOM_CACHE
  if unit_key.urlsafe() in __GET_UOM_CACHE:
    return __GET_UOM_CACHE.get(unit_key.urlsafe())
  measurement = get_system_measurement(unit_key.parent())
  data = {'measurement' : measurement.name}
  unit = get_system_unit(unit_key)
  for unit_property_name, unit_property in unit._properties.items():
    data[unit_property._code_name] = unit_property._get_value(unit)
  new_uom = UOM(**data)
  __GET_UOM_CACHE[unit_key.urlsafe()] = new_uom
  return new_uom

def get_system_measurement(measurement_key=None):
  global __SYSTEM_MEASUREMENTS
  if measurement_key == None:
     return __SYSTEM_MEASUREMENTS
  return __SYSTEM_MEASUREMENTS.get(measurement_key.urlsafe())

def register_system_measurements(*measurements):
  global __SYSTEM_MEASUREMENTS
  for measurement in measurements:
    __SYSTEM_MEASUREMENTS[measurement.key.urlsafe()] = measurement

def get_system_unit(unit_key=None):
  global __SYSTEM_UNITS
  if unit_key == None:
    return __SYSTEM_UNITS
  return __SYSTEM_UNITS.get(unit_key.urlsafe())

def register_system_units(*units):
  global __SYSTEM_UNITS
  for unit in units:
    __SYSTEM_UNITS[unit.key.urlsafe()] = unit

def convert_value(value, value_uom, conversion_uom):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not isinstance(value_uom, (UOM, Unit)) or not isinstance(conversion_uom, (UOM, Unit)):
    raise Exception('not_value_uom_or_conversion_uom')
  if not hasattr(value_uom, 'rate') or not isinstance(value_uom.rate, Decimal):
    raise Exception('no_rate_in_value_uom')
  if not hasattr(conversion_uom, 'rate') or not isinstance(conversion_uom.rate, Decimal):
    raise Exception('no_rate_in_conversion_uom')
  if (value_uom.measurement == conversion_uom.measurement):
    return (value / value_uom.rate) * conversion_uom.rate
  else:
    raise Exception('incompatible_units')

def round_value(value, uom, rounding=ROUND_HALF_EVEN):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not isinstance(uom, (UOM, Unit)):
    raise Exception('not_uom')
  if not hasattr(uom, 'rounding') or not isinstance(uom.rounding, Decimal):
    raise Exception('no_rounding_in_uom')
  return (value / uom.rounding).quantize(Decimal('1.'), rounding=rounding) * uom.rounding

def format_value(value, uom, rounding=ROUND_HALF_EVEN):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not isinstance(uom, (UOM, Unit)):
    raise Exception('not_uom')
  if not hasattr(uom, 'digits') or not isinstance(uom.digits, (int, long)):
    raise Exception('no_digits_in_uom')
  places = Decimal(10) ** -uom.digits
  return (value).quantize(places, rounding=rounding)


class Measurement(ndb.BaseModel):
  
  _kind = 18
  # root
  # http://hg.tryton.org/modules/product/file/tip/uom.py#l16
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L81
  name = ndb.SuperStringProperty('1', required=True)


class Unit(ndb.BaseExpando):
  
  _kind = 19
  
  # ancestor Measurement
  # http://hg.tryton.org/modules/product/file/tip/uom.py#l28
  # http://hg.tryton.org/modules/product/file/tip/uom.xml#l63 - http://hg.tryton.org/modules/product/file/tip/uom.xml#l312
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L89
  # http://hg.tryton.org/modules/currency/file/tip/currency.py#l14
  # http://hg.tryton.org/modules/currency/file/tip/currency.xml#l107
  # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_currency.py#L32
  # http://en.wikipedia.org/wiki/ISO_4217
  # http://en.wikipedia.org/wiki/Systems_of_measurement#Units_of_currency
  # composite index: ancestor:no - active,name
  name = ndb.SuperStringProperty('1', required=True)
  symbol = ndb.SuperStringProperty('2', required=True, indexed=False) # Turn on index if projection query is required.
  rate = ndb.SuperDecimalProperty('3', required=True, indexed=False) # The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12).
  factor = ndb.SuperDecimalProperty('4', required=True, indexed=False) # The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12).
  rounding = ndb.SuperDecimalProperty('5', indexed=False) # Rounding Precision - digits=(12, 12).
  digits = ndb.SuperIntegerProperty('6', indexed=False)
  active = ndb.SuperBooleanProperty('7', default=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_measurement' : ndb.SuperComputedProperty(lambda self: self._get_measurement())
  }
  
  _expando_fields = {
                     'code' : ndb.SuperStringProperty('8', required=True),
                     'numeric_code' : ndb.SuperStringProperty('9'),
                     'grouping' : ndb.SuperIntegerProperty('10', repeated=True),
                     'decimal_separator' : ndb.SuperStringProperty('11', required=True),
                     'thousands_separator' : ndb.SuperStringProperty('12'),
                     'positive_sign_position' : ndb.SuperIntegerProperty('13', required=True),
                     'negative_sign_position' : ndb.SuperIntegerProperty('14', required=True),
                     'positive_sign' : ndb.SuperStringProperty('15'),
                     'negative_sign' : ndb.SuperStringProperty('16'),
                     'positive_currency_symbol_precedes' : ndb.SuperBooleanProperty('17', default=True),
                     'negative_currency_symbol_precedes' : ndb.SuperBooleanProperty('18', default=True),
                     'positive_separate_by_space' : ndb.SuperBooleanProperty('19', default=True),
                     'negative_separate_by_space' : ndb.SuperBooleanProperty('20', default=True),
                     }
  
  def _get_measurement(self):
    return get_system_measurement(self.key.parent())


class UOM(ndb.BaseExpando):
  
  _kind = 72
  
  # Local structured property
  measurement = ndb.SuperStringProperty('1', required=True, indexed=False)
  name = ndb.SuperStringProperty('2', required=True, indexed=False)
  symbol = ndb.SuperStringProperty('3', required=True, indexed=False)
  rate = ndb.SuperDecimalProperty('4', required=True, indexed=False)
  factor = ndb.SuperDecimalProperty('5', required=True, indexed=False)
  rounding = ndb.SuperDecimalProperty('6', required=True, indexed=False)
  digits = ndb.SuperIntegerProperty('7', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
                     'code' : ndb.SuperStringProperty('8', required=True),
                     'numeric_code' : ndb.SuperStringProperty('9'),
                     'grouping' : ndb.SuperIntegerProperty('10', repeated=True),
                     'decimal_separator' : ndb.SuperStringProperty('11', required=True),
                     'thousands_separator' : ndb.SuperStringProperty('12'),
                     'positive_sign_position' : ndb.SuperIntegerProperty('13', required=True),
                     'negative_sign_position' : ndb.SuperIntegerProperty('14', required=True),
                     'positive_sign' : ndb.SuperStringProperty('15'),
                     'negative_sign' : ndb.SuperStringProperty('16'),
                     'positive_currency_symbol_precedes' : ndb.SuperBooleanProperty('17', default=True),
                     'negative_currency_symbol_precedes' : ndb.SuperBooleanProperty('18', default=True),
                     'positive_separate_by_space' : ndb.SuperBooleanProperty('19', default=True),
                     'negative_separate_by_space' : ndb.SuperBooleanProperty('20', default=True),
                     }

def build_uom():
  with file(os.path.join(os.path.abspath('.'), 'tryton_uom.xml')) as f:
    tree = ElementTree.fromstring(f.read())
    root = tree.findall('data')
    measurements = []
    uoms = []
    for child in root[0]:
      if child.attrib.get('model') == 'product.uom.category':
        the_id = child.attrib.get('id')[8:]
        new_uom_category = {'id' : the_id}
        for child2 in child:
          new_uom_category['name'] = child2.text
        measurements.append(new_uom_category)
        
      if child.attrib.get('model') == 'product.uom':
         new_uom = {'id' : child.attrib.get('id')[4:]}
         new_uom_data = {}
         for child2 in child:
           new_uom_data[child2.attrib.get('name')] = child2
         
         rounding = new_uom_data.get('rounding')
         digits = new_uom_data.get('digits')
         if rounding != None:
            rounding = Decimal(eval(rounding.attrib.get('eval')))
         if digits != None:
            digits = long(eval(digits.attrib.get('eval')))
            
         new_uom.update({'name' : new_uom_data['name'].text, 
                         'active' : True,
                         'symbol' : new_uom_data['symbol'].text,
                         'parent' : Measurement.build_key(new_uom_data['category'].attrib.get('ref')[8:]),
                         'factor' : Decimal(eval(new_uom_data['factor'].attrib.get('eval'))),
                         'rate' : Decimal(eval(new_uom_data['rate'].attrib.get('eval'))),
                         'rounding' : rounding,
                         'digits' : digits,
                         })
         uoms.append(new_uom)
         
  return (measurements, uoms)


def build_currency():
  with file(os.path.join(os.path.abspath('.'), 'tryton_currency.xml')) as f:
    tree = ElementTree.fromstring(f.read())
    root = tree.findall('data')
    measurements = [{'name' : 'Currency', 'id' : 'currency'}]
    uoms = []
    
    def __text(item, key, op=None):
      if op == None:
        op = str
      gets = item.get(key)
      if gets != None:
        return op(gets.text)
      return gets
    
    def __eval(item, key):
      gets = item.get(key)
      if gets != None:
        return eval(gets.attrib.get('eval'))
      return gets
          
    for child in root[1]:
  
      if child.attrib.get('model') == 'currency.currency':
         """
            <field name="name">Swiss Franc</field>
            <field name="code">CHF</field>
            <field name="numeric_code">756</field>
            <field name="symbol">CHF</field>
            <field name="rounding" eval="Decimal('0.01')"/>
            <field name="digits" eval="2"/>
            <field name="p_cs_precedes" eval="False"/>
            <field name="n_cs_precedes" eval="False"/>
            <field name="p_sep_by_space" eval="True"/>
            <field name="n_sep_by_space" eval="True"/>
            <field name="mon_grouping">[3, 3, 0]</field>
            <field name="mon_decimal_point">,</field>
            <field name="mon_thousands_sep"> </field>
            <field name="p_sign_posn" eval="1"/>
            <field name="n_sign_posn" eval="1"/>
            <field name="negative_sign">-</field>
            <field name="positive_sign"></field>
            
         """
         new_uom = {'id' : child.attrib.get('id')}
         new_uom_data = {}
         for child2 in child:
           new_uom_data[child2.attrib.get('name')] = child2
           
         rounding = new_uom_data.get('rounding')
         digits = new_uom_data.get('digits')
         grouping = new_uom_data.get('mon_grouping')
        
         if rounding != None:
            rounding = Decimal(eval(rounding.attrib.get('eval')))
         if digits != None:
            digits = long(eval(digits.attrib.get('eval')))
         if grouping != None:
           grouping = eval(grouping.text)
         else:
           grouping = []
     
         new_uom.update({
           'parent' : Measurement.build_key('currency'),
           'name' : new_uom_data['name'].text,
           'code' : new_uom_data['code'].text,
           'numeric_code' : new_uom_data['numeric_code'].text,
           'symbol' : new_uom_data['symbol'].text,
           'rounding' : rounding,
           'digits' : digits,
           'grouping' : grouping,
           'decimal_separator' : __text(new_uom_data, 'mon_decimal_point'),
           'thousands_separator' : __text(new_uom_data, 'mon_thousands_sep'),
           'positive_sign_position' : __eval(new_uom_data, 'p_sign_posn'),
           'negative_sign_position' : __eval(new_uom_data, 'n_sign_posn'),
           'positive_sign' : __text(new_uom_data, 'positive_sign'),
           'negative_sign' : __text(new_uom_data, 'negative_sign'),
           'positive_currency_symbol_precedes' : __eval(new_uom_data, 'p_cs_precedes'),
           'negative_currency_symbol_precedes' : __eval(new_uom_data, 'n_cs_precedes'),
           'positive_separate_by_space' : __eval(new_uom_data, 'p_sep_by_space'),
           'negative_separate_by_space' : __eval(new_uom_data, 'n_sep_by_space'),
           'active' : True,
         })
         uoms.append(new_uom)
         
  return (measurements, uoms)
          
        
__measurements, __units = build_uom()        
register_system_measurements(*(Measurement(**d) for d in __measurements))
register_system_units(*(Unit(**d) for d in __units))

__measurements, __units = build_currency()        
register_system_measurements(*(Measurement(**d) for d in __measurements))
register_system_units(*(Unit(**d) for d in __units))