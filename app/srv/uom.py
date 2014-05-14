# -*- coding: utf-8 -*-
'''
Created on Jan 1, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from decimal import Decimal, ROUND_HALF_EVEN

from app import ndb
from app.srv.event import Action
from app.srv.rule import ActionPermission, FieldPermission, GlobalRole
from app.plugins import common, callback, rule, uom
  
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
  
  _use_cache = True
  _use_memcache = True
  
  # root
  # http://hg.tryton.org/modules/product/file/tip/uom.py#l16
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L81
  name = ndb.SuperStringProperty('1', required=True)


class Unit(ndb.BaseExpando):
  
  _kind = 19
  
  _use_cache = True
  _use_memcache = True
  
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
  rate = ndb.SuperDecimalProperty('3', indexed=False) # The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12).
  factor = ndb.SuperDecimalProperty('4', indexed=False) # The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12).
  rounding = ndb.SuperDecimalProperty('5', indexed=False) # Rounding Precision - digits=(12, 12).
  digits = ndb.SuperIntegerProperty('6', indexed=False)
  active = ndb.SuperBooleanProperty('7', default=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    
  }
  
  _expando_fields = {
   'code' : ndb.SuperStringProperty('8', required=True),
   'numeric_code' : ndb.SuperStringProperty('9'),
   'grouping' : ndb.SuperIntegerProperty('10', repeated=True),
   'decimal_separator' : ndb.SuperStringProperty('11'),
   'thousands_separator' : ndb.SuperStringProperty('12'),
   'positive_sign_position' : ndb.SuperIntegerProperty('13'),
   'negative_sign_position' : ndb.SuperIntegerProperty('14'),
   'positive_sign' : ndb.SuperStringProperty('15'),
   'negative_sign' : ndb.SuperStringProperty('16'),
   'positive_currency_symbol_precedes' : ndb.SuperBooleanProperty('17', default=True),
   'negative_currency_symbol_precedes' : ndb.SuperBooleanProperty('18', default=True),
   'positive_separate_by_space' : ndb.SuperBooleanProperty('19', default=True),
   'negative_separate_by_space' : ndb.SuperBooleanProperty('20', default=True),
  }
  
  
  _global_role = GlobalRole(permissions=[
                   ActionPermission('19', Action.build_key('19', 'update_currency').urlsafe(), True, "context.user._root_admin"),
                   ActionPermission('19', Action.build_key('19', 'update_unit').urlsafe(), True, "context.user._root_admin"),
                   ActionPermission('19', Action.build_key('19', 'search').urlsafe(), True, "True"),
                 ])
  
  _actions = [
    Action(key=Action.build_key('19', 'update_currency'),
             arguments={},
             _plugins=[
              common.Context(),
              common.Prepare(domain_model=False),
              rule.Prepare(skip_user_roles=True, strict=False),
              rule.Exec(),
              uom.CurrencyUpdate(),
            ]             
     ), 
    Action(key=Action.build_key('19', 'update_unit'),
             arguments={},
             _plugins=[
              common.Context(),
              common.Prepare(domain_model=False),
              rule.Prepare(skip_user_roles=True, strict=False),
              rule.Exec(),
              uom.UnitUpdate(),
            ]             
     ),      
    Action(
      key=Action.build_key('19', 'search'), # search_currency, search_units? should this be separated?
      arguments={},
      _plugins=[
       ]
      )         
  ]
 
 
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