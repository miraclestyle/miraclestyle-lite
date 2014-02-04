# -*- coding: utf-8 -*-
'''
Created on Jan 1, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import collections
import re
from decimal import Decimal, ROUND_HALF_EVEN
from app import ndb


__SYSTEM_UNITS = collections.OrderedDict()
__SYSTEM_MEASUREMENTS = collections.OrderedDict()

def get_uom(unit_key):
  measurement = get_system_measurement(unit_key.parent())
  data = {'measurement' : measurement.name}
  unit = get_system_unit(unit_key)
  for unit_property_name, unit_property in unit._properties.items():
    data[unit_property._code_name] = unit_property._get_value(unit)
  return UOM(**data)

def get_system_measurement(measurement_key):
  global __SYSTEM_MEASUREMENTS
  return __SYSTEM_MEASUREMENTS.get(measurement_key.urlsafe())

def register_system_measurements(*measurements):
  global __SYSTEM_MEASUREMENTS
  for measurement in measurements:
    __SYSTEM_MEASUREMENTS[measurement.key.urlsafe()] = measurement

def get_system_unit(unit_key):
  global __SYSTEM_UNITS
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
  rounding = ndb.SuperDecimalProperty('5', required=True, indexed=False) # Rounding Precision - digits=(12, 12).
  digits = ndb.SuperIntegerProperty('6', required=True, indexed=False)
  active = ndb.SuperBooleanProperty('7', default=True)
  
  _expando_fields = {
                     'code' : ndb.SuperStringProperty('8', required=True, indexed=False), # Turn on index if projection query is required.
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


class UOM(ndb.BaseExpando):
  
  # Local structured property
  measurement = ndb.SuperStringProperty('1', required=True)
  name = ndb.SuperStringProperty('2', required=True)
  symbol = ndb.SuperStringProperty('3', required=True, indexed=False) # Turn on index if projection query is required.
  rate = ndb.SuperDecimalProperty('4', required=True, indexed=False) # The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12).
  factor = ndb.SuperDecimalProperty('5', required=True, indexed=False) # The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12).
  rounding = ndb.SuperDecimalProperty('6', required=True, indexed=False) # Rounding Precision - digits=(12, 12).
  digits = ndb.SuperIntegerProperty('7', required=True, indexed=False)
  
  _expando_fields = {
                     'code' : ndb.SuperStringProperty('8', required=True, indexed=False), # Turn on index if projection query is required.
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
