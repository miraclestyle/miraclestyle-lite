# -*- coding: utf-8 -*-
'''
Created on Apr 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import collections

from app import ndb, settings
from app.srv import event
from app.plugins import log, callback


class ActionDenied(Exception):
  
  def __init__(self, context):
    self.message = {'action_denied': context.action}


def _is_structured_field(field):
  """Checks if the provided field is instance of one of the structured properties,
  and if the '_modelclass' is set.
  
  """
  return isinstance(field, (ndb.SuperStructuredProperty, ndb.SuperLocalStructuredProperty)) and field._modelclass

def _write_helper(permissions, entity, field_key, field, field_value):
  """If the field is writable, ignore substructure permissions and override field fith new values.
  Otherwise go one level down and check again.
  
  """
  if (field_key in permissions) and (permissions[field_key]['writable']):
    try:
      setattr(entity, field_key, field_value)
    except ndb.ComputedPropertyError:
      pass
  else:
    if _is_structured_field(field):
      child_entity = getattr(entity, field_key)
      for child_field_key, child_field in field.get_model_fields().items():
        if field._repeated:
          for i, child_entity_item in enumerate(child_entity):
            try:
              child_field_value = getattr(field_value[i], child_field_key)
              _write_helper(permissions[field_key], child_entity_item, child_field_key, child_field, child_field_value)
            except IndexError as e:
              pass
        else:
          _write_helper(permissions[field_key], child_entity, child_field_key, child_field, getattr(field_value, child_field_key))

def write(entity, values):
  entity_fields = entity.get_fields()
  for field_key, field in entity_fields.items():
    if field_key in values:
      field_value = values.get(field_key)
      _write_helper(entity._field_permissions, entity, field_key, field, field_value)

def _read_helper(permissions, entity, field_key, field):
  """If the field is invisible, ignore substructure permissions and remove field along with entire substructure.
  Otherwise go one level down and check again.
  
  """
  if (not field_key in permissions) or (not permissions[field_key]['visible']):
    entity.remove_output(field_key)
  else:
    if _is_structured_field(field):
      child_entity = getattr(entity, field_key)
      if field._repeated:
        if child_entity is not None:  # @todo We'll see how this behaves for def write as well, because None is sometimes here when they are expando properties.
          for child_entity_item in child_entity:
            child_fields = child_entity_item.get_fields()
            child_fields.update(dict([(p._code_name, p) for _, p in child_entity_item._properties.items()]))
            for child_field_key, child_field in child_fields.items():
              _read_helper(permissions[field_key], child_entity_item, child_field_key, child_field)
      else:
        child_entity = getattr(entity, field_key)
        if child_entity is not None:  # @todo We'll see how this behaves for def write as well, because None is sometimes here when they are expando properties.
          child_fields = child_entity.get_fields()
          child_fields.update(dict([(p._code_name, p) for _, p in child_entity._properties.items()]))
          for child_field_key, child_field in child_fields.items():
            _read_helper(permissions[field_key], child_entity, child_field_key, child_field)

def read(entity):
  entity_fields = entity.get_fields()
  for field_key, field in entity_fields.items():
    _read_helper(entity._field_permissions, entity, field_key, field)

def reset_actions(action_permissions, actions):
  for action_key in actions:
    action_permissions[action_key] = {'executable': []}

def reset_fields(field_permissions, fields):
  for field_key, field in fields.items():
    if field_key not in field_permissions:
      field_permissions[field_key] = collections.OrderedDict([('writable', []), ('visible', [])])
    if _is_structured_field(field):
      model_fields = field.get_model_fields()
      if field._code_name in model_fields:
        model_fields.pop(field._code_name)  # @todo Test this behaviour!
      reset_fields(field_permissions[field_key], model_fields)

def reset(entity):
  """This method builds dictionaries that will hold permissions inside
  entity object.
  
  """
  entity._action_permissions = {}
  entity._field_permissions = {}
  actions = entity.get_actions()
  fields = entity.get_fields()
  reset_actions(entity._action_permissions, actions)
  reset_fields(entity._field_permissions, fields)

def decide(permissions, strict, root=True, parent_permissions=None):
  for key, value in permissions.items():
    if isinstance(value, dict):
      if parent_permissions:
        root = False
      decide(permissions[key], strict, root, permissions)
    else:
      if isinstance(value, list) and len(value):
        if (strict):
          if all(value):
            permissions[key] = True
          else:
            permissions[key] = False
        elif any(value):
          permissions[key] = True
        else:
          permissions[key] = False
      else:
        permissions[key] = None
        if not root and not len(value):
          permissions[key] = parent_permissions[key]

def override_local_permissions(global_permissions, local_permissions):
  for key, value in local_permissions.items():
    if isinstance(value, dict):
      override_local_permissions(global_permissions[key], local_permissions[key])  # global_permissions[key] will fail in case global and local permissions are (for some reason) out of sync!
    else:
      if key in global_permissions:
        gp_value = global_permissions[key]
        if gp_value is not None and gp_value != value:
          local_permissions[key] = gp_value
      if local_permissions[key] is None:
        local_permissions[key] = False

def complement_local_permissions(global_permissions, local_permissions):
  for key, value in global_permissions.items():
    if isinstance(value, dict):
      complement_local_permissions(global_permissions[key], local_permissions[key])  # local_permissions[key] will fail in case global and local permissions are (for some reason) out of sync!
    else:
      if key not in local_permissions:
        local_permissions[key] = value

def compile_global_permissions(global_permissions):
  for key, value in global_permissions.items():
    if isinstance(value, dict):
      compile_global_permissions(global_permissions[key])
    else:
      if value is None:
        value = False
      global_permissions[key] = value

def compile(global_permissions, local_permissions, strict):
  decide(global_permissions, strict)
  # If local permissions are present, process them.
  if local_permissions:
    decide(local_permissions, strict)
    # Iterate over local permissions, and override them with the global permissions.
    override_local_permissions(global_permissions, local_permissions)
    # Make sure that global permissions are always present.
    complement_local_permissions(global_permissions, local_permissions)
    permissions = local_permissions
  # Otherwise just process global permissions.
  else:
    compile_global_permissions(global_permissions)
    permissions = global_permissions
  return permissions

def prepare(context, skip_user_roles, strict):
  """This method generates permissions situation for the context.entity object,
  at the time of execution.
  
  """
  if context.entity:
    reset(context.entity)
    if hasattr(context.entity, '_global_role') and context.entity._global_role.get_kind() == '67':
      context.entity._global_role.run(context)
    # Copy generated entity permissions to separate dictionary.
    global_action_permissions = context.entity._action_permissions.copy()
    global_field_permissions = context.entity._field_permissions.copy()
    # Reset permissions structures.
    reset(context.entity)
    local_action_permissions = {}
    local_field_permissions = {}
    if not skip_user_roles:
      if not context.user._is_guest:
        domain_user_key = ndb.Key('8', context.user.key_id_str, namespace=context.entity.key_namespace)
        domain_user = domain_user_key.get()
        clean_roles = False
        if domain_user and domain_user.state == 'accepted':
          roles = ndb.get_multi(domain_user.roles)
          for role in roles:
            if role is None:
              clean_roles = True
            else:
              if role.active:
                role.run(context)
          if clean_roles:
            payload = callback.Payload(queue='callback',
                                       internal_fields={'action_model': '8',
                                                        'action_key': 'clean_roles',
                                                        'caller_user': context.user.key.urlsafe(),
                                                        'caller_action': context.action.key.urlsafe(),
                                                        'key': domain_user.key.urlsafe()})
            callback.execute(context, payload)
        # Copy generated entity permissions to separate dictionary.
        local_action_permissions = context.entity._action_permissions.copy()
        local_field_permissions = context.entity._field_permissions.copy()
        # Reset permissions structures.
        reset(context.entity)
    context.entity._action_permissions = compile(global_action_permissions, local_action_permissions, strict)
    context.entity._field_permissions = compile(global_field_permissions, local_field_permissions, strict)
    context.entity.add_output('_action_permissions')
    context.entity.add_output('_field_permissions')


class Prepare(event.Plugin):
  
  prepare_entities = ndb.SuperStringProperty('4', indexed=False, repeated=True)
  skip_user_roles = ndb.SuperBooleanProperty('5', indexed=False, required=True, default=True)
  strict = ndb.SuperBooleanProperty('6', indexed=False, required=True, default=True)
  
  def run(self, context):
    if context.entities:
      if isinstance(context.entities, dict):
        if len(self.prepare_entities):
          for kind_id in self.prepare_entities:
            if kind_id in context.entities:
              context.rule.entity = context.entities[kind_id]  # @todo This line is temporary!
              context.entity = context.entities[kind_id]
              prepare(context, self.skip_user_roles, self.strict)
        else:
          context.rule.entity = context.entities[context.model.get_kind()]  # @todo This line is temporary!
          context.entity = context.entities[context.model.get_kind()]
          prepare(context, self.skip_user_roles, self.strict)
      elif isinstance(context.entities, list):
        for entity in context.entities:
          context.rule.entity = entity  # @todo This line is temporary!
          context.entity = entity
          prepare(context, self.skip_user_roles, self.strict)


class Read(event.Plugin):
  
  read_entities = ndb.SuperStringProperty('4', indexed=False, repeated=True)
  
  def run(self, context):
    if context.entities:
      if isinstance(context.entities, dict):
        if len(self.read_entities):
          for kind_id in self.read_entities:
            if kind_id in context.entities:
              read(context.entities[kind_id])
        else:
          read(context.entities[context.model.get_kind()])
      elif isinstance(context.entities, list):
        for entity in context.entities:
          read(entity)


class Write(event.Plugin):
  
  write_entities = ndb.SuperStringProperty('4', indexed=False, repeated=True)
  
  def run(self, context):
    if context.entities:
      if isinstance(context.entities, dict):
        if len(self.write_entities):
          for kind_id in self.write_entities:
            if kind_id in context.entities:  # @todo Do we check context.values as well?
              write(context.entities[kind_id], context.values[kind_id])
        else:
          write(context.entities[context.model.get_kind()], context.values[context.model.get_kind()])
      elif isinstance(context.entities, list):  # @todo Not sure if this is usefull at all?
        for i, entity in enumerate(context.entities):
          write(entity, context.values[i])


class Exec(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('4', indexed=False, required=False)
  
  def run(self, context):
    if context.entities:
      if isinstance(context.entities, dict):
        if self.kind_id != None:
          if not context.entities[self.kind_id]._action_permissions[context.action.key.urlsafe()]['executable']:
            raise ActionDenied(context)
        else:
          if not context.entities[context.model.get_kind()]._action_permissions[context.action.key.urlsafe()]['executable']:
            raise ActionDenied(context)
      else:
        raise ActionDenied(context)
    else:
      raise ActionDenied(context)
