# -*- coding: utf-8 -*-
'''
Created on Feb 24, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
#from app.srv.event import Action, PluginGroup
#from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
#from app.srv import log as ndb_log
#from app.plugins import common, rule, log, callback, nav
from app.srv.base import *
from app.plugins.base import *
from app.plugins import nav


class Filter(ndb.BaseModel):
  
  _kind = 65
  
  name = ndb.SuperStringProperty('1', required=True, indexed=False)
  kind = ndb.SuperStringProperty('2', required=True, indexed=False)
  query = ndb.SuperJsonProperty('3', required=True, indexed=False, default={})


class Widget(ndb.BaseExpando):
  
  _kind = 62
  
  name = ndb.SuperStringProperty('1', required=True)
  sequence = ndb.SuperIntegerProperty('2', required=True)
  active = ndb.SuperBooleanProperty('3', required=True, default=True)
  role = ndb.SuperKeyProperty('4', kind='60', required=True)
  search_form = ndb.SuperBooleanProperty('5', required=True, indexed=False, default=True)
  filters = ndb.SuperLocalStructuredProperty(Filter, '6', repeated=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': SuperLocalStructuredRecordProperty('62', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('62', [Action.build_key('62', 'prepare'),
                              Action.build_key('62', 'create'),
                              Action.build_key('62', 'read'),
                              Action.build_key('62', 'update'),
                              Action.build_key('62', 'delete'),
                              Action.build_key('62', 'search'),
                              Action.build_key('62', 'read_records'),
                              Action.build_key('62', 'build_menu')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('62', [Action.build_key('62', 'create'),
                              Action.build_key('62', 'update'),
                              Action.build_key('62', 'delete')], False, 'context.entity._is_system'),
      FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], False, None,
                      'context.entity._is_system'),
      FieldPermission('62', ['role'], False, None,
                      '(context.action.key_id_str == "create" or context.action.key_id_str == "update") and (context.value and context.value.role and context.entity.key_namespace != context.value.role.entity.key_namespace)')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('62', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            Set(config={'dynamic': {'output.entity': 'entities.62'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('62', 'create'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'sequence': ndb.SuperIntegerProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True),
        'role': ndb.SuperKeyProperty(kind='60', required=True),
        'search_form': ndb.SuperBooleanProperty(default=True),
        'filters': ndb.SuperJsonProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            nav.Set(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            #log.Entity(),
            RecordWrite(config={'records': ['entities']}),
            RuleRead(),
            Set(config={'dynamic': {'output.entity': 'entities.62'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('62', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RuleRead(),
            Set(config={'dynamic': {'output.entity': 'entities.62'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('62', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'sequence': ndb.SuperIntegerProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True),
        'role': ndb.SuperKeyProperty(kind='60', required=True),
        'search_form': ndb.SuperBooleanProperty(default=True),
        'filters': ndb.SuperJsonProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            nav.Set(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            #log.Entity(),
            RecordWrite(config={'records': ['entities']}),
            RuleRead(),
            Set(config={'dynamic': {'output.entity': 'entities.62'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('62', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Delete(),
            #log.Entity(),
            RecordWrite(config={'records': ['entities']}),
            RuleRead(),
            Set(config={'dynamic': {'output.entity': 'entities.62'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('62', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'sequence', 'operator': 'asc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'role': {'operators': ['==', '!='], 'type': ndb.SuperKeyProperty(kind='60')},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty()}
            },
          indexes=[
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['role'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['name', 'active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['role', 'active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']},
            'sequence': {'operators': ['asc', 'desc']}
            }
          ),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            Search(config={'page': settings.SEARCH_PAGE}),
            RulePrepare(config={'to': 'entities'}),
            RuleRead(config={'path': 'entities'}),
            Set(config={'dynamic': {'output.entities': 'entities',
                                    'output.search_cursor': 'search_cursor',
                                    'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('62', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RecordRead(config={'page': settings.RECORDS_PAGE}),
            RuleRead(),
            Set(config={'dynamic': {'output.entity': 'entities.62',
                                    'output.log_read_cursor': 'log_read_cursor',
                                    'output.log_read_more': 'log_read_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('62', 'build_menu'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            nav.BuildMenu(),
            Set(config={'dynamic': {'output.menu': 'tmp.widgets', 'output.domain': 'domain'}})
            ]
          )
        ]
      )
    ]
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')
