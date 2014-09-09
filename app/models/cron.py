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
            RulePrepare(),
            RuleExec(),
            CronConfigProcessCatalogs(cfg={'page': settings.ACCOUNTS_PER_CRON}),
            Write(),
            CallbackExec()
            ]
          )
        ]
      )
    ]
  
  # @todo Right now this will work however, once we implement other cron actions, prepare_key will be useless (see plugins/base.py Read plugin)!
  # One way this could work with multiple actions is if we use CronConfig.data to store action specific parameters!
  @classmethod
  def prepare_key(cls, input, **kwargs):
    return cls.build_key('process_catalogs_key')
