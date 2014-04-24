# -*- coding: utf-8 -*-
'''
Created on Apr 17, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr
from app.srv.log import Record


class Entity(event.Plugin):
  
  log_entities = ndb.SuperStringProperty('5', indexed=False, repeated=True)
  static_arguments = ndb.SuperJsonProperty('6', indexed=False, required=True, default={})
  dynamic_arguments = ndb.SuperJsonProperty('7', indexed=False, required=True, default={})
  
  def run(self, context):
    if len(context.entities):
      if isinstance(context.entities, dict):
        arguments = {}
        arguments.update(self.static_arguments)
        for key, value in self.dynamic_arguments.items():
          arguments[key] = get_attr(context, value)
        if len(self.log_entities):
          for kind_id in self.log_entities:
            if kind_id in context.entities:
              context.log_entities.append((context.entities[kind_id], arguments))
        else:
          context.log_entities.append((context.entities[context.model.get_kind()], arguments))


class Write(event.Plugin):
  
  static_arguments = ndb.SuperJsonProperty('5', indexed=False, required=True, default={})
  dynamic_arguments = ndb.SuperJsonProperty('6', indexed=False, required=True, default={})
  
  def run(self, context):
    records = []
    if len(context.log_entities):
      for config in context.log_entities:
        arguments = {}
        kwargs = {}
        arguments.update(self.static_arguments)
        for key, value in self.dynamic_arguments.items():
          arguments[key] = get_attr(context, value)
        entity = config[0]
        try:
          entity_arguments = config[1]
        except:
          entity_arguments = {}
        arguments.update(entity_arguments)
        log_entity = arguments.pop('log_entity', True)
        if len(arguments):
          for key, value in arguments.items():
            if entity._field_permissions['_records'][key]['writable']:
              kwargs[key] = value
        record = Record(parent=entity.key, agent=context.user.key, action=context.action.key, **kwargs)
        if log_entity is True:
          log_entity = entity
        if log_entity:
          record.log_entity(log_entity)
        records.append(record)
    if len(records):
      recorded = ndb.put_multi(records)
    context.log_entities = []
