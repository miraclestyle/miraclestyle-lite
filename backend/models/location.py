# -*- coding: utf-8 -*-
'''
Created on Jan 9, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

# @todo Perhaps split this file in two: country.py and address.py?
import orm
import settings

from plugins.base import *
from plugins.location import *


__all__ = ['Country', 'CountrySubdivision']


class Country(orm.BaseModel):
  
  _kind = 12
  
  _use_record_engine = False
  _use_cache = True
  _use_memcache = True
  
  code = orm.SuperStringProperty('1', required=True, indexed=False)
  name = orm.SuperStringProperty('2', required=True)
  active = orm.SuperBooleanProperty('3', required=True, default=True)
  
  _global_role = orm.GlobalRole(
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
            'filters': {'active': orm.SuperBooleanProperty(choices=(True,))},
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
  
  _global_role = orm.GlobalRole(
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
            'search_arguments': {'kind': '13', 'options': {'limit': 100}},
            'ancestor_kind': '12',
            'search_by_keys': True,
            'filters': {'active': orm.SuperBooleanProperty(choices=(True,))},
            'indexes': [{'ancestor': True,
                         'filters': [('active', ['=='])],
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
