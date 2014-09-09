# -*- coding: utf-8 -*-
'''
Created on Apr 30, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.setup import *


class Configuration(orm.BaseExpando):
  
  _kind = 57
  
  _use_record_engine = False
  _use_rule_engine = False
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  configuration_input = orm.SuperPickleProperty('3', required=True, compressed=False, indexed=False)
  setup = orm.SuperStringProperty('4', required=True, indexed=False)
  state = orm.SuperStringProperty('5', required=True)
  next_operation = orm.SuperStringProperty('6', indexed=False)
  next_operation_input = orm.SuperPickleProperty('7', indexed=False)
  
  _default_indexed = False
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('57', [orm.Action.build_key('57', 'install'),
                                  orm.Action.build_key('57', 'cron_install')], True, 'account._is_taskqueue')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('57', 'install'),
      arguments={
        'key': orm.SuperKeyProperty(required=True, kind='57')
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            ConfigurationInstall()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('57', 'cron_install'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            ConfigurationCronInstall(cfg={'time': settings.SETUP_ELAPSED_TIME})
            ]
          )
        ]
      )
    ]
