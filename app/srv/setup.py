# -*- coding: utf-8 -*-
'''
Created on Apr 30, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv.event import Action
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.plugins import common, rule, log, callback, setup as plugin_setup


class Configuration(ndb.BaseExpando):
  
  _kind = 57
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  configuration_input = ndb.SuperPickleProperty('3', required=True, compressed=False)
  setup = ndb.SuperStringProperty('4', required=True, indexed=False)
  state = ndb.SuperStringProperty('5', required=True)
  next_operation = ndb.SuperStringProperty('6', indexed=False)
  next_operation_input = ndb.SuperPickleProperty('7', indexed=False)
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('57', [Action.build_key('57', 'install').urlsafe(),
                              Action.build_key('57', 'cron_install').urlsafe()], True, "context.user._is_taskqueue")
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('57', 'install'),
      arguments={
        'key': ndb.SuperKeyProperty(required=True, kind='57')
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        plugin_setup.Install()
        ]
      ),
    Action(
      key=Action.build_key('57', 'cron_install'),
      arguments={},
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=False),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        plugin_setup.CronInstall()
        ]
      )
    ]
