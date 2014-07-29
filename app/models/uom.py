# -*- coding: utf-8 -*-
'''
Created on Jan 1, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.uom import *


class Unit(orm.BaseExpando):
  
  _kind = 18
  
  _use_record_engine = False
  _use_cache = True
  _use_memcache = True
  
  name = orm.SuperStringProperty('1', required=True)
  symbol = orm.SuperStringProperty('2', required=True, indexed=False)
  rate = orm.SuperDecimalProperty('3', indexed=False)  # The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12).
  factor = orm.SuperDecimalProperty('4', indexed=False)  # The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12).
  rounding = orm.SuperDecimalProperty('5', indexed=False)  # Rounding Precision - digits=(12, 12).
  digits = orm.SuperIntegerProperty('6', indexed=False)
  active = orm.SuperBooleanProperty('7', required=True, default=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'code': orm.SuperStringProperty('8'),
    'numeric_code': orm.SuperStringProperty('9'),
    'grouping': orm.SuperIntegerProperty('10', repeated=True),
    'decimal_separator': orm.SuperStringProperty('11'),
    'thousands_separator': orm.SuperStringProperty('12'),
    'positive_sign_position': orm.SuperIntegerProperty('13'),
    'negative_sign_position': orm.SuperIntegerProperty('14'),
    'positive_sign': orm.SuperStringProperty('15'),
    'negative_sign': orm.SuperStringProperty('16'),
    'positive_currency_symbol_precedes': orm.SuperBooleanProperty('17', default=True),
    'negative_currency_symbol_precedes': orm.SuperBooleanProperty('18', default=True),
    'positive_separate_by_space': orm.SuperBooleanProperty('19', default=True),
    'negative_separate_by_space': orm.SuperBooleanProperty('20', default=True)
    }


# @todo Thought has to be given to this construction.
# The fact is that, it is the Unit that is being searched and used directly all the time!
# Measurement merely serves as a constraint for unit conversions and categorization!
# Perhaps there should be units = orm.SuperLocalStructuredProperty(Unit, '2', repeated=True).
# By calculating expected max size of Unit (1536) with expected number of units per Measurement (512), total space occupied is 786432!
# This fact notes that even currency measurement can be accomodated in a single measurement entity,
# provided that there would be no more than 512 currencies at any given moment!
class Measurement(orm.BaseModel):
  
  _kind = 19
  
  _use_record_engine = False
  _use_cache = True
  _use_memcache = True
  
  name = orm.SuperStringProperty('1', required=True)
  
  _virtual_fields = {
    '_units': orm.SuperStorageStructuredProperty(Unit, storage='remote_multi')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('19', [orm.Action.build_key('19', 'update_currency'),
                                  orm.Action.build_key('19', 'update_unit')], True, 'user._root_admin or user._is_taskqueue'),
      orm.ActionPermission('19', [orm.Action.build_key('19', 'search')], True, 'not user._is_guest'),
      orm.FieldPermission('19', ['name', '_units'], False, True, 'True'),
      orm.FieldPermission('19', ['name', '_units'], True, True, 'user._root_admin or user._is_taskqueue')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('19', 'update_currency'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            UnitCurrencyUpdateWrite(cfg={'file': settings.CURRENCY_DATA_FILE})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('19', 'update_unit'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            UnitUpdateWrite(cfg={'file': settings.UOM_DATA_FILE})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('19', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['IN'], 'type': orm.SuperKeyProperty(kind='19', repeated=True)},
            'active': {'operators': ['==', '!='], 'type': orm.SuperBooleanProperty(choices=[True])},
            'ancestor': {'operators': ['=='], 'type': orm.SuperKeyFromPathProperty(kind='18')}
            },
          indexes=[
            {'filter': ['key']},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['active', 'ancestor'],
             'order_by': [['name', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
            }
          ),
        'cursor': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Search(cfg={'page': 1000}),
            UnitRemoveCurrencies(),
            RulePrepare(cfg={'path': '_entities', 'skip_user_roles': True}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      )
    ]


class UOM(orm.BaseExpando):
  
  _kind = 72
  
  measurement = orm.SuperStringProperty('1', required=True, indexed=False)
  name = orm.SuperStringProperty('2', required=True, indexed=False)
  symbol = orm.SuperStringProperty('3', required=True, indexed=False)
  rate = orm.SuperDecimalProperty('4', required=True, indexed=False)
  factor = orm.SuperDecimalProperty('5', required=True, indexed=False)
  rounding = orm.SuperDecimalProperty('6', required=True, indexed=False)
  digits = orm.SuperIntegerProperty('7', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'code': orm.SuperStringProperty('8', required=True),
    'numeric_code': orm.SuperStringProperty('9'),
    'grouping': orm.SuperIntegerProperty('10', repeated=True),
    'decimal_separator': orm.SuperStringProperty('11', required=True),
    'thousands_separator': orm.SuperStringProperty('12'),
    'positive_sign_position': orm.SuperIntegerProperty('13', required=True),
    'negative_sign_position': orm.SuperIntegerProperty('14', required=True),
    'positive_sign': orm.SuperStringProperty('15'),
    'negative_sign': orm.SuperStringProperty('16'),
    'positive_currency_symbol_precedes': orm.SuperBooleanProperty('17', default=True),
    'negative_currency_symbol_precedes': orm.SuperBooleanProperty('18', default=True),
    'positive_separate_by_space': orm.SuperBooleanProperty('19', default=True),
    'negative_separate_by_space': orm.SuperBooleanProperty('20', default=True)
    }
