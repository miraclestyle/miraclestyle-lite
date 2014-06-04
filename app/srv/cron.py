# -*- coding: utf-8 -*-
'''
Created on May 29, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv.rule import GlobalRole, ActionPermission
from app.srv.event import Action
from app.plugins import common, rule, callback, cron


class CronConfig(ndb.BaseModel):
  
  _kind = 83
  
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
      _plugins=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            cron.ProcessCatalogs(page_size=settings.DOMAINS_PER_CRON),
            callback.Exec()
            ]
          )
        ]
      )
    ]
