# -*- coding: utf-8 -*-
from .base import *
from .properties import *


__all__ = ['Record', 'Action', 'PluginGroup', 'Permission', 'ActionPermission', 'FieldPermission']


class Record(BaseExpando):
  '''
  The class Record overrides some methods because it needs to accomplish proper deserialization of the logged entity.
  It uses Model._clone_properties() in Record.log_entity() and Record._get_property_for(). That is because
  if we do not call that method, the class(cls) scope - Record._properties will be altered which will cause variable leak,
  meaning that simultaneously based on user actions, new properties will be appended to Record._properties, and that will
  cause complete inconsistency and errors while fetching, storing and deleting data. This behavior was noticed upon testing.
  Same approach must be done with the transaction / entry / line scenario, which implements its own logic for new
  properties.
  This implementation will not cause any performance issues or variable leak whatsoever, the _properties will be adjusted to
  be available in "self" - not "cls".
  In the beginning i forgot to look into the Model._fix_up_properties, which explicitly sets cls._properties to {} which then
  allowed mutations to class(cls) scope.

  '''
  _kind = 0
  
  _use_record_engine = False
  _use_rule_engine = False
  
  # Letters for field aliases are provided in order to avoid conflict with logged object fields, and alow scaling!
  logged = SuperDateTimeProperty('l', auto_now_add=True)
  agent = SuperKeyProperty('u', kind='11', required=True)
  action = SuperKeyProperty('a', kind='1', required=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'message': SuperTextProperty('m'),
    'note': SuperTextProperty('n')
    }
  
  _virtual_fields = {
    '_agent': SuperReferenceProperty(callback=lambda self: self._retreive_agent(),
                                     format_callback=lambda self, value: self._retrieve_agent_name(value)),
    '_action': SuperComputedProperty(lambda self: self._retrieve_action())
    }
  
  def _retrieve_agent_name(self, value):
    return value._primary_email
  
  def _retreive_agent(self):
    return self.agent.get_async()
  
  def _retrieve_action(self):
    entity = self
    action_parent = entity.action.parent()
    modelclass = entity._lookup_model(action_parent.kind())
    action_id = entity.action.id()
    if modelclass and hasattr(modelclass, '_actions'):
      for action in modelclass._actions:
        if entity.action == action.key:
          return '%s.%s' % (modelclass.__name__, action_id)
  
  def _if_properties_are_cloned(self):
    return not (self.__class__._properties is self._properties)
  
  def _retrieve_cloned_name(self, name):
    for _, prop in self._properties.iteritems():
      if name == prop._code_name:
        return prop._name
  
  def __setattr__(self, name, value):
    if self._if_properties_are_cloned():
      _name = self._retrieve_cloned_name(name)
      if _name:
        name = _name
    return super(Record, self).__setattr__(name, value)
  
  def __getattr__(self, name):
    if self._if_properties_are_cloned():
      _name = self._retrieve_cloned_name(name)
      if _name:
        name = _name
    return super(Record, self).__getattr__(name)
  
  def _get_property_for(self, p, indexed=True, depth=0):
    '''Overrides BaseExpando._get_property_for.
    Only way to merge properties from its parent kind to log entity.
    
    '''
    name = p.name()
    parts = name.split('.')
    if len(parts) <= depth:
      # Apparently there's an unstructured value here.
      # Assume it is a None written for a missing value.
      # (It could also be that a schema change turned an unstructured
      # value into a structured one. In that case, too, it seems
      # better to return None than to return an unstructured value,
      # since the latter doesn't match the current schema.)
      return None
    next = parts[depth]
    prop = self._properties.get(next)
    if prop is None:
      # This loads up proper class to deal with the expandos.
      kind = self.key_parent.kind()
      modelclass = self._lookup_model(kind)
      # We cannot use entity.get_fields here directly as it returns 'friendly_field_name: prop', and we need 'prop._name: prop'.
      properties = dict([(pr._name, pr) for _, pr in modelclass.get_fields().iteritems()])
      # Adds properties from parent class to the log entity making it possible to deserialize them properly.
      prop = properties.get(next)
      if prop:
        # prop = copy.deepcopy(prop) no need to deepcopy prop for now, we'll see.
        self._clone_properties()  # Clone properties, because if we don't, the Record._properties will be used!
        self._properties[next] = prop
        self.add_output(prop._code_name)  # Besides rule engine, this must be here as well.
    return super(Record, self)._get_property_for(p, indexed, depth)
  
  def log_entity(self, entity):
    self._clone_properties()  # Clone properties, because if we don't, the Record._properties will be used.
    for _, prop in entity._properties.iteritems():  # We do not call get_fields here because all fields that have been written are in _properties.
      value = prop._get_value(entity)
      if isinstance(value, LocalStructuredPropertyValue): # we can only log locally structured data
        value = value.value
      elif hasattr(prop, 'is_structured') and prop.is_structured:
        continue # we cannot log remote structured properties
      prop = copy.deepcopy(prop)
      prop._indexed = False
      self._properties[prop._name] = prop
      try:
        prop._set_value(self, value)
      except TypeError as e:
        setattr(self, prop._code_name, value)
      self.add_output(prop._code_name)
    return self


class Action(BaseExpando):
  
  _kind = 1
  
  name = SuperStringProperty('1', required=True)
  arguments = SuperPickleProperty('2', required=True, default={}, compressed=False)
  active = SuperBooleanProperty('3', required=True, default=True)
  
  _default_indexed = False
  
  def __init__(self, *args, **kwargs):
    self._plugin_groups = kwargs.pop('_plugin_groups', None)
    super(Action, self).__init__(*args, **kwargs)
  
  @classmethod
  def build_key(cls, kind, action_id):
    return Key(kind, 'action', cls._get_kind(), action_id)


class PluginGroup(BaseExpando):
  
  _kind = 2
  
  name = SuperStringProperty('1', required=True)
  subscriptions = SuperKeyProperty('2', kind='1', repeated=True)
  active = SuperBooleanProperty('3', required=True, default=True)
  sequence = SuperIntegerProperty('4', required=True)  # @todo Not sure if we are gonna need this?
  transactional = SuperBooleanProperty('5', required=True, default=False, indexed=False)
  plugins = SuperPickleProperty('6', required=True, default=[], compressed=False)
  
  _default_indexed = False


class Permission(BasePolyExpando):
  '''Base class for all permissions.
  If the futuer deems scaling to be a problem, possible solutions could be to:
  a) Create DomainUserPermissions entity, that will fan-out on DomainUser entity,
  and will contain all permissions for the domain user (based on it's domain role membership) in it;
  b) Transform this class to BasePolyExpando, so it can be indexed and queried (by model kind, by action...),
  and store each permission in datasotre as child entity of DomainUser;
  c) Some other similar pattern.
  
  '''
  _kind = 3
  
  _default_indexed = False


class ActionPermission(Permission):
  
  _kind = 4
  
  model = SuperStringProperty('1', required=True, indexed=False)
  actions = SuperVirtualKeyProperty('2', kind='1', repeated=True, indexed=False)
  executable = SuperBooleanProperty('3', required=False, default=None, indexed=False)
  condition = SuperStringProperty('4', required=True, indexed=False)
  
  def __init__(self, *args, **kwargs):
    super(ActionPermission, self).__init__(**kwargs)
    if len(args):
      model, actions, executable, condition = args
      if not isinstance(actions, (tuple, list)):
        actions = [actions]
      self.model = model
      self.actions = actions
      self.executable = executable
      self.condition = condition
  
  def run(self, entity, **kwargs):
    kwargs['entity'] = entity
    if (self.model == entity.get_kind()):
      for action in self.actions:
        if (entity.get_action(action) is not None) and (util.safe_eval(self.condition, kwargs)) and (self.executable != None):
          entity._action_permissions[action.urlsafe()]['executable'].append(self.executable)


class FieldPermission(Permission):
  
  _kind = 5
  
  model = SuperStringProperty('1', required=True, indexed=False)
  fields = SuperStringProperty('2', repeated=True, indexed=False)
  writable = SuperBooleanProperty('3', required=False, default=None, indexed=False)
  visible = SuperBooleanProperty('4', required=False, default=None, indexed=False)
  condition = SuperStringProperty('5', required=True, indexed=False)
  
  def __init__(self, *args, **kwargs):
    super(FieldPermission, self).__init__(**kwargs)
    if len(args):
      model, fields, writable, visible, condition = args
      if not isinstance(fields, (tuple, list)):
        fields = [fields]
      self.model = model
      self.fields = fields
      self.writable = writable
      self.visible = visible
      self.condition = condition
  
  def run(self, entity, **kwargs):
    kwargs['entity'] = entity
    if (self.model == entity.get_kind()):
      for field in self.fields:
        parsed_field = util.get_attr(entity, '_field_permissions.' + field)
        if parsed_field and (util.safe_eval(self.condition, kwargs)):
          if (self.writable != None):
            parsed_field['writable'].append(self.writable)
          if (self.visible != None):
            parsed_field['visible'].append(self.visible)