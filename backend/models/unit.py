# -*- coding: utf-8 -*-
'''
Created on Jan 1, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import orm, settings

from models.base import *
from plugins.base import *

from plugins.unit import *


class Unit(orm.BaseExpando):
  
  _kind = 17
  
  _use_record_engine = False
  _use_cache = True
  _use_memcache = True
  
  measurement = orm.SuperStringProperty('1', required=True)  # By definition, once a unit is created, measurement can not be modified! @todo We can implement choices=['Currency', 'Mass'...], or we can use query projections for data presentation from this property! Shall we incorporate measurement value into key_id?
  name = orm.SuperStringProperty('2', required=True)
  symbol = orm.SuperStringProperty('3', required=True, indexed=False)
  rate = orm.SuperDecimalProperty('4', indexed=False)  # The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12).
  factor = orm.SuperDecimalProperty('5', indexed=False)  # The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12).
  rounding = orm.SuperDecimalProperty('6', indexed=False)  # Rounding Precision - digits=(12, 12).
  digits = orm.SuperIntegerProperty('7', indexed=False)
  active = orm.SuperBooleanProperty('8', required=True, default=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'code': orm.SuperStringProperty('9'),
    'numeric_code': orm.SuperStringProperty('10'),
    'grouping': orm.SuperIntegerProperty('11', repeated=True),
    'decimal_separator': orm.SuperStringProperty('12'),
    'thousands_separator': orm.SuperStringProperty('13'),
    'positive_sign_position': orm.SuperIntegerProperty('14'),
    'negative_sign_position': orm.SuperIntegerProperty('15'),
    'positive_sign': orm.SuperStringProperty('16'),
    'negative_sign': orm.SuperStringProperty('17'),
    'positive_currency_symbol_precedes': orm.SuperBooleanProperty('18', default=True),
    'negative_currency_symbol_precedes': orm.SuperBooleanProperty('19', default=True),
    'positive_separate_by_space': orm.SuperBooleanProperty('20', default=True),
    'negative_separate_by_space': orm.SuperBooleanProperty('21', default=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('17', [orm.Action.build_key('17', 'update_currency'),
                                  orm.Action.build_key('17', 'update_unit')], True,
                           'account._root_admin or account._is_taskqueue'),
      orm.ActionPermission('17', [orm.Action.build_key('17', 'search')], True, 'not account._is_guest'),
      orm.FieldPermission('17', ['measurement', 'name', 'symbol', 'rate', 'factor', 'rounding',
                                 'digits', 'active', 'code', 'numeric_code', 'grouping', 'decimal_separator',
                                 'thousands_separator', 'positive_sign_position', 'negative_sign_position',
                                 'positive_sign', 'positive_currency_symbol_precedes', 'negative_currency_symbol_precedes',
                                 'positive_separate_by_space', 'negative_separate_by_space'], False, True, 'True'),
      orm.FieldPermission('17', ['measurement', 'name', 'symbol', 'rate', 'factor', 'rounding', 'digits', 'active',
                                 'code', 'numeric_code', 'grouping', 'decimal_separator', 'thousands_separator',
                                 'positive_sign_position', 'negative_sign_position', 'positive_sign',
                                 'positive_currency_symbol_precedes', 'negative_currency_symbol_precedes',
                                 'positive_separate_by_space', 'negative_separate_by_space'], True, True,
                          'account._root_admin or account._is_taskqueue')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('17', 'update_currency'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            UnitCurrencyUpdateWrite(cfg={'file': settings.CURRENCY_DATA_FILE})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('17', 'update_unit'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            UnitUpdateWrite(cfg={'file': settings.UOM_DATA_FILE})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('17', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}], 'orders': [{'field': 'name', 'operator': 'asc'}]},
          cfg={
            'search_arguments': {'kind': '17', 'options': {'limit': 1000}},
            'search_by_keys': True,
            'filters': {'measurement': orm.SuperStringProperty(),
                        'active': orm.SuperBooleanProperty(choices=[True])},
            'indexes': [{'filters': [('active', ['=='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('active', ['==']), ('measurement', ['=='])],
                         'orders': [('name', ['asc', 'desc'])]},
                         {'filters': [('measurement', ['!=']), ('active', ['=='])],
                         'orders': [('measurement', ['asc', 'desc']), ('key', ['asc', 'desc'])]}]
            }
          )
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Search(),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      )
    ]
