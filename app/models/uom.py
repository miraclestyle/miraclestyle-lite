# -*- coding: utf-8 -*-
'''
Created on Jan 1, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.uom import *


class Measurement(orm.BaseModel):  # @todo Not sure about the fact that actions are hosted in child model of the structure!!?
  
  _kind = 18
  
  _use_record_engine = False
  _use_cache = True
  _use_memcache = True
  
  name = orm.SuperStringProperty('1', required=True)


class Unit(orm.BaseExpando):
  
  _kind = 19
  
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
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('19', [orm.Action.build_key('19', 'update_currency'),
                                  orm.Action.build_key('19', 'update_unit')], True, 'user._root_admin or user._is_taskqueue'),
      orm.ActionPermission('19', [orm.Action.build_key('19', 'search')], True, 'not user._is_guest'),
      orm.FieldPermission('19', ['name', 'symbol', 'rate', 'factor', 'rounding', 'digits', 'active', 'code', 'numeric_code',
                                 'grouping', 'decimal_separator', 'thousands_separator', 'positive_sign_position',
                                 'negative_sign_position', 'positive_sign', 'positive_currency_symbol_precedes',
                                 'negative_currency_symbol_precedes', 'positive_separate_by_space', 'negative_separate_by_space'], False, True, 'True'),
      orm.FieldPermission('19', ['name', 'symbol', 'rate', 'factor', 'rounding', 'digits', 'active', 'code', 'numeric_code',
                                 'grouping', 'decimal_separator', 'thousands_separator', 'positive_sign_position',
                                 'negative_sign_position', 'positive_sign', 'positive_currency_symbol_precedes',
                                 'negative_currency_symbol_precedes', 'positive_separate_by_space', 'negative_separate_by_space'], True, True,
                          'user._root_admin or user._is_taskqueue')
      ]
    )
  
  _actions = [  # @todo Do we need read action here?
    orm.Action(
      key=orm.Action.build_key('19', 'update_currency'),  # @todo In order to warrant idempotency, this action has to produce custom key for each commited entry.
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
      key=orm.Action.build_key('19', 'update_unit'),  # @todo In order to warrant idempotency, this action has to produce custom key for each commited entry.
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
