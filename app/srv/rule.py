# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import collections

from app import ndb
from app.lib.safe_eval import safe_eval
from app.srv import event, log, callback, cruds
from app.plugins import common
from app.plugins import rule as plugin_rule
from app.plugins import log as plugin_log
from app.plugins import callback as plugin_callback

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


class Context():
  
  def __init__(self):
    self.entity = None
    self.skip_user_roles = False
    self.strict = False


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
    for action in self.actions:
      if (self.kind == context.rule.entity.get_kind()) and (action in context.rule.entity.get_actions()) and (safe_eval(self.condition, {'context': context, 'action': action})) and (self.executable != None):
        context.rule.entity._action_permissions[action]['executable'].append(self.executable)


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
    for field in self.fields:
      parsed_field = _parse_field(context.rule.entity._field_permissions, field)  # Retrieves field value from foo.bar.far
      if (self.kind == context.rule.entity.get_kind()) and parsed_field and (safe_eval(self.condition, {'context': context, 'field': field})):
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


class Engine:
  
  @classmethod
  def prepare_actions(cls, action_permissions, actions):
    for action_key in actions:
      action_permissions[action_key] = {'executable': []}
  
  @classmethod
  def prepare_fields(cls, field_permissions, fields):
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
  def decide(cls, permissions, strict, root=True, parent_permissions=None):
    for key, value in permissions.items():
      if isinstance(value, dict):
        if parent_permissions:
          root = False
        cls.decide(permissions[key], strict, root, permissions)
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
        global_permissions[key] = value
  
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
  def run(cls, context):
    """This method generates permissions situation for the context.rule.entity object,
    at the time of execution.
    
    """
    skip_user_roles = context.rule.skip_user_roles
    strict = context.rule.strict
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
  
  _kind = 67


class DomainRole(Role):
  
  _kind = 60
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('60', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('60', event.Action.build_key('60-0').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('60', event.Action.build_key('60-1').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active' or context.rule.entity.key_id_str == 'admin'"),
      ActionPermission('60', event.Action.build_key('60-2').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('60', event.Action.build_key('60-3').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active' or context.rule.entity.key_id_str == 'admin'"),
      ActionPermission('60', event.Action.build_key('60-4').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active' or context.rule.entity.key_id_str == 'admin'"),
      ActionPermission('60', event.Action.build_key('60-5').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('60', event.Action.build_key('60-6').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active'"),
      FieldPermission('60', ['name', 'active', 'permissions', '_records'], False, None,
                      "not context.rule.entity.namespace_entity.state == 'active' or context.rule.entity.key_id_str == 'admin'"),
      FieldPermission('60', ['name', 'active', 'permissions', '_records'], None, False,
                      "not context.rule.entity.namespace_entity.state == 'active'")
      ]
    )
  
  _actions = {
    'prepare': event.Action(
      id='60-0',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
    'create': event.Action(
      id='60-1',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'permissions': ndb.SuperJsonProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True)
        }
      ),
    'read': event.Action(id='60-2', arguments={'key': ndb.SuperKeyProperty(kind='60', required=True)}),
    'update': event.Action(
      id='60-3',
      arguments={
        'key': ndb.SuperKeyProperty(kind='60', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'permissions': ndb.SuperJsonProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True)
        }
      ),
    'delete': event.Action(id='60-4', arguments={'key': ndb.SuperKeyProperty(kind='60', required=True)}),
    'search': event.Action(
      id='60-5',
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
  
  _plugins = [
    common.Prepare(
      subscriptions=[
        event.Action.build_key('60-0'),
        event.Action.build_key('60-1'),
        event.Action.build_key('60-5')
        ],
      domain_model=True
      ),
    common.Read(
      subscriptions=[
        event.Action.build_key('60-2'),
        event.Action.build_key('60-3'),
        event.Action.build_key('60-4'),
        event.Action.build_key('60-6')
        ]
      ),
    plugin_rule.Prepare(
      subscriptions=[
        event.Action.build_key('60-0'),
        event.Action.build_key('60-1'),
        event.Action.build_key('60-2'),
        event.Action.build_key('60-3'),
        event.Action.build_key('60-4'),
        event.Action.build_key('60-5'),
        event.Action.build_key('60-6')
        ],
      skip_user_roles=False,
      strict=False
      ),
    plugin_rule.Exec(
      subscriptions=[
        event.Action.build_key('60-0'),
        event.Action.build_key('60-1'),
        event.Action.build_key('60-2'),
        event.Action.build_key('60-3'),
        event.Action.build_key('60-4'),
        event.Action.build_key('60-5'),
        event.Action.build_key('60-6')
        ]
      ),
    plugin_rule.SetValue(
      subscriptions=[
        event.Action.build_key('60-1'),
        event.Action.build_key('60-3')
        ]
      ),
    plugin_rule.Write(
      subscriptions=[
        event.Action.build_key('60-1'),
        event.Action.build_key('60-3')
        ],
      transactional=True
      ),
    common.Write(
      subscriptions=[
        event.Action.build_key('60-1'),
        event.Action.build_key('60-3')
        ],
      transactional=True
      ),
    common.Delete(
      subscriptions=[
        event.Action.build_key('60-4')
        ],
      transactional=True
      ),
    plugin_log.Entity(
      subscriptions=[
        event.Action.build_key('60-1'),
        event.Action.build_key('60-3'),
        event.Action.build_key('60-4')
        ],
      transactional=True
      ),
    plugin_log.Write(
      subscriptions=[
        event.Action.build_key('60-1'),
        event.Action.build_key('60-3'),
        event.Action.build_key('60-4')
        ],
      transactional=True
      ),
    plugin_rule.Read(
      subscriptions=[
        event.Action.build_key('60-1'),
        event.Action.build_key('60-3'),
        event.Action.build_key('60-4')
        ],
      transactional=True
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('60-1'),
        event.Action.build_key('60-3'),
        event.Action.build_key('60-4')
        ],
      transactional=True,
      output_data={'entity': 'entities.60'}
      ),
    plugin_callback.Payload(
      subscriptions=[
        event.Action.build_key('60-1'),
        event.Action.build_key('60-3'),
        event.Action.build_key('60-4')
        ],
      transactional=True,
      queue = 'notify',
      static_data = {'action_key': 'initiate', 'action_model': '61'},
      dynamic_data = {'caller_entity': 'entities.60.key_urlsafe'}
      ),
    plugin_callback.Exec(
      subscriptions=[
        event.Action.build_key('60-1'),
        event.Action.build_key('60-3'),
        event.Action.build_key('60-4')
        ],
      transactional=True,
      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'}
      ),
    plugin_log.Read(
      subscriptions=[
        event.Action.build_key('60-6')
        ]
      ),
    common.Search(
      subscriptions=[
        event.Action.build_key('60-5')
        ]
      ),
    plugin_rule.Prepare(
      subscriptions=[
        event.Action.build_key('60-5')
        ],
      skip_user_roles=False,
      strict=False
      ),
    plugin_rule.Read(
      subscriptions=[
        event.Action.build_key('60-2'),
        event.Action.build_key('60-5'),
        event.Action.build_key('60-6')
        ]
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('60-0'),
        event.Action.build_key('60-2')
        ],
      output_data={'entity': 'entities.60'}
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('60-5')
        ],
      output_data={'entities': 'entities', 'next_cursor': 'next_cursor', 'more': 'more'}
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('60-6')
        ],
      output_data={'entity': 'entities.60', 'next_cursor': 'next_cursor', 'more': 'more'}
      )
    ]
  
  """@classmethod
  def delete(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.delete(context)
  
  @classmethod
  def complete_save(cls, context):
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
    return values
  
  @classmethod
  def create(cls, context):
    values = cls.complete_save(context)
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    context.cruds.values = values
    cruds.Engine.create(context)
  
  @classmethod
  def update(cls, context):
    values = cls.complete_save(context)
    context.cruds.entity = context.input.get('key').get()
    context.cruds.values = values
    cruds.Engine.update(context)
  
  @classmethod
  def search(cls, context):
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    cruds.Engine.search(context)
  
  @classmethod
  def prepare(cls, context):
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    cruds.Engine.prepare(context)
  
  @classmethod
  def read(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.read(context)
  
  @classmethod
  def read_records(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.read_records(context)"""


class DomainUser(ndb.BaseModel):
  
  _kind = 8
  
  name = ndb.SuperStringProperty('1', required=True)
  roles = ndb.SuperKeyProperty('2', kind=DomainRole, repeated=True)  # It's important to ensure that this list doesn't contain duplicate role keys, since taht can pose security issue!!
  state = ndb.SuperStringProperty('3', required=True, choices=['invited', 'accepted'])
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('8', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('8', event.Action.build_key('8-0').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('8', event.Action.build_key('8-1').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('8', event.Action.build_key('8-2').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('8', event.Action.build_key('8-3').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('8', event.Action.build_key('8-4').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active' or context.rule.entity.key_id_str == context.rule.entity.namespace_entity.primary_contact.entity.key_id_str"),
      ActionPermission('8', event.Action.build_key('8-4').urlsafe(), True,
                       "(context.rule.entity.namespace_entity.state == 'active' and context.auth.user.key_id_str == context.rule.entity.key_id_str) and not (context.rule.entity.key_id_str == context.rule.entity.namespace_entity.primary_contact.entity.key_id_str)"),
      ActionPermission('8', event.Action.build_key('8-5').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('8', event.Action.build_key('8-6').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active'"),
      ActionPermission('8', event.Action.build_key('8-7').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active' or context.auth.user.key_id_str != context.rule.entity.key_id_str"),
      ActionPermission('8', event.Action.build_key('8-7').urlsafe(), True,
                       "context.rule.entity.namespace_entity.state == 'active' and context.auth.user.key_id_str != context.rule.entity.key_id_str and context.rule.entity.state == 'invited'"),
      ActionPermission('8', event.Action.build_key('8-8').urlsafe(), False,
                       "not context.rule.entity.namespace_entity.state == 'active' or not context.auth.user._is_taskqueue"),
      ActionPermission('8', event.Action.build_key('8-8').urlsafe(), True,
                       "context.rule.entity.namespace_entity.state == 'active' and context.auth.user._is_taskqueue"),
      FieldPermission('8', ['name', 'roles', 'state', '_records'], False, False,
                      "not context.rule.entity.namespace_entity.state == 'active'"),
      FieldPermission('8', ['state'], False, None,
                      "context.rule.entity.namespace_entity.state == 'active'")  # @todo Not sure how to handle state field permissions (though actions seem to not respect field permissions)?
      ]
    )
  
  _actions = {
    'prepare': event.Action(
      id='8-0',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6')
        }
      ),
    'invite': event.Action(
      id='8-1',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6'),
        'name': ndb.SuperStringProperty(required=True),
        'email': ndb.SuperStringProperty(required=True),
        'roles': ndb.SuperKeyProperty(kind=DomainRole, repeated=True)
        }
      ),
    'read': event.Action(id='8-2', arguments={'key': ndb.SuperKeyProperty(kind='8', required=True)}),
    'update': event.Action(
      id='8-3',
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'roles': ndb.SuperKeyProperty(kind=DomainRole, repeated=True)
        }
      ),
    'remove': event.Action(id='8-4', arguments={'key': ndb.SuperKeyProperty(kind='8', required=True)}),
    'search': event.Action(
      id='8-5',
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
        }
      ),
    'read_records': event.Action(
      id='8-6',
      arguments={
        'key': ndb.SuperKeyProperty(kind='8', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    'accept': event.Action(id='8-7', arguments={'key': ndb.SuperKeyProperty(kind='8', required=True)}),
    'clean_roles': event.Action(id='8-8', arguments={'key': ndb.SuperKeyProperty(kind='8', required=True)})
    }
  
  @classmethod
  def clean_roles(cls, context):  # @todo Do we need notifications here?
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    Engine.run(context, True)
    if not executable(context):
      raise ActionDenied(context)
    roles = ndb.get_multi(entity.roles)
    
    @ndb.transactional(xg=True)
    def transaction():
      for i, role in enumerate(roles):
        if role is None:
          entity.roles.pop(i)
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
    
    transaction()
  
  @classmethod
  def prepare(cls, context):
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    cruds.Engine.prepare(context)
    entity = context.output['entity']
    context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
  
  @classmethod
  def invite(cls, context):
    from app.srv import auth
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
      if user.state == 'active':  # @todo Why is this validation not implemented in global role?
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
        context.callback.payloads.append(('notify',
                                          {'action_key': 'initiate',
                                           'action_model': '61',
                                           'caller_entity': entity.key.urlsafe()}))
        callback.Engine.run(context)
        context.output['entity'] = entity
      else:
        raise DomainUserError('not_active')
    
    transaction()
  
  @classmethod
  def remove(cls, context):
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
      context.callback.payloads.append(('notify',
                                        {'action_key': 'initiate',
                                         'action_model': '61',
                                         'caller_entity': entity.key.urlsafe()}))
      callback.Engine.run(context)
      context.output['entity'] = entity
    
    transaction()
  
  @classmethod
  def accept(cls, context):
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    Engine.run(context)
    if not executable(context):
      raise ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      entity.state = 'accepted'
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
      Engine.run(context)
      domain = entity.namespace_entity
      context.rule.entity = domain
      Engine.run(context)
      read(entity)
      read(domain)
      context.callback.payloads.append(('notify',
                                        {'action_key': 'initiate',
                                         'action_model': '61',
                                         'caller_entity': entity.key.urlsafe()}))
      callback.Engine.run(context)
      context.output['entity'] = entity
      context.output['domain'] = domain
    
    transaction()
  
  @classmethod
  def update(cls, context):
    input_roles = ndb.get_multi(context.input.get('roles'))
    entity_key = context.input.get('key')
    entity = entity_key.get()
    roles = []
    # Avoid rogue roles.
    for role in input_roles:
      if role.key.namespace() == entity.key_namespace:
        roles.append(role.key)
    context.cruds.entity = context.input.get('key').get()
    context.cruds.values = {'name': context.input.get('name'), 'roles': roles}
    cruds.Engine.update(context)
  
  @classmethod
  def read(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.read(context)
    entity = context.output['entity']
    context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
  
  @classmethod
  def search(cls, context):
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    cruds.Engine.search(context)
  
  @classmethod
  def read_records(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.read_records(context)
  
  @classmethod
  def selection_roles_helper(cls, namespace):  # @todo This method will die, ajax DomainRole.search() will be used instead!
    return DomainRole.query(DomainRole.active == True, namespace=namespace).fetch()
