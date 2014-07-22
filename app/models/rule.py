# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.rule import *


class DomainRole(Role):
  
  _kind = 60
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('60')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('60', [orm.Action.build_key('60', 'prepare'),
                                  orm.Action.build_key('60', 'create'),
                                  orm.Action.build_key('60', 'read'),
                                  orm.Action.build_key('60', 'update'),
                                  orm.Action.build_key('60', 'delete'),
                                  orm.Action.build_key('60', 'search')], False, 'entity._original.namespace_entity._original.state != "active"'),
      orm.ActionPermission('60', [orm.Action.build_key('60', 'create'),
                                  orm.Action.build_key('60', 'update'),
                                  orm.Action.build_key('60', 'delete')], False, 'entity._is_system'),
      orm.FieldPermission('60', ['name', 'active', 'permissions', '_records'], False, False,
                          'entity._original.namespace_entity._original.state != "active"'),
      orm.FieldPermission('60', ['name', 'active', 'permissions', '_records'], False, None, 'entity._is_system')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('60', 'prepare'),
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
            Set(cfg={'d': {'output.entity': '_domainrole'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('60', 'create'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'name': orm.SuperStringProperty(required=True),
        'permissions': orm.SuperJsonProperty(required=True),
        'active': orm.SuperBooleanProperty(default=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            DomainRoleSet()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_domainrole'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('60', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='60', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_domainrole'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('60', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='60', required=True),
        'name': orm.SuperStringProperty(required=True),
        'permissions': orm.SuperJsonProperty(required=True),
        'active': orm.SuperBooleanProperty(default=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            DomainRoleSet()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_domainrole'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('60', 'delete'),
      arguments={
        'key': orm.SuperKeyProperty(kind='60', required=True)
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
            Set(cfg={'d': {'output.entity': '_domainrole'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('60', 'search'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['IN'], 'type': orm.SuperKeyProperty(kind='60', repeated=True)},
            'name': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()},
            'active': {'operators': ['==', '!='], 'type': orm.SuperBooleanProperty()}
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
            RulePrepare(cfg={'path': 'entities'}),
            Set(cfg={'d': {'output.entities': 'entities',
                           'output._cursor': '_cursor',
                           'output._more': '_more'}})
            ]
          )
        ]
      )
    ]
  
  @property
  def _is_system(self):
    # return self.key_id_str.startswith('system_') @todo Perhaps we will have more than one system role!
    return self.key_id_str == 'admin'


class DomainUser(orm.BaseExpando):
  
  _kind = 8
  
  name = orm.SuperStringProperty('1', required=True)
  roles = orm.SuperKeyProperty('2', kind='60', repeated=True)  # It's important to ensure that this list doesn't contain duplicate role keys, since that can pose security issue!!
  state = orm.SuperStringProperty('3', required=True, choices=['invited', 'accepted'])
  
  _default_indexed = False
  
  _virtual_fields = {
    '_primary_email': orm.SuperReferenceProperty(callback=lambda self: self._get_primary_email_async(),
                                                 format_callback=lambda self, value: value._primary_email),
    '_records': orm.SuperRecordProperty('8')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('8', [orm.Action.build_key('8', 'prepare'),
                                 orm.Action.build_key('8', 'invite'),
                                 orm.Action.build_key('8', 'read'),
                                 orm.Action.build_key('8', 'update'),
                                 orm.Action.build_key('8', 'remove'),
                                 orm.Action.build_key('8', 'search'),
                                 orm.Action.build_key('8', 'accept'),
                                 orm.Action.build_key('8', 'clean_roles')], False, 'entity._original.namespace_entity._original.state != "active"'),
      orm.ActionPermission('8', orm.Action.build_key('8', 'remove'), False,
                           'entity._original.key_id_str == entity._original.namespace_entity._original.primary_contact.entity._original.key_id_str'),
      orm.ActionPermission('8', orm.Action.build_key('8', 'remove'), True,
                           '(entity._original.namespace_entity._original.state == "active" and user.key_id_str == entity._original.key_id_str) and not (entity._original.key_id_str == entity._original.namespace_entity._original.primary_contact.entity._original.key_id_str)'),
      orm.ActionPermission('8', orm.Action.build_key('8', 'accept'), False,
                           'user.key_id_str != entity._original.key_id_str'),
      orm.ActionPermission('8', orm.Action.build_key('8', 'accept'), True,
                           'entity._original.namespace_entity._original.state == "active" and user.key_id_str == entity._original.key_id_str and entity._original.state == "invited"'),
      orm.ActionPermission('8', orm.Action.build_key('8', 'clean_roles'), False, 'False'),
      orm.ActionPermission('8', orm.Action.build_key('8', 'clean_roles'), True,
                           'entity._original.namespace_entity._original.state == "active" and user._is_taskqueue'),
      orm.FieldPermission('8', ['name', 'roles', 'state', '_primary_email', '_records'], False, False,
                          'entity._original.namespace_entity._original.state != "active"'),
      orm.FieldPermission('8', ['state'], False, None, 'True'),
      orm.FieldPermission('8', ['roles'], False, None,
                          'entity._original.key_id_str == entity._original.namespace_entity._original.primary_contact.entity._original.key_id_str'),
      orm.FieldPermission('8', ['state'], True, None,
                          '(action.key_id_str == "invite" and entity.state == "invited") or (action.key_id_str == "accept" and entity.state == "accepted")')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('8', 'prepare'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6')
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_domainuser'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('8', 'invite'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6'),
        'name': orm.SuperStringProperty(required=True),
        'email': orm.SuperStringProperty(required=True),
        'roles': orm.SuperKeyProperty(kind='60', repeated=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            DomainUserInviteSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Write(cfg={'path': '_user'}),
            Set(cfg={'d': {'output.entity': '_domainuser'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('8', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='8', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_domainuser'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('8', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='8', required=True),
        'name': orm.SuperStringProperty(required=True),
        'roles': orm.SuperKeyProperty(kind='60', repeated=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            DomainUserUpdateSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_domainuser'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('8', 'remove'),
      arguments={
        'key': orm.SuperKeyProperty(kind='8', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            DomainUserRemoveSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'path': '_user'}),
            Delete(),
            Set(cfg={'d': {'output.entity': '_domainuser'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('8', 'search'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['IN'], 'type': orm.SuperKeyProperty(kind='8', repeated=True)},
            'name': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': orm.SuperStringProperty(choices=['invited', 'accepted'])}
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
                           'output._cursor': '_cursor',
                           'output._more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('8', 'accept'),
      arguments={
        'key': orm.SuperKeyProperty(kind='8', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_domainuser.state': 'accepted'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            CallbackNotify(),
            CallbackExec()
            ]
          ),
        orm.PluginGroup(
          plugins=[
            Set(cfg={'d': {'_domain': '_domainuser.namespace_entity'}}),
            RulePrepare(),  # @todo Should run out of transaction!!!
            RulePrepare(cfg={'path': '_domain'}),  # @todo Should run out of transaction!!!
            Set(cfg={'d': {'output.entity': '_domainuser',
                           'output.domain': '_domain'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('8', 'clean_roles'),
      arguments={
        'key': orm.SuperKeyProperty(kind='8', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            DomainUserCleanRolesSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write()
            ]
          )
        ]
      )
    ]
  
  def _get_primary_email_async(self):
    return orm.Key('0', long(self.key_id_str)).get_async()
