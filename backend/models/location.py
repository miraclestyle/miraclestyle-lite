# -*- coding: utf-8 -*-
'''
Created on Jan 9, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

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

  def condition_root_or_taskqueue(account, **kwargs):
    return account._root_admin or account._is_taskqueue

  def condition_not_guest(account, **kwargs):
    return not account._is_guest

  def condition_true(**kwargs):
    return True

  _permissions = [
      orm.ExecuteActionPermission('update', condition_root_or_taskqueue),
      orm.ExecuteActionPermission('search', condition_not_guest),
      orm.ReadFieldPermission(('code', 'name', 'active'), condition_true)
  ]

  _actions = [
      orm.Action(
          id='update',
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
          id='search',
          arguments={
              'search': orm.SuperSearchProperty(
                  default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}],
                           'orders': [{'field': 'name', 'operator': 'asc'}]},
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

  def condition_not_guest(account, **kwargs):
    return not account._is_guest

  def condition_true(**kwargs):
    return True

  _permissions = [
      orm.ExecuteActionPermission('search', condition_not_guest),
      orm.ReadFieldPermission(('parent_record', 'code', 'name', 'complete_name', 'type', 'active'), condition_true)
  ]

  _actions = [
      orm.Action(
          id='search',
          arguments={
              'search': orm.SuperSearchProperty(
                  default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}],
                           'orders': [{'field': 'name', 'operator': 'asc'}]},
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
