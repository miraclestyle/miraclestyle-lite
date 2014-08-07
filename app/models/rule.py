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
        'permissions': orm.SuperMultiLocalStructuredProperty(('80', '79'), repeated=True),
        'active': orm.SuperBooleanProperty(default=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_domainrole.name': 'input.name',
                           '_domainrole.active': 'input.active',
                           '_domainrole.permissions': 'input.permissions'}}),
            RulePrepare(),
            RuleExec()
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
        'key': orm.SuperKeyProperty(kind='60', required=True),
        'read_arguments': orm.SuperJsonProperty()
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
        'permissions': orm.SuperMultiLocalStructuredProperty(('80', '79'), repeated=True),
        'active': orm.SuperBooleanProperty(default=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_domainrole.name': 'input.name',
                           '_domainrole.active': 'input.active',
                           '_domainrole.permissions': 'input.permissions'}}),
            RulePrepare(),
            RuleExec()
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
          default={'filters': [], 'orders': [{'field': 'name', 'operator': 'asc'}]},
          cfg={
            'search_by_keys': True,
            'search_arguments': {'kind': '60', 'options': {'limit': settings.SEARCH_PAGE}},
            'filters': {'name': orm.SuperStringProperty(),
                        'active': orm.SuperBooleanProperty()},
            'indexes': [{'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('name', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('active', ['=='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('active', ['==']), ('name', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]}]
            }
          )
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Search(),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
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
    '_primary_email': orm.SuperReferenceProperty(callback=lambda self: self._get_user_async(),
                                                 format_callback=lambda self, value: value._primary_email),
    '_user': orm.SuperStorageStructuredProperty('0', updateable=False, deleteable=False,
                                                storage='reference', autoload=False,
                                                storage_config={'callback': lambda self: self._get_user_async()}),
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
                          '(action.key_id_str == "invite" and entity.state == "invited") or (action.key_id_str == "accept" and entity.state == "accepted")'),
      orm.FieldPermission('8', ['state'], None, True,
                          'action.key_id_str == "read_domains" and user.key_id_str == entity._original.key_id_str')
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
        'key': orm.SuperKeyProperty(kind='8', required=True),
        'read_arguments': orm.SuperJsonProperty()
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
        'roles': orm.SuperKeyProperty(kind='60', repeated=True),
        'read_arguments': orm.SuperJsonProperty()
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
          default={'filters': [], 'orders': [{'field': 'name', 'operator': 'asc'}]},
          cfg={
            'search_by_keys': True,
            'search_arguments': {'kind': '8', 'options': {'limit': settings.SEARCH_PAGE}},
            'filters': {'name': orm.SuperStringProperty(),
                        'state': orm.SuperStringProperty(choices=['invited', 'accepted'])},
            'indexes': [{'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('name', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!=']), ('name', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]}]
            }
          )
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Search(),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
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
            RulePrepare(),
            RulePrepare(cfg={'path': '_domain'}),
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
  
  def _get_user_async(self):
    return orm.Key('0', long(self.key_id_str)).get_async()
