# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.lib.safe_eval import safe_eval
from app.srv.event import Action
from app.srv import log as ndb_log
from app.plugins import common, rule, log, callback


def _parse_field(values, field_path):
  """Returns part of the 'values' that coresponds to the ending node of the given field path.
  'field_path' is a string that takes dot notation form ('foo.bar.far').
  It is assumed that 'values' is a structure that contains mixture of objects and dictionaries along the given path.
  
  """
  fields = field_path.split('.')
  for field in fields:
    if isinstance(values, dict):
      try:
        values = values[field]
      except KeyError as e:
        return None
    else:
      try:
        values = getattr(values, field)
      except ValueError as e:
        return None
  return values


class Permission():
  """Base class for all permissions.
  If the futuer deems scaling a problem, possible solutions could be to:
  a) Create DomainUserPermissions entity, taht will fan-out on DomainUser entity,
  and will contain all permissions for the domain user (based on it's domain role membership) in it;
  b) Transform this class to BasePolyExpando, so it can be indexed and queried (by model kind, by action...), 
  and store each permission in datasotre as child entity of DomainUser;
  c) Some other similar pattern.
  
  """


class ActionPermission(Permission):
  
  def __init__(self, kind, actions, executable=None, condition=None):
    if not isinstance(actions, (tuple, list)):
      actions = [actions]
    self.kind = kind  # Entity kind identifier (entity._kind).
    self.actions = actions  # List of action urlsafe keys.
    self.executable = executable
    self.condition = condition
  
  def get_output(self):
    return {'kind': self.kind, 'actions': self.actions,
            'executable': self.executable, 'condition': self.condition, 'type': self.__class__.__name__}
  
  def run(self, role, context):
    if (self.kind == context.entity.get_kind()):
      for action in self.actions:
        if (action in context.entity.get_actions()) and (safe_eval(self.condition, {'context': context, 'action': action})) and (self.executable != None):
          context.entity._action_permissions[action]['executable'].append(self.executable)


class FieldPermission(Permission):
  
  def __init__(self, kind, fields, writable=None, visible=None, condition=None):
    if not isinstance(fields, (tuple, list)):
      fields = [fields]
    self.kind = kind  # Entity kind identifier (entity._kind).
    self.fields = fields  # List of field code names from ndb property (field._code_name).
    self.writable = writable
    self.visible = visible
    self.condition = condition
  
  def get_output(self):
    return {'kind': self.kind, 'fields': self.fields, 'writable': self.writable,
            'visible': self.visible, 'condition': self.condition, 'type': self.__class__.__name__}
  
  def run(self, role, context):
    if (self.kind == context.entity.get_kind()):
      for field in self.fields:
        parsed_field = _parse_field(context.entity._field_permissions, field)  # Retrieves field value from foo.bar.far
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
  permissions = ndb.SuperPickleProperty('3', required=True, compressed=False)  # List of Permissions instances. Validation is required against objects in this list, if it is going to be stored in datastore.
  
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
      ActionPermission('60', Action.build_key('60', 'prepare').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('60', Action.build_key('60', 'create').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active' or context.entity.key_id_str == 'admin'"),
      ActionPermission('60', Action.build_key('60', 'read').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('60', Action.build_key('60', 'update').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active' or context.entity.key_id_str == 'admin'"),
      ActionPermission('60', Action.build_key('60', 'delete').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active' or context.entity.key_id_str == 'admin'"),
      ActionPermission('60', Action.build_key('60', 'search').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('60', Action.build_key('60', 'read_records').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      FieldPermission('60', ['name', 'active', 'permissions', '_records'], False, None,
                      "context.entity.namespace_entity.state != 'active' or context.entity.key_id_str == 'admin'"),
      FieldPermission('60', ['name', 'active', 'permissions', '_records'], None, False,
                      "context.entity.namespace_entity.state != 'active'")
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
        common.Prepare(domain_model=True),
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
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.DomainRoleSet(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.60'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.60.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
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
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.60.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
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
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.60.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('60', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "name", "operator": "asc"}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty()}
            },
          indexes=[
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name', 'active'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
            }
          ),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('60', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.60', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      )
    ]


class DomainUser(ndb.BaseModel):
  
  _kind = 8
  
  name = ndb.SuperStringProperty('1', required=True)
  roles = ndb.SuperKeyProperty('2', kind=DomainRole, repeated=True)  # It's important to ensure that this list doesn't contain duplicate role keys, since taht can pose security issue!!
  state = ndb.SuperStringProperty('3', required=True, choices=['invited', 'accepted'])
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('8', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('8', Action.build_key('8', 'prepare').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('8', Action.build_key('8', 'invite').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('8', Action.build_key('8', 'read').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('8', Action.build_key('8', 'update').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('8', Action.build_key('8', 'remove').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active' or context.entity.key_id_str == context.entity.namespace_entity.primary_contact.entity.key_id_str"),
      ActionPermission('8', Action.build_key('8', 'remove').urlsafe(), True,
                       "(context.entity.namespace_entity.state == 'active' and context.user.key_id_str == context.entity.key_id_str) and not (context.entity.key_id_str == context.entity.namespace_entity.primary_contact.entity.key_id_str)"),
      ActionPermission('8', Action.build_key('8', 'search').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('8', Action.build_key('8', 'read_records').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('8', Action.build_key('8', 'accept').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active' or context.user.key_id_str != context.entity.key_id_str"),
      ActionPermission('8', Action.build_key('8', 'accept').urlsafe(), True,
                       "context.entity.namespace_entity.state == 'active' and context.user.key_id_str == context.entity.key_id_str and context.entity.state == 'invited'"),
      ActionPermission('8', Action.build_key('8', 'clean_roles').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active' or not context.user._is_taskqueue"),
      ActionPermission('8', Action.build_key('8', 'clean_roles').urlsafe(), True,
                       "context.entity.namespace_entity.state == 'active' and context.user._is_taskqueue"),
      FieldPermission('8', ['name', 'roles', 'state', '_records'], False, False,
                      "context.entity.namespace_entity.state != 'active'"),
      FieldPermission('8', ['roles'], False, None,
                      "context.entity.key_id_str == context.entity.namespace_entity.primary_contact.entity.key_id_str"),
      FieldPermission('8', ['state'], False, None,
                      "context.entity.namespace_entity.state == 'active'"),
      FieldPermission('8', ['state'], True, None,
                      "(context.action.key_id_str == 'invite' and context.value and context.value.state == 'invited') or (context.action.key_id_str == 'accept' and context.value and context.value.state == 'accepted')")
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
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'output.entity': 'entities.8'}),
        rule.SelectRoles()
        ]
      ),
    Action(
      key=Action.build_key('8', 'invite'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6'),
        'name': ndb.SuperStringProperty(required=True),
        'email': ndb.SuperStringProperty(required=True),
        'roles': ndb.SuperKeyProperty(kind=DomainRole, repeated=True)
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
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.8.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
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
        common.Set(dynamic_values={'output.entity': 'entities.8'}),
        rule.SelectRoles()
        ]
      ),
    Action(
      key=Action.build_key('8', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'roles': ndb.SuperKeyProperty(kind=DomainRole, repeated=True)
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
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.8.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
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
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.8.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('8', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "name", "operator": "asc"}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty(choices=['invited', 'accepted'])},
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
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('8', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.8', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
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
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.8.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
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
