# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.lib.safe_eval import safe_eval
from app.lib.attribute_manipulator import set_attr, get_attr
from app.srv.event import Action
from app.srv import log as ndb_log
from app.plugins import common, rule, log, callback


class Permission(ndb.BasePolyExpando):
  '''Base class for all permissions.
  If the futuer deems scaling to be a problem, possible solutions could be to:
  a) Create DomainUserPermissions entity, that will fan-out on DomainUser entity,
  and will contain all permissions for the domain user (based on it's domain role membership) in it;
  b) Transform this class to BasePolyExpando, so it can be indexed and queried (by model kind, by action...),
  and store each permission in datasotre as child entity of DomainUser;
  c) Some other similar pattern.
  
  '''
  _kind = 78
  
  _default_indexed = False


class ActionPermission(Permission):
  
  _kind = 79
  
  kind = ndb.SuperStringProperty('1', required=True, indexed=False)
  actions = ndb.SuperKeyProperty('2', kind='56', repeated=True, indexed=False)
  executable = ndb.SuperBooleanProperty('3', required=True, default=True, indexed=False)
  condition = ndb.SuperStringProperty('4', required=True, indexed=False)
  
  def __init__(self, *args, **kwargs):
    super(ActionPermission, self).__init__(**kwargs)
    if len(args):
      kind, actions, executable, condition = args
      if not isinstance(actions, (tuple, list)):
        actions = [actions]
      self.kind = kind
      self.actions = actions
      self.executable = executable
      self.condition = condition
  
  def run(self, role, context):
    if (self.kind == context.entity.get_kind()):
      for action in self.actions:
        if (action.urlsafe() in context.entity.get_actions()) and (safe_eval(self.condition, {'context': context, 'action': action})) and (self.executable != None):
          context.entity._action_permissions[action.urlsafe()]['executable'].append(self.executable)


class FieldPermission(Permission):
  
  _kind = 80
  
  kind = ndb.SuperStringProperty('1', required=True, indexed=False)
  fields = ndb.SuperStringProperty('2', repeated=True, indexed=False)
  writable = ndb.SuperBooleanProperty('3', required=True, default=True, indexed=False)
  visible = ndb.SuperBooleanProperty('4', required=True, default=True, indexed=False)
  condition = ndb.SuperStringProperty('5', required=True, indexed=False)
  
  def __init__(self, *args, **kwargs):
    super(FieldPermission, self).__init__(**kwargs)
    if len(args):
      kind, fields, writable, visible, condition = args
      if not isinstance(fields, (tuple, list)):
        fields = [fields]
      self.kind = kind
      self.fields = fields
      self.writable = writable
      self.visible = visible
      self.condition = condition
  
  def run(self, role, context):
    if (self.kind == context.entity.get_kind()):
      for field in self.fields:
        parsed_field = get_attr(context.entity._field_permissions, field)  # Retrieves field value from foo.bar.far
        if parsed_field and (safe_eval(self.condition, {'context': context, 'field': field})):
          if (self.writable != None):
            parsed_field['writable'].append(self.writable)
          if (self.visible != None):
            parsed_field['visible'].append(self.visible)


class Role(ndb.BaseExpando):
  
  _kind = 66
  
  # feature proposition (though it should create overhead due to the required drilldown process!)
  # parent_record = ndb.SuperKeyProperty('1', kind='Role', indexed=False)
  # complete_name = ndb.SuperTextProperty('2')
  name = ndb.SuperStringProperty('1', required=True)
  active = ndb.SuperBooleanProperty('2', required=True, default=True)
  permissions = ndb.SuperPickleProperty('3', required=True, indexed=False, compressed=False)  # List of Permissions instances. Validation is required against objects in this list, if it is going to be stored in datastore.
  
  _default_indexed = False
  
  def run(self, context):
    for permission in self.permissions:
      permission.run(self, context)


class GlobalRole(Role):
  
  _kind = 67


class DomainRole(Role):
  
  _kind = 60
  
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('60', repeated=True)
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
                              Action.build_key('60', 'delete')], False, 'context.entity.key_id_str == "admin"'),
      FieldPermission('60', ['name', 'active', 'permissions', '_records'], False, None,
                      'context.entity.namespace_entity.state != "active" or context.entity.key_id_str == "admin"'),
      FieldPermission('60', ['name', 'active', 'permissions', '_records'], None, False,
                      'context.entity.namespace_entity.state != "active"')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('60', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'output.entity': 'entities.60'})
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
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.DomainRoleSet(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.60'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.60.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('60', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.60'})
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
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.DomainRoleSet(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.60'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.60.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('60', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Delete(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.60'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.60.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
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
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(page_size=settings.SEARCH_PAGE),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities',
                                   'output.search_cursor': 'search_cursor',
                                   'output.search_more': 'search_more'})
        ]
      ),
    Action(
      key=Action.build_key('60', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(page_size=settings.RECORDS_PAGE),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.60',
                                   'output.log_read_cursor': 'log_read_cursor',
                                   'output.log_read_more': 'log_read_more'})
        ]
      )
    ]


class DomainUser(ndb.BaseExpando):
  
  _kind = 8
  
  name = ndb.SuperStringProperty('1', required=True)
  roles = ndb.SuperKeyProperty('2', kind='60', repeated=True)  # It's important to ensure that this list doesn't contain duplicate role keys, since that can pose security issue!!
  state = ndb.SuperStringProperty('3', required=True, choices=['invited', 'accepted'])
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('8', repeated=True)
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
      FieldPermission('8', ['name', 'roles', 'state', '_records'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('8', ['roles'], False, None,
                      'context.entity.key_id_str == context.entity.namespace_entity.primary_contact.entity.key_id_str'),
      FieldPermission('8', ['state'], False, None,
                      'context.entity.namespace_entity.state == "active"'),
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
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'output.entity': 'entities.8'})
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
      _plugins=[
        common.Context(),
        rule.DomainUserInvite(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True, write_entities=['8', '0']),
        log.Entity(transactional=True, log_entities=['8', '0']),
        log.Write(transactional=True),
        rule.Read(),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.8'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.8.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('8', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.8'})
        ]
      ),
    Action(
      key=Action.build_key('8', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'roles': ndb.SuperKeyProperty(kind='60', repeated=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.DomainUserUpdate(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.8'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.8.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('8', 'remove'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.DomainUserRemove(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Write(transactional=True, write_entities=['0']),
        common.Delete(transactional=True),
        log.Entity(transactional=True, log_entities=['8', '0']),
        log.Write(transactional=True),
        rule.Read(),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.8'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.8.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('8', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty(choices=['invited', 'accepted'])}
            },
          indexes=[
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
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(page_size=settings.SEARCH_PAGE),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities',
                                   'output.search_cursor': 'search_cursor',
                                   'output.search_more': 'search_more'})
        ]
      ),
    Action(
      key=Action.build_key('8', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(page_size=settings.RECORDS_PAGE),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.8',
                                   'output.log_read_cursor': 'log_read_cursor',
                                   'output.log_read_more': 'log_read_more'})
        ]
      ),
    Action(
      key=Action.build_key('8', 'accept'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(static_values={'values.8.state': 'accepted'}),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        common.Set(transactional=True,
                   dynamic_values={'entities.6': 'entities.8.namespace_entity', 'values.6': 'entities.8.namespace_entity'}),
        rule.Prepare(transactional=True, prepare_entities=['8', '6'], skip_user_roles=False, strict=False),
        rule.Read(transactional=True, read_entities=['8', '6']),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.8', 'output.domain': 'entities.6'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.8.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('8', 'clean_roles'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.DomainUserCleanRoles(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True)
        ]
      )
    ]
