# -*- coding: utf-8 -*-
'''
Created on Jan 9, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

# @todo Perhaps split this file in two: country.py and address.py?
from backend import orm, settings
from backend.models.base import *
from backend.plugins.base import *

from backend.plugins.location import *


__all__ = ['Country', 'CountrySubdivision', 'Address', 'Location', 'get_location']


def get_location(location):
  if isinstance(location, orm.Key):
    location = location.get()
  location_country = location.country.get()
  location_region = location.region.get()
  return Location(name=location.name,
                  country=location_country.name,
                  country_code=location_country.code,
                  region=location_region.name,
                  region_code=location_region.code,
                  city=location.city,
                  postal_code=location.postal_code,
                  street=location.street,
                  email=location.email,
                  telephone=location.telephone)


class Country(orm.BaseModel):
  
  _kind = 12
  
  _use_record_engine = False
  _use_cache = True
  _use_memcache = True
  
  code = orm.SuperStringProperty('1', required=True, indexed=False)
  name = orm.SuperStringProperty('2', required=True)
  active = orm.SuperBooleanProperty('3', required=True, default=True)
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('12', [orm.Action.build_key('12', 'update')], True,
                           'account._root_admin or account._is_taskqueue'),
      orm.ActionPermission('12', [orm.Action.build_key('12', 'search')], True, 'not account._is_guest'),
      orm.FieldPermission('12', ['code', 'name', 'active'], False, True, 'True'),
      orm.FieldPermission('12', ['code', 'name', 'active'], True, True,
                          'account._root_admin or account._is_taskqueue')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('12', 'update'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CountryUpdateWrite(cfg={'file': settings.LOCATION_DATA_FILE,
                                    'prod_env': settings.DEVELOPMENT_SERVER})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('12', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}], 'orders': [{'field': 'name', 'operator': 'asc'}]},
          cfg={
            'search_arguments': {'kind': '12', 'options': {'limit': 1000}},
            'search_by_keys': True,
            'filters': {'active': orm.SuperBooleanProperty(choices=[True])},
            'indexes': [{'filters': [('active', ['=='])],
                         'orders': [('name', ['asc', 'desc'])]}]
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


class CountrySubdivision(orm.BaseModel):
  
  _kind = 13
  
  _use_record_engine = False
  _use_cache = True
  _use_memcache = True
  
  parent_record = orm.SuperKeyProperty('1', kind='13', indexed=False)
  code = orm.SuperStringProperty('2', required=True, indexed=False)
  name = orm.SuperStringProperty('3', required=True)
  complete_name = orm.SuperTextProperty('4', required=True)
  type = orm.SuperStringProperty('5', required=True, indexed=False)
  active = orm.SuperBooleanProperty('6', required=True, default=True)
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('13', [orm.Action.build_key('13', 'search')], True, 'not account._is_guest'),
      orm.FieldPermission('13', ['parent_record', 'code', 'name', 'complete_name', 'type', 'active'], False, True, 'True'),
      orm.FieldPermission('13', ['parent_record', 'code', 'name', 'complete_name', 'type', 'active'], True, True,
                          'account._root_admin or account._is_taskqueue')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('13', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}], 'orders': [{'field': 'name', 'operator': 'asc'}]},
          cfg={
            'search_arguments': {'kind': '13', 'options': {'limit': settings.SEARCH_PAGE}},
            'ancestor_kind': '12',
            'search_by_keys': True,
            'filters': {'name': orm.SuperStringProperty(value_filters=[lambda p, s: s.capitalize()]),
                        'active': orm.SuperBooleanProperty(choices=[True])},
            'indexes': [{'filters': [('active', ['=='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'ancestor': True,
                         'filters': [('active', ['=='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('active', ['==']), ('name', ['==', '!=', 'contains'])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'ancestor': True,
                         'filters': [('active', ['==']), ('name', ['==', '!=', 'contains'])],
                         'orders': [('name', ['asc', 'desc'])]}]
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


class Address(orm.BaseExpando):
  
  _kind = 14
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  country = orm.SuperKeyProperty('2', kind='12', required=True, indexed=False)
  city = orm.SuperStringProperty('3', required=True, indexed=False)
  postal_code = orm.SuperStringProperty('4', required=True, indexed=False)
  street = orm.SuperStringProperty('5', required=True, indexed=False)
  default_shipping = orm.SuperBooleanProperty('6', required=True, default=True, indexed=False)
  default_billing = orm.SuperBooleanProperty('7', required=True, default=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'region': orm.SuperKeyProperty('8', kind='13'),
    'email': orm.SuperStringProperty('9'),
    'telephone': orm.SuperStringProperty('10')
    }
  
  _virtual_fields = {
    '_country': orm.SuperReferenceStructuredProperty('12', autoload=True, target_field='country'),
    '_region': orm.SuperReferenceStructuredProperty('13', autoload=True, target_field='region')
  }


class Location(orm.BaseExpando):
  
  _kind = 15
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  country = orm.SuperStringProperty('2', required=True, indexed=False)
  country_code = orm.SuperStringProperty('3', required=True, indexed=False)
  city = orm.SuperStringProperty('4', required=True, indexed=False)
  postal_code = orm.SuperStringProperty('5', required=True, indexed=False)
  street = orm.SuperStringProperty('6', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'region': orm.SuperStringProperty('7'),
    'region_code': orm.SuperStringProperty('8'),
    'email': orm.SuperStringProperty('9'),
    'telephone': orm.SuperStringProperty('10')
    }
