# -*- coding: utf-8 -*-
'''
Created on May 29, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb, settings
from app.srv.rule import GlobalRole, ActionPermission
from app.srv.event import Action
from app.plugins import common, rule, callback, cron


class DomainCatalogProcess(ndb.BaseModel): # it can be called differently
   
  _kind = 83
  
  current_cursor = ndb.SuperStringProperty()
  current_more = ndb.SuperBooleanProperty(default=False)
   
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('83', [Action.build_key('83', 'run')], True, 'context.user._is_cron')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('83', 'run'), # it can be called differently
      arguments={},
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        cron.DomainCatalogProcessRun(page_size=settings.DOMAINS_PER_CRON),
        callback.Exec(dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'}),
        ]
      )
    ]