# -*- coding: utf-8 -*-
'''
Created on May 29, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins import cron


class CronConfig(ndb.BaseModel):
  
  _kind = 83
  
  _use_record_engine = False
  _use_rule_engine = False
  
  data = ndb.SuperJsonProperty('1', indexed=False, default={})
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('83', [Action.build_key('83', 'process_catalogs')], True, 'context.user._is_cron')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('83', 'process_catalogs'),
      arguments={},
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            cron.ProcessCatalogs(cfg={'page': settings.DOMAINS_PER_CRON}),
            CallbackExec()
            ]
          )
        ]
      )
    ]
