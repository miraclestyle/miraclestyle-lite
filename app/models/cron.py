# -*- coding: utf-8 -*-
'''
Created on May 29, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.cron import *


class CronConfig(orm.BaseModel):
  
  _kind = 83
  
  _use_record_engine = False
  _use_rule_engine = False
  
  data = orm.SuperJsonProperty('1', indexed=False, default={})
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('83', [orm.Action.build_key('83', 'process_catalogs')], True, 'user._is_cron')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('83', 'process_catalogs'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            CronConfigProcessCatalogs(cfg={'page': settings.DOMAINS_PER_CRON}),
            CallbackExec()
            ]
          )
        ]
      )
    ]
