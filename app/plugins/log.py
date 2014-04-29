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


def get_records(entity, urlsafe_cursor):
  items_per_page = settings.RECORDS_PAGE
  cursor = Cursor(urlsafe=urlsafe_cursor)
  query = Record.query(ancestor=entity.key).order(-Record.logged)
  entities, next_cursor, more = query.fetch_page(items_per_page, start_cursor=cursor)
  if next_cursor:
    next_cursor = next_cursor.urlsafe()
  
  @ndb.tasklet
  def async(entity):
    if entity.key_namespace:
      domain_user_key = ndb.Key('8', str(entity.agent.id()), namespace=entity.key_namespace)
      agent = yield domain_user_key.get_async()
      agent = agent.name
    else:
      agent = yield entity.agent.get_async()
      agent = agent._primary_email
    entity._agent = agent
    action_key_id = str(entity.action.id()).split('-')
    if len(action_key_id) == 2:
      kind_id, action_id = action_key_id
      modelclass = entity._kind_map.get(kind_id)
      if modelclass and hasattr(modelclass, '_actions'):
        for action_key, action in modelclass._actions.items():
          if entity.action == action.key:
            entity._action = '%s.%s' % (modelclass.__name__, action_key)
            break
    else:
      entity._action = entity.action.id()
    raise ndb.Return(entity)
  
  @ndb.tasklet
  def helper(entities):
    results = yield map(async, entities)
    raise ndb.Return(results)
  
  entities = helper(entities)
  entities = [entity for entity in entities.get_result()]
  return entities, next_cursor, more


class Read(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  
  def run(self, context):
    if len(context.entities):
      if isinstance(context.entities, dict):
        if self.kind_id != None:
          entities, next_cursor, more = get_records(context.entities[self.kind_id], context.input.get('next_cursor'))
          context.entities[self.kind_id]._records = entities
          context.next_cursor = next_cursor
          context.more = more
        else:
          entities, next_cursor, more = get_records(context.entities[context.model.get_kind()], context.input.get('next_cursor'))
          context.entities[context.model.get_kind()]._records = entities
          context.next_cursor = next_cursor
          context.more = more


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
