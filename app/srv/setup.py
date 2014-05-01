# -*- coding: utf-8 -*-
'''
Created on Apr 30, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv.event import Action
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.plugins import common, rule, log, callback, setup


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
      ActionPermission('57', Action.build_key('57-0').urlsafe(), True, "context.user._is_taskqueue"),
      ActionPermission('57', Action.build_key('57-1').urlsafe(), True, "context.user._is_taskqueue")
      ]
    )
  
  _actions = {
    'install': Action(
      id='57-0',
      arguments={
        'key': ndb.SuperKeyProperty(required=True, kind='57')
        }
      ),
    'cron_install': Action(
      id='57-1',
      arguments={}
      )
    }
  
  _plugins = [
    common.Context(
      subscriptions=[
        Action.build_key('57-0'),
        Action.build_key('57-1')
        ]
      ),
    common.Prepare(
      subscriptions=[
        Action.build_key('57-1')
        ],
      domain_model=False
      ),
    common.Read(
      subscriptions=[
        Action.build_key('57-0')
        ]
      ),
    rule.Prepare(
      subscriptions=[
        Action.build_key('57-0'),
        Action.build_key('57-1')
        ],
      skip_user_roles=True,
      strict=False
      ),
    rule.Exec(
      subscriptions=[
        Action.build_key('57-0'),
        Action.build_key('57-1')
        ]
      ),
    setup.Install(
      subscriptions=[
        Action.build_key('57-0')
        ]
      ),
    setup.CronInstall(
      subscriptions=[
        Action.build_key('57-1')
        ]
      )
    ]
