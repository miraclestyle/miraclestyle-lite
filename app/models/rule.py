# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins import rule


class DomainRole(Role):
  
  _kind = 60
  
  _virtual_fields = {
    '_records': SuperLocalStructuredRecordProperty('60', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('60', [Action.build_key('60', 'prepare'),
                              Action.build_key('60', 'create'),
                              Action.build_key('60', 'read'),
                              Action.build_key('60', 'update'),
                              Action.build_key('60', 'delete'),
                              Action.build_key('60', 'search'),
                              Action.build_key('60', 'read_records')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('60', [Action.build_key('60', 'create'),
                              Action.build_key('60', 'update'),
                              Action.build_key('60', 'delete')], False, 'context.entity._is_system'),
      FieldPermission('60', ['name', 'active', 'permissions', '_records'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('60', ['name', 'active', 'permissions', '_records'], False, None,
                      'context.entity._is_system')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('60', 'prepare'),
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
            Set(cfg={'d': {'output.entity': 'entities.60'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('60', 'create'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'permissions': ndb.SuperJsonProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            rule.DomainRoleSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(cfg={'paths': ['entities.60']}),
            RuleRead(),
            Set(cfg={'d': {'output.entity': 'entities.60'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('60', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RuleRead(),
            Set(cfg={'d': {'output.entity': 'entities.60'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('60', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'permissions': ndb.SuperJsonProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            rule.DomainRoleSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(cfg={'paths': ['entities.60']}),
            RuleRead(),
            Set(cfg={'d': {'output.entity': 'entities.60'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('60', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True)
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
            RecordWrite(cfg={'paths': ['entities.60']}),
            RuleRead(),
            Set(cfg={'d': {'output.entity': 'entities.60'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('60', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['IN'], 'type': ndb.SuperKeyProperty(kind='60', repeated=True)},
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty()}
            },
          indexes=[
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['key']},
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name', 'active'],
             'order_by': [['name', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
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
            Search(cfg={'page': settings.SEARCH_PAGE}),
            RulePrepare(cfg={'to': 'entities'}),
            RuleRead(cfg={'path': 'entities'}),
            Set(cfg={'d': {'output.entities': 'entities',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('60', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RecordRead(cfg={'page': settings.RECORDS_PAGE}),
            RuleRead(),
            Set(cfg={'d': {'output.entity': 'entities.60',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}})
            ]
          )
        ]
      )
    ]
  
  @property
  def _is_system(self):
    return self.key_id_str == 'admin'


class DomainUser(ndb.BaseExpando):
  
  _kind = 8
  
  name = ndb.SuperStringProperty('1', required=True)
  roles = ndb.SuperKeyProperty('2', kind='60', repeated=True)  # It's important to ensure that this list doesn't contain duplicate role keys, since that can pose security issue!!
  state = ndb.SuperStringProperty('3', required=True, choices=['invited', 'accepted'])
  
  _default_indexed = False
  
  _virtual_fields = {
    '_primary_email': ndb.SuperStringProperty(),
    '_records': SuperLocalStructuredRecordProperty('8', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('8', [Action.build_key('8', 'prepare'),
                             Action.build_key('8', 'invite'),
                             Action.build_key('8', 'read'),
                             Action.build_key('8', 'update'),
                             Action.build_key('8', 'remove'),
                             Action.build_key('8', 'search'),
                             Action.build_key('8', 'read_records'),
                             Action.build_key('8', 'accept'),
                             Action.build_key('8', 'clean_roles')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('8', Action.build_key('8', 'remove'), False,
                       'context.entity.key_id_str == context.entity.namespace_entity.primary_contact.entity.key_id_str'),
      ActionPermission('8', Action.build_key('8', 'remove'), True,
                       '(context.entity.namespace_entity.state == "active" and context.user.key_id_str == context.entity.key_id_str) and not (context.entity.key_id_str == context.entity.namespace_entity.primary_contact.entity.key_id_str)'),
      ActionPermission('8', Action.build_key('8', 'accept'), False,
                       'context.user.key_id_str != context.entity.key_id_str'),
      ActionPermission('8', Action.build_key('8', 'accept'), True,
                       'context.entity.namespace_entity.state == "active" and context.user.key_id_str == context.entity.key_id_str and context.entity.state == "invited"'),
      ActionPermission('8', Action.build_key('8', 'clean_roles'), False,
                       'not context.user._is_taskqueue'),
      ActionPermission('8', Action.build_key('8', 'clean_roles'), True,
                       'context.entity.namespace_entity.state == "active" and context.user._is_taskqueue'),
      FieldPermission('8', ['name', 'roles', 'state', '_primary_email', '_records'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('8', ['state'], False, None, 'True'),
      FieldPermission('8', ['roles'], False, None,
                      'context.entity.key_id_str == context.entity.namespace_entity.primary_contact.entity.key_id_str'),
      FieldPermission('8', ['state'], True, None,
                      '(context.action.key_id_str == "invite" and context.value and context.value.state == "invited") or (context.action.key_id_str == "accept" and context.value and context.value.state == "accepted")')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('8', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6')
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': 'entities.8'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('8', 'invite'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6'),
        'name': ndb.SuperStringProperty(required=True),
        'email': ndb.SuperStringProperty(required=True),
        'roles': ndb.SuperKeyProperty(kind='60', repeated=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            rule.DomainUserInvite(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(cfg={'paths': ['entities.8', 'entities.0']}),
            RecordWrite(cfg={'paths': ['entities.8', 'entities.0']}),
            RuleRead(),
            Set(cfg={'d': {'output.entity': 'entities.8'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('8', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            rule.DomainUserRead(),
            RulePrepare(),
            RuleExec(),
            RuleRead(),
            Set(cfg={'d': {'output.entity': 'entities.8'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('8', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'roles': ndb.SuperKeyProperty(kind='60', repeated=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            rule.DomainUserRead(),
            rule.DomainUserUpdate(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(cfg={'paths': ['entities.8']}),
            RuleRead(),
            Set(cfg={'d': {'output.entity': 'entities.8'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('8', 'remove'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            rule.DomainUserRead(),
            rule.DomainUserRemove(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'paths': ['entities.0']}),
            Delete(),
            RecordWrite(cfg={'paths': ['entities.8', 'entities.0']}),
            RuleRead(),
            Set(cfg={'d': {'output.entity': 'entities.8'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('8', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['IN'], 'type': ndb.SuperKeyProperty(kind='8', repeated=True)},
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty(choices=['invited', 'accepted'])}
            },
          indexes=[
            {'filter': ['key']},
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['state'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name', 'state'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
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
            Search(cfg={'page': settings.SEARCH_PAGE}),
            RulePrepare(cfg={'to': 'entities'}),
            RuleRead(cfg={'path': 'entities'}),
            Set(cfg={'d': {'output.entities': 'entities',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('8', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            rule.DomainUserRead(),
            RulePrepare(),
            RuleExec(),
            RecordRead(cfg={'page': settings.RECORDS_PAGE}),
            RuleRead(),
            Set(cfg={'d': {'output.entity': 'entities.8',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('8', 'accept'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            rule.DomainUserRead(),
            Set(cfg={'s': {'values.8.state': 'accepted'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(cfg={'paths': ['entities.8']}),
            Set(cfg={'d': {'entities.6': 'entities.8.namespace_entity',
                           'values.6': 'entities.8.namespace_entity'}}),
            RulePrepare(cfg={'to': 'entities', 'from': 'values'}),  # @todo Should run out of transaction!!!
            RuleRead(cfg={'path': 'entities'}),
            Set(cfg={'d': {'output.entity': 'entities.8',
                           'output.domain': 'entities.6'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('8', 'clean_roles'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            rule.DomainUserRead(),
            rule.DomainUserCleanRoles(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(cfg={'paths': ['entities.8']})
            ]
          )
        ]
      )
    ]
