# -*- coding: utf-8 -*-
'''
Created on Jan 1, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv.event import Action
from app.srv.rule import ActionPermission, FieldPermission, GlobalRole
from app.plugins import common, callback, rule, uom


class Measurement(ndb.BaseModel):
  
  _kind = 18
  
  _use_cache = True
  _use_memcache = True
  
  name = ndb.SuperStringProperty('1', required=True)


class Unit(ndb.BaseExpando):
  
  _kind = 19
  
  _use_cache = True
  _use_memcache = True
  
  name = ndb.SuperStringProperty('1', required=True)
  symbol = ndb.SuperStringProperty('2', required=True, indexed=False)
  rate = ndb.SuperDecimalProperty('3', indexed=False)  # The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12).
  factor = ndb.SuperDecimalProperty('4', indexed=False)  # The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12).
  rounding = ndb.SuperDecimalProperty('5', indexed=False)  # Rounding Precision - digits=(12, 12).
  digits = ndb.SuperIntegerProperty('6', indexed=False)
  active = ndb.SuperBooleanProperty('7', required=True, default=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'code': ndb.SuperStringProperty('8'),
    'numeric_code': ndb.SuperStringProperty('9'),
    'grouping': ndb.SuperIntegerProperty('10', repeated=True),
    'decimal_separator': ndb.SuperStringProperty('11'),
    'thousands_separator': ndb.SuperStringProperty('12'),
    'positive_sign_position': ndb.SuperIntegerProperty('13'),
    'negative_sign_position': ndb.SuperIntegerProperty('14'),
    'positive_sign': ndb.SuperStringProperty('15'),
    'negative_sign': ndb.SuperStringProperty('16'),
    'positive_currency_symbol_precedes': ndb.SuperBooleanProperty('17', default=True),
    'negative_currency_symbol_precedes': ndb.SuperBooleanProperty('18', default=True),
    'positive_separate_by_space': ndb.SuperBooleanProperty('19', default=True),
    'negative_separate_by_space': ndb.SuperBooleanProperty('20', default=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('19', [Action.build_key('19', 'update_currency'),
                              Action.build_key('19', 'update_unit'),
                              Action.build_key('19', 'search')], True, 'context.user._root_admin or context.user._is_taskqueue'),
      FieldPermission('19', ['name', 'symbol', 'rate', 'factor', 'rounding', 'digits', 'active', 'code', 'numeric_code',
                             'grouping', 'decimal_separator', 'thousands_separator', 'positive_sign_position',
                             'negative_sign_position', 'positive_sign', 'positive_currency_symbol_precedes',
                             'negative_currency_symbol_precedes', 'positive_separate_by_space', 'negative_separate_by_space'], False, None, 'True'),
      FieldPermission('19', ['name', 'symbol', 'rate', 'factor', 'rounding', 'digits', 'active', 'code', 'numeric_code',
                             'grouping', 'decimal_separator', 'thousands_separator', 'positive_sign_position',
                             'negative_sign_position', 'positive_sign', 'positive_currency_symbol_precedes',
                             'negative_currency_symbol_precedes', 'positive_separate_by_space', 'negative_separate_by_space'], True, True,
                      'context.user._root_admin or context.user._is_taskqueue')
      ]
    )
  
  _actions = [  # @todo Do we need read action here?
    Action(
      key=Action.build_key('19', 'update_currency'),
      arguments={},
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        uom.CurrencyUpdate(file_path=settings.CURRENCY_DATA_FILE)
        ]
      ),
    Action(
      key=Action.build_key('19', 'update_unit'),
      arguments={},
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        uom.UnitUpdate(file_path=settings.UOM_DATA_FILE)
        ]
      ),
    Action(
      key=Action.build_key('19', 'search'),
      arguments={
        'search': ndb.SuperSearchProperty(
          default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['IN'], 'type': ndb.SuperKeyProperty(kind='19', repeated=True)},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty(choices=[True])},
            'ancestor': {'operators': ['=='], 'type': ndb.SuperKeyFromPathProperty(kind='18')}
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
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(page_size=-1),
        uom.RemoveCurrencies(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities',
                                   'output.search_cursor': 'search_cursor',
                                   'output.search_more': 'search_more'})
        ]
      )
    ]


class UOM(ndb.BaseExpando):
  
  _kind = 72
  
  measurement = ndb.SuperStringProperty('1', required=True, indexed=False)
  name = ndb.SuperStringProperty('2', required=True, indexed=False)
  symbol = ndb.SuperStringProperty('3', required=True, indexed=False)
  rate = ndb.SuperDecimalProperty('4', required=True, indexed=False)
  factor = ndb.SuperDecimalProperty('5', required=True, indexed=False)
  rounding = ndb.SuperDecimalProperty('6', required=True, indexed=False)
  digits = ndb.SuperIntegerProperty('7', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'code': ndb.SuperStringProperty('8', required=True),
    'numeric_code': ndb.SuperStringProperty('9'),
    'grouping': ndb.SuperIntegerProperty('10', repeated=True),
    'decimal_separator': ndb.SuperStringProperty('11', required=True),
    'thousands_separator': ndb.SuperStringProperty('12'),
    'positive_sign_position': ndb.SuperIntegerProperty('13', required=True),
    'negative_sign_position': ndb.SuperIntegerProperty('14', required=True),
    'positive_sign': ndb.SuperStringProperty('15'),
    'negative_sign': ndb.SuperStringProperty('16'),
    'positive_currency_symbol_precedes': ndb.SuperBooleanProperty('17', default=True),
    'negative_currency_symbol_precedes': ndb.SuperBooleanProperty('18', default=True),
    'positive_separate_by_space': ndb.SuperBooleanProperty('19', default=True),
    'negative_separate_by_space': ndb.SuperBooleanProperty('20', default=True)
    }
