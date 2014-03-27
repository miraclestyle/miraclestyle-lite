# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import collections

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, util, settings
from app.lib.safe_eval import safe_eval
from app.srv import event, log, callback


"""
This file is used to control input, and output trough the application Model actions.

Examples:
 

from app.srv import rule, event

class OtherModel2(ndb.BaseModel):

   name = ndb.SuperStringProperty()


class OtherModel(ndb.BaseModel):

   name = ndb.SuperStringProperty()
   other = ndb.SuperStructuredProperty(OtherModel2)

class Model(ndb.BaseModel):

   foo = ndb.SuperStringProperty()
   bar = ndb.SuperStructuredProperty(OtherModel)

   _virtual_fields = {
     'my_magic_field' : ndb.SuperComputedProperty(lambda self: 'this field does magic!')
   }
 
   
   _global_role = rule.GlobalRole(permissions=[
                                  
                                  Action permissions:
                                  
                                  work very simple, its a key-value checking system with conditions
                                  rule.ActionPermission('0', event.Action.build_key('0-0').urlsafe(), True, "context variable available, valid any `simple` python expression"),
                                  
                                  
                                  Field permissions:
                              
                                  rule.FieldPermission('0', 'bar', True, True, 'True'), 
                                  
                                  This field permission definition would generate:
                                  
                                   bar : {
                                     writable : True,
                                     required : True,
                                     visible : True,
                                     name : {
                                         writable : True,
                                         required : True,
                                         visible : True,
                                     },
                                     
                                     other : {
                                        writable : True,
                                        required : True,
                                        visible : True,
                                        name : {
                                          writable : True,
                                          required : True,
                                          visible : True,
                                        }
                                        
                                     }
                                  }
                                  
                                  If you specify rule like this
                                  
                                  rule.FieldPermission('0', 'bar.other.name', False, False, 'True'),
                                  
                                  This field permission definition would generate:
                                  
                                   bar : {
                                     writable : True,
                                     required : True,
                                     visible : True,
                                     name : {
                                         writable : True,
                                         required : True,
                                         visible : True,
                                     },
                                     
                                     other : {
                                        writable : True,
                                        required : True,
                                        visible : True,
                                        name : {
                                          writable : False,
                                          required : False,
                                          visible : False,
                                        }
                                      
                                     }
                                  }
                                   
                                  rule.FieldPermission('0', ['my_magic_field', 'foo', 'bar'])
                                  
  _actions = {
     'friendly_action_name' : event.Action(id='0-0',
                                           arguments={
                                             'my_input_name' : ndb.<Any NDB property that begins with `Super`>
                                           })
    
  }
  
  @classmethod
  def friendly_action_name(context):
      
      Now, rule engine will only work if the entity is set into the context like so
      
      context.rule.entity = entity
      
      `entity` must be an instance of any subclass of ndb.Base<Type> 
        and it should have _global_role if its not part of domain
        
      By default all actions and field permissions are False, only way to override that is to define rules for each of 
      the types, either field or action
      
      
      
      .....
      
      
      rule.write function should be used before doing entity.put()
      
      the rule.write will ensure that there wont be illegal property changes to the entity before putting.
      
      the rule.write will only set the value(s) if the conditions are met from the rule engine - entity._field_permissons
      
      there is a problem that comes with repeated Structured properties:
 
      when the rule.write is fired it wont be a problem to update existing properties in the list (respecting the field perms)
      
      the problem is if the additional item is added into the list, in that case if the structured property permission is not
      set to writable that item will not get appended into the list
      
      
      ....
      
      rule.read works on system of elimination, if the property is not visible, it will be hidden from output,
      
      if the property is structured, it will check its fields recursively until they are all hidden if needed.
          
"""


class DomainUserError(Exception):
  
  def __init__(self, message):
    self.message = {'domain_user': message}


class ActionDenied(Exception):
  
  def __init__(self, context):
    self.message = {'action_denied': context.action}


def _is_structured_field(field):
  """Checks if the provided field is instance of one of the structured properties,
  and if the '_modelclass' is set.
  
  """
  return isinstance(field, (ndb.SuperStructuredProperty, ndb.SuperLocalStructuredProperty)) and field._modelclass

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

def _check_field(context, fields, prop):  # Not sure if 'prop' cause confusion, 'property' in this case is propetry of the field itself!
  """Internal helper to check if the field for provided rule context is
  either writable or invisible.
  
  """
  if context.rule.entity:
    # This arangement allows us to call parent functions in the manner like this: writable(context, ('field1', 'field2')).
    if not isinstance(fields, (tuple, list)):
      fields = (fields, )
    results = []
    for field in fields:
      result = _parse_field(context.rule.entity._field_permissions, field)
      results.append(result[prop])
    return all(results)
  else:
    return False

def writable(context, field):
  """Checks if the field is writable for given context."""
  return _check_field(context, field, 'writable')

def visible(context, field):
  """Checks if the field is visible for given context."""
  return _check_field(context, field, 'visible')

def executable(context):
  """Checks if the action is executable for given context."""
  if context.rule.entity:
    return context.rule.entity._action_permissions[context.action.key.urlsafe()]['executable']
  else:
    return False

def _write_helper(field_permissions, field_key, field, field_value, parent_value=None, parent=None, position=None):
  if _is_structured_field(field):
    if position is not None:
      try:
        sub_entity = getattr(parent_value[position], field_key)
      except IndexError as e:
        sub_entity = parent._modelclass()
        parent_value.append(sub_entity)
    else:
      sub_entity = getattr(parent_value, field_key)
    if field._repeated:
      for i, value in enumerate(field_value):
        for sub_field_key, sub_field in field.get_model_fields().items():
          sub_field_value = getattr(value, sub_field_key)
          _write_helper(field_permissions[field_key], sub_field_key, sub_field, sub_field_value, sub_entity, field, i)
      return
    else:
      for sub_field_key, sub_field in field.get_model_fields().items():
        sub_field_value = getattr(sub_entity, sub_field_key)
        _write_helper(field_permissions[field_key], sub_field_key, sub_field, sub_field_value, sub_entity, field, i)
  else:
    if (field_key in field_permissions) and (field_permissions[field_key]['writable']):
      if position is not None and isinstance(parent_value, list):
         try:
           sub_entity = parent_value[position]
         except IndexError as e:
           sub_entity = parent._modelclass()
           parent_value.append(sub_entity)
         setattr(sub_entity, field_key, field_value)
      else:
        try:
          setattr(parent_value, field_key, field_value)
        except ndb.ComputedPropertyError:
          pass

def write(entity, values):
  entity_fields = entity.get_fields()
  for field_key, field_value in values.items():
    if field_key in entity_fields:
      field = entity_fields.get(field_key)
      _write_helper(entity._field_permissions, field_key, field, field_value, entity)

def _read_helper(field_permissions, entity, field_key, field):
  if _is_structured_field(field):
    values = getattr(entity, field_key)
    if field._repeated and isinstance(values, list):
      for value in values:
        sub_fields = value.get_fields()
        sub_fields.update(dict([(p._code_name, p) for _, p in value._properties.items()]))
        for sub_field_key, sub_field in sub_fields.items():
          _read_helper(field_permissions[field_key], value, sub_field_key, sub_field)
    else:
      value = getattr(entity, field_key)
      if value is not None:
        sub_fields = value.get_fields()
        sub_fields.update(dict([(p._code_name, p) for _, p in value._properties.items()]))
        for sub_field_key, sub_field in sub_fields.items():
          _read_helper(field_permissions[field_key], value, sub_field_key, sub_field)
  else:
    if (not field_key in field_permissions) or (not field_permissions[field_key]['visible']):
      entity.remove_output(field_key)

def read(entity):
  entity_fields = entity.get_fields()
  for field_key, field in entity_fields.items():
    _read_helper(entity._field_permissions, entity, field_key, field)
  return entity  # @todo Why this return?


class Context():
  
  def __init__(self):
    self.entity = None


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
    self.actions = actions  # List of action urlsafe keys. @todo This has been renamed from 'action' to 'actions'!
    self.executable = executable
    self.condition = condition
  
  def get_output(self):
    return {'kind': self.kind, 'actions': self.actions,
            'executable': self.executable, 'condition': self.condition, 'type': self.__class__.__name__}
  
  def run(self, role, context):
    for action in self.actions:
      if (self.kind == context.rule.entity.get_kind()) and (action in context.rule.entity.get_actions()) and (safe_eval(self.condition, {'context': context, 'action': action})) and (self.executable != None):
        context.rule.entity._action_permissions[action]['executable'].append(self.executable)


class FieldPermission(Permission):
  
  def __init__(self, kind, fields, writable=None, visible=None, condition=None):
    if not isinstance(fields, (tuple, list)):
      fields = [fields]
    self.kind = kind  # Entity kind identifier (entity._kind).
    self.fields = fields  # List of field code names from ndb property (field._code_name). @todo This has been renamed from 'field' to 'fields'!
    self.writable = writable
    self.visible = visible
    self.condition = condition
  
  def get_output(self):
    return {'kind': self.kind, 'fields': self.fields, 'writable': self.writable,
            'visible': self.visible, 'condition': self.condition, 'type': self.__class__.__name__}
  
  def run(self, role, context):
    for field in self.fields:
      parsed_field = _parse_field(context.rule.entity._field_permissions, field)  # Retrieves field value from foo.bar.far
      if (self.kind == context.rule.entity.get_kind()) and parsed_field and (safe_eval(self.condition, {'context': context, 'field': field})):
        if (self.writable != None):
          parsed_field['writable'].append(self.writable)
        if (self.visible != None):
          parsed_field['visible'].append(self.visible)


class Role(ndb.BaseExpando):
  
  # root (namespace Domain)
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


class Engine:
  
  @classmethod
  def prepare_actions(cls, action_permissions, actions):
    for action_key in actions:
      action_permissions[action_key] = {'executable': []}
  
  @classmethod
  def prepare_fields(cls, field_permissions, fields):  # @todo Check if this version of the function is correct?
    for field_key, field in fields.items():
      if field_key not in field_permissions:
        field_permissions[field_key] = collections.OrderedDict([('writable', []), ('visible', [])])
      if _is_structured_field(field):
        model_fields = field.get_model_fields()
        if field._code_name in model_fields:
          model_fields.pop(field._code_name)  # @todo Test this behaviour!
        cls.prepare_fields(field_permissions[field_key], model_fields)
  
  @classmethod
  def prepare(cls, context):
    """This method builds dictionaries that will hold permissions inside
    context.rule.entity object.
    """
    entity = context.rule.entity
    entity._action_permissions = {}
    entity._field_permissions = {}
    actions = entity.get_actions()
    fields = entity.get_fields()
    cls.prepare_actions(entity._action_permissions, actions)
    cls.prepare_fields(entity._field_permissions, fields)
  
  @classmethod
  def decide(cls, permissions, strict, parent_key=None, parent_permissions=None):  # @todo Perhaps parent_key is not required!
    for key, value in permissions.items():
      if isinstance(value, dict):
        cls.decide(permissions[key], strict, key, permissions)
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
          if parent_key and not len(value):
            permissions[key] = parent_permissions[key]
  
  @classmethod
  def override_local_permissions(cls, global_permissions, local_permissions):
    for key, value in local_permissions.items():
      if isinstance(value, dict):
        cls.override_local_permissions(global_permissions[key], local_permissions[key])  # global_permissions[key] will fail in case global and local permissions are (for some reason) out of sync!
      else:
        if key in global_permissions:
          gp_value = global_permissions[key]
          if gp_value is not None and gp_value != value:
            local_permissions[key] = gp_value
        if local_permissions[key] is None:
          local_permissions[key] = False
  
  @classmethod
  def complement_local_permissions(cls, global_permissions, local_permissions):
    for key, value in global_permissions.items():
      if isinstance(value, dict):
        cls.complement_local_permissions(global_permissions[key], local_permissions[key])  # local_permissions[key] will fail in case global and local permissions are (for some reason) out of sync!
      else:
        if key not in local_permissions:
          local_permissions[key] = value
  
  @classmethod
  def compile_global_permissions(cls, global_permissions):
    for key, value in global_permissions.items():
      if isinstance(value, dict):
        cls.compile_global_permissions(global_permissions[key])
      else:
        if value is None:
          value = False
          global_permissions[key] = values
  
  @classmethod
  def compile(cls, local_permissions, global_permissions, strict):
    cls.decide(global_permissions, strict)
    # If local permissions are present, process them.
    if local_permissions:
      cls.decide(local_permissions, strict)
      # Iterate over local permissions, and override them with the global permissions.
      cls.override_local_permissions(global_permissions, local_permissions)
      # Make sure that global permissions are always present.
      cls.complement_local_permissions(global_permissions, local_permissions)
      permissions = local_permissions
    # Otherwise just process global permissions.
    else:
      cls.compile_global_permissions(global_permissions)
      permissions = global_permissions
    return permissions
  
  @classmethod
  def run(cls, context, skip_user_roles=False, strict=False):
    """This method generates permissions situation for the context.rule.entity object,
    at the time of execution.
    
    """
    if context.rule.entity:
      cls.prepare(context)
      local_action_permissions = {}
      local_field_permissions = {}
      if not skip_user_roles:
        if not context.auth.user._is_guest:
          domain_user_key = DomainUser.build_key(context.auth.user.key_id_str, namespace=context.rule.entity.key_namespace)
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
              context.callbacks.inputs.append({'action_model': '8', 'action_key': 'clean_roles', 'key': domain_user.key.urlsafe()})
              callback.Engine.run(context)
          # Copy generated entity permissions to separate dictionary.
          local_action_permissions = context.rule.entity._action_permissions.copy()
          local_field_permissions = context.rule.entity._field_permissions.copy()
          # Reset permissions structures.
          cls.prepare(context)
      entity = context.rule.entity
      if hasattr(entity, '_global_role') and isinstance(entity._global_role, GlobalRole):
        entity._global_role.run(context)
      # Copy generated entity permissions to separate dictionary.
      global_action_permissions = context.rule.entity._action_permissions.copy()
      global_field_permissions = context.rule.entity._field_permissions.copy()
      # Reset permissions structures.
      cls.prepare(context)
      context.rule.entity._action_permissions = cls.compile(local_action_permissions, global_action_permissions, strict)
      context.rule.entity._field_permissions = cls.compile(local_field_permissions, global_field_permissions, strict)
      context.rule.entity.add_output('_action_permissions')
      context.rule.entity.add_output('_field_permissions')


class GlobalRole(Role):
  pass


class DomainRole(Role):
  
  _kind = 60
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('60', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('60', event.Action.build_key('60-0').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('60', event.Action.build_key('60-3').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('60', event.Action.build_key('60-1').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('60', event.Action.build_key('60-2').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('60', event.Action.build_key('60-3').urlsafe(), False, "context.rule.entity.key_id_str == 'admin'"),
      ActionPermission('60', event.Action.build_key('60-1').urlsafe(), False, "context.rule.entity.key_id_str == 'admin'"),
      ActionPermission('60', event.Action.build_key('60-3').urlsafe(), True, "not context.rule.entity.key_id_str == 'admin'"),
      ActionPermission('60', event.Action.build_key('60-1').urlsafe(), True, "not context.rule.entity.key_id_str == 'admin'"),
      ActionPermission('60', event.Action.build_key('60-6').urlsafe(), True, "context.auth.user._root_admin"),
      FieldPermission('60', '_records.note', False, False, "not context.auth.user._root_admin"),
      FieldPermission('60', '_records.note', True, True, "context.auth.user._root_admin")
      ]
    )
  
  _actions = {
    'create': event.Action(
      id='60-0',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'permissions': ndb.SuperJsonProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True)
        }
      ),
    'update': event.Action(
      id='60-3',
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'permissions': ndb.SuperJsonProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True)
        }
      ),
    'delete': event.Action(id='60-1', arguments={'key': ndb.SuperKeyProperty(kind='60', required=True)}),
    'search': event.Action(
      id='60-2',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
    'read': event.Action(id='60-4', arguments={'key': ndb.SuperKeyProperty(kind='60', required=True)}),
    'prepare': event.Action(
      id='60-5',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
    'read_records': event.Action(
      id='60-6',
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      )
    }
  
  @classmethod
  def delete(cls, context):  # @todo Transaction 'outbound' code presence!
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      entity.key.delete()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
      read(entity)
      context.output['entity'] = entity
    
    transaction()
    return context
  
  @classmethod
  def complete_save(cls, entity, context, create):
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    input_permissions = context.input.get('permissions')
    permissions = []
    for permission in input_permissions:
      if permission.get('type') == 'FieldPermission':
        permissions.append(FieldPermission(permission.get('kind'),
                                           permission.get('fields'),
                                           permission.get('writable'),
                                           permission.get('visible'),
                                           permission.get('condition')))
      elif permission.get('type') == 'ActionPermission':
        permissions.append(ActionPermission(permission.get('kind'),
                                            permission.get('actions'),
                                            permission.get('executable'),
                                            permission.get('condition')))
    values = {'name': context.input.get('name'),
              'active': context.input.get('active'),
              'permissions': permissions}
    if create:
      entity.populate(**values)  # @todo We do not have field level write control here (known issue with required fields)!
    else:
      write(entity, values)
    entity.put()
    context.log.entities.append((entity, ))
    log.Engine.run(context)
    read(entity)
    context.output['entity'] = entity
  
  @classmethod
  def create(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      domain_key = context.input.get('domain')
      domain = domain_key.get()
      entity = cls(namespace=domain.key_namespace)
      cls.complete_save(entity, context, True)
    
    transaction()
    return context
  
  @classmethod
  def update(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      entity = entity_key.get()
      cls.complete_save(entity, context, False)
    
    transaction()
    return context
  
  @classmethod
  def search(cls, context):  # @todo Implement search input property!
    domain_key = context.input.get('domain')
    domain = domain_key.get()
    context.rule.entity = cls(namespace=domain.key_namespace)
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    query = cls.query(namespace=domain.key_namespace).order(cls.name)
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    entities, next_cursor, more = query.fetch_page(settings.DOMAIN_ADMIN_PER_PAGE, start_cursor=cursor)  # @todo UNIFY PAGING CONFIG ACROSS ALL QUERIES!!!!!!!!!!!!!!
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    for entity in entities:  # @todo Can we async this?
      context.rule.entity = entity
      Engine.run(context)
      read(entity)
    context.output['entities'] = entities
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
    return context
  
  @classmethod
  def prepare(cls, context):
    domain_key = context.input.get('domain')
    domain = domain_key.get()
    entity = cls(namespace=domain.key_namespace)
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    context.output['entity'] = entity
    return context
  
  @classmethod
  def read(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    read(entity)
    context.output['entity'] = entity
    return context
  
  @classmethod
  def read_records(cls, context):
    entity_key = context.input.get('key')
    next_cursor = context.input.get('next_cursor')
    entity = entity_key.get()
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    entities, next_cursor, more = log.Record.get_records(entity, next_cursor)
    entity._records = entities
    read(entity)
    context.output['entity'] = entity
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
    return context


class DomainUser(ndb.BaseModel):
  
  _kind = 8
  
  # root (namespace Domain) - id = str(user_key.id())
  # composite index: ancestor:no - name
  name = ndb.SuperStringProperty('1', required=True)
  roles = ndb.SuperKeyProperty('2', kind=DomainRole, repeated=True)  # It's important to ensure that this list doesn't contain duplicate role keys, since taht can pose security issue!!
  state = ndb.SuperStringProperty('3', required=True, choices=['invited', 'accepted'])
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('8', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('8', event.Action.build_key('8-0').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('8', event.Action.build_key('8-1').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('8', event.Action.build_key('8-1').urlsafe(), True,
                       "(context.rule.entity.namespace_entity.state == 'active' and context.auth.user.key_id_str == context.rule.entity.key_id_str) and not (context.auth.user.key_id_str == context.rule.entity.namespace_entity.primary_contact.entity.key_id_str)"),
      ActionPermission('8', event.Action.build_key('8-1').urlsafe(), False,
                       "(context.rule.entity.key_id_str == context.rule.entity.namespace_entity.primary_contact.entity.key_id_str)"),
      FieldPermission('8', 'roles', False, True, "(context.rule.entity.key_id_str == context.rule.entity.namespace_entity.primary_contact.entity.key_id_str)"),
      ActionPermission('8', event.Action.build_key('8-2').urlsafe(), False, 
                       "not context.rule.entity.namespace_entity.state == 'active' or context.auth.user.key_id_str != context.rule.entity.key_id_str"),
      ActionPermission('8', event.Action.build_key('8-2').urlsafe(), True,
                       "context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'invited' and context.auth.user.key_id_str == context.rule.entity.key_id_str"),
      ActionPermission('8', event.Action.build_key('8-3').urlsafe(), False, "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('8', event.Action.build_key('8-4').urlsafe(), True, "context.auth.user._is_taskqueue"),
      ActionPermission('8', event.Action.build_key('8-4').urlsafe(), False, "not context.auth.user._is_taskqueue"),
      ActionPermission('8', event.Action.build_key('8-8').urlsafe(), True, "context.auth.user._root_admin"),
      FieldPermission('8', '_records.note', False, False, 'not context.auth.user._root_admin'),
      FieldPermission('8', '_records.note', True, True, 'context.auth.user._root_admin')
      ]
    )
  
  _actions = {
    'invite': event.Action(
      id='8-0',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6'),
        'name': ndb.SuperStringProperty(required=True),
        'email': ndb.SuperStringProperty(required=True),
        'roles': ndb.SuperKeyProperty(kind=DomainRole, repeated=True)
        }
      ),
    'remove': event.Action(id='8-1', arguments={'key': ndb.SuperKeyProperty(kind='8', required=True)}),
    'accept': event.Action(id='8-2', arguments={'key': ndb.SuperKeyProperty(kind='8', required=True)}),
    'update': event.Action(
      id='8-3',
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'roles': ndb.SuperKeyProperty(kind=DomainRole, repeated=True)
        }
      ),
    'clean_roles': event.Action(id='8-4', arguments={'key': ndb.SuperKeyProperty(kind='8', required=True)}),
    'read': event.Action(id='8-5', arguments={'key': ndb.SuperKeyProperty(kind='8', required=True)}),
    'search': event.Action(
      id='8-6',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6')
        }
      ),
    'prepare': event.Action(
      id='8-7',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6')
        }
      ),
    'read_records': event.Action(
      id='8-8',
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      )
    }
  
  @classmethod
  def clean_roles(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      Engine.run(context, True)
      if not executable(context):
        raise ActionDenied(context)
      roles = ndb.get_multi(entity.roles)
      for i, role in enumerate(roles):
        if role is None:
          entity.roles.pop(i)
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
    
    transaction()
    return context
  
  @classmethod
  def prepare(cls, context):
    domain_key = context.input.get('domain')
    domain = domain_key.get()
    entity = cls(namespace=domain.key_namespace)
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    context.output['entity'] = entity
    context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
    return context
  
  @classmethod
  def invite(cls, context):  # @todo Transaction 'outbound' code presence!
    from app.srv import auth
    # Operating on too many entity groups.
    # All datastore operations in a transaction must operate on entities in the same entity group.
    # This includes querying for entities by ancestor, retrieving entities by key, updating entities, and deleting entities.
    email = context.input.get('email')
    user = auth.User.query(auth.User.emails == email).get()
    if not user:
      raise DomainUserError('not_found')
    input_roles = ndb.get_multi(context.input.get('roles'))
    domain_key = context.input.get('domain')
    domain = domain_key.get()
    already_invited = cls.build_key(user.key_id_str, namespace=domain.key_namespace).get()
    if already_invited:
      raise DomainUserError('already_invited')
    entity = cls(id=user.key_id_str, namespace=domain.key_namespace)
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      if user.state == 'active':
        roles = []
        # Avoid rogue roles.
        for role in input_roles:
          if role.key.namespace() == domain.key_namespace:
            roles.append(role.key)
        entity.populate(name=context.input.get('name'), state='invited', roles=roles)
        user.domains.append(domain.key)
        ndb.put_multi([entity, user])
        context.log.entities.append((entity, ))
        context.log.entities.append((user, ))
        log.Engine.run(context)
        read(entity)
        context.output['entity'] = entity
      else:
        raise DomainUserError('not_active')
    
    transaction()
    return context
  
  @classmethod
  def remove(cls, context):  # @todo Transaction 'outbound' code presence!
    from app.srv import auth
    entity_key = context.input.get('key')
    entity = entity_key.get()
    user = auth.User.build_key(long(entity.key.id())).get()
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      entity.key.delete()
      user.domains.remove(ndb.Key(urlsafe=entity.key_namespace))
      user.put()
      context.log.entities.append((entity, ))
      context.log.entities.append((user, ))
      log.Engine.run(context)
      read(entity)
      context.output['entity'] = entity
    
    transaction()
    return context
  
  @classmethod
  def accept(cls, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      Engine.run(context)
      if not executable(context):
        raise ActionDenied(context)
      entity.state = 'accepted'
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
      Engine.run(context)
      domain = entity.namespace_entity
      entity.key.delete(use_datastore=False)
      context.rule.entity = domain
      Engine.run(context)
      read(entity)
      read(domain)
      context.output['entity'] = entity
      context.output['domain'] = domain
    
    transaction()
    return context
  
  @classmethod
  def update(cls, context):  # @todo Transaction 'outbound' code presence!
    input_roles = ndb.get_multi(context.input.get('roles'))
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      Engine.run(context)
      if not executable(context):
        raise ActionDenied(context)
      roles = []
      # Avoid rogue roles.
      for role in input_roles:
        if role.key.namespace() == entity.key_namespace:
          roles.append(role.key)
      values = {'name': context.input.get('name'),
                'roles': roles}
      write(entity, values)
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
      read(entity)
      context.output['entity'] = entity
    
    transaction()
    return context
  
  @classmethod
  def read(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    read(entity)
    context.output['entity'] = entity
    context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
    return context
  
  @classmethod
  def search(cls, context):  # @todo Implement search input property!
    domain_key = context.input.get('domain')
    domain = domain_key.get()
    context.rule.entity = cls(namespace=domain.key_namespace)
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    query = cls.query(namespace=domain.key_namespace).order(cls.name)
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    entities, next_cursor, more = query.fetch_page(settings.DOMAIN_ADMIN_PER_PAGE, start_cursor=cursor)  # @todo UNIFY PAGING CONFIG ACROSS ALL QUERIES!!!!!!!!!!!!!!
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    for entity in entities:  # @todo Can we async this?
      context.rule.entity = entity
      Engine.run(context)
      read(entity)
    context.output['entities'] = entities
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
    return context
  
  @classmethod
  def read_records(cls, context):
    entity_key = context.input.get('key')
    next_cursor = context.input.get('next_cursor')
    entity = entity_key.get()
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    entities, next_cursor, more = log.Record.get_records(entity, next_cursor)
    entity._records = entities
    read(entity)
    context.output['entity'] = entity
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
    return context
  
  @classmethod
  def selection_roles_helper(cls, namespace):  # @todo Perhaps kill this method in favor of DomainRole.search()!?
    return DomainRole.query(DomainRole.active == True, namespace=namespace).fetch()
