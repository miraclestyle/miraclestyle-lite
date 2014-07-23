# -*- coding: utf-8 -*-
'''
Created on Feb 24, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.nav import *


class Filter(orm.BaseModel):
  
  _kind = 65
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  model = orm.SuperStringProperty('2', required=True, indexed=False)
  query = orm.SuperJsonProperty('3', required=True, indexed=False, default={})


class Widget(orm.BaseExpando):
  
  _kind = 62
  
  name = orm.SuperStringProperty('1', required=True)
  sequence = orm.SuperIntegerProperty('2', required=True)
  active = orm.SuperBooleanProperty('3', required=True, default=True)
  role = orm.SuperKeyProperty('4', kind='60', required=True)
  search_form = orm.SuperBooleanProperty('5', required=True, indexed=False, default=True)
  filters = orm.SuperLocalStructuredProperty(Filter, '6', repeated=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('62')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('62', [orm.Action.build_key('62', 'prepare'),
                                  orm.Action.build_key('62', 'create'),
                                  orm.Action.build_key('62', 'read'),
                                  orm.Action.build_key('62', 'update'),
                                  orm.Action.build_key('62', 'delete'),
                                  orm.Action.build_key('62', 'search'),
                                  orm.Action.build_key('62', 'read_records'),
                                  orm.Action.build_key('62', 'build_menu')], False, 'entity._original.namespace_entity._original.state != "active"'),
      orm.ActionPermission('62', [orm.Action.build_key('62', 'create'),
                                  orm.Action.build_key('62', 'update'),
                                  orm.Action.build_key('62', 'delete')], False, 'entity._is_system'),
      orm.FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], False, False,
                          'entity._original.namespace_entity._original.state != "active"'),
      orm.FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], False, None,
                          'entity._is_system'),
      orm.FieldPermission('62', ['role'], False, None,
                          '(action.key_id_str == "create" or action.key_id_str == "update") and (entity.role and entity._original.key_namespace != entity.role.entity._original.key_namespace)')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('62', 'prepare'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_widget'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('62', 'create'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'name': orm.SuperStringProperty(required=True),
        'sequence': orm.SuperIntegerProperty(required=True),
        'active': orm.SuperBooleanProperty(default=True),
        'role': orm.SuperKeyProperty(kind='60', required=True),
        'search_form': orm.SuperBooleanProperty(default=True),
        'filters': orm.SuperLocalStructuredProperty(Filter, repeated=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_widget.name': 'input.name',
                           '_widget.sequence': 'input.sequence',
                           '_widget.active': 'input.active',
                           '_widget.role': 'input.role',
                           '_widget.search_form': 'input.search_form',
                           '_widget.filters': 'input.filters'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_widget'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('62', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='62', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_widget'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('62', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='62', required=True),
        'name': orm.SuperStringProperty(required=True),
        'sequence': orm.SuperIntegerProperty(required=True),
        'active': orm.SuperBooleanProperty(default=True),
        'role': orm.SuperKeyProperty(kind='60', required=True),
        'search_form': orm.SuperBooleanProperty(default=True),
        'filters': orm.SuperLocalStructuredProperty(Filter, repeated=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_widget.name': 'input.name',
                           '_widget.sequence': 'input.sequence',
                           '_widget.active': 'input.active',
                           '_widget.role': 'input.role',
                           '_widget.search_form': 'input.search_form',
                           '_widget.filters': 'input.filters'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_widget'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('62', 'delete'),
      arguments={
        'key': orm.SuperKeyProperty(kind='62', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Delete(),
            Set(cfg={'d': {'output.entity': '_widget'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('62', 'search'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'sequence', 'operator': 'asc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()},
            'role': {'operators': ['==', '!='], 'type': orm.SuperKeyProperty(kind='60')},
            'active': {'operators': ['==', '!='], 'type': orm.SuperBooleanProperty()}
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
        'search_cursor': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Search(cfg={'page': settings.SEARCH_PAGE}),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('62', 'build_menu'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            NavBuildMenu(),
            Set(cfg={'d': {'output.menu': '_widgets', 'output.domain': 'domain'}})
            ]
          )
        ]
      )
    ]
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')
