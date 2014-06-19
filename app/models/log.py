# -*- coding: utf-8 -*-
'''
Created on Dec 25, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings


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


class SuperLocalStructuredRecordProperty(ndb.SuperLocalStructuredProperty):
  
  def __init__(self, *args, **kwargs):
    args = list(args)
    self._modelclass2 = args[0]
    args[0] = Record
    super(SuperLocalStructuredRecordProperty, self).__init__(*args, **kwargs)
  
  def get_model_fields(self):
    parent = super(SuperLocalStructuredRecordProperty, self).get_model_fields()
    if isinstance(self._modelclass2, basestring):
      self._modelclass2 = ndb.Model._kind_map.get(self._modelclass2)
    parent.update(self._modelclass2.get_fields())
    return parent


class SuperStructuredRecordProperty(ndb.SuperStructuredProperty):
  '''Usage: '_records': ndb.SuperStructuredRecordProperty(Domain or '6')'''
  
  def __init__(self, *args, **kwargs):
    args = list(args)
    self._modelclass2 = args[0]
    args[0] = Record
    super(SuperStructuredRecordProperty, self).__init__(*args, **kwargs)
  
  def get_model_fields(self):
    parent = super(SuperStructuredRecordProperty, self).get_model_fields()
    if isinstance(self._modelclass2, basestring):
      self._modelclass2 = ndb.Model._kind_map.get(self._modelclass2)
    parent.update(self._modelclass2.get_fields())
    return parent


class Record(ndb.BaseExpando):
  
  _kind = 5
  # Letters for field aliases are provided in order to avoid conflict with logged object fields, and alow scaling!
  logged = ndb.SuperDateTimeProperty('l', auto_now_add=True)
  agent = ndb.SuperKeyProperty('u', kind='0', required=True)
  action = ndb.SuperKeyProperty('a', kind='56', required=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'message': ndb.SuperTextProperty('m'),
    'note': ndb.SuperTextProperty('n')
    }
  
  _virtual_fields = {
    '_agent': ndb.SuperStringProperty(),
    '_action': ndb.SuperStringProperty()
    }
  
  def _if_properties_are_cloned(self):
    return not (self.__class__._properties is self._properties)
  
  def _retrieve_cloned_name(self, name):
    for _, prop in self._properties.items():
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
    '''Overrides ndb.BaseExpando._get_property_for.
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
      modelclass = self._kind_map.get(kind)
      # We cannot use entity.get_fields here directly as it returns 'friendly_field_name: prop', and we need 'prop._name: prop'.
      properties = dict([(pr._name, pr) for _, pr in modelclass.get_fields().items()])
      # Adds properties from parent class to the log entity making it possible to deserialize them properly.
      prop = properties.get(next)
      if prop:
        self._clone_properties()  # Clone properties, because if we don't, the Record._properties will be overriden!
        self._properties[next] = prop
        self.add_output(prop._code_name)  # Besides rule engine, this must be here as well.
    return super(Record, self)._get_property_for(p, indexed, depth)
  
  def log_entity(self, entity):
    self._clone_properties()  # Clone properties, because if we don't, the Record._properties will be overriden.
    for _, prop in entity._properties.items():  # We do not call get_fields here because all fields that have been written are in _properties.
      value = prop._get_value(entity)
      self._properties[prop._name] = prop
      try:
        prop._set_value(self, value)
      except TypeError as e:
        setattr(self, prop._code_name, value)
      self.add_output(prop._code_name)
    return self
