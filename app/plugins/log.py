# -*- coding: utf-8 -*-
'''
Created on Apr 17, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings, memcache, util
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


class Read(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  page_size = ndb.SuperIntegerProperty('6', indexed=False, required=True, default=10)
  
  def run(self, context):
    if len(context.entities) and isinstance(context.entities, dict):
      if self.kind_id != None:
        kind_id = self.kind_id
      else:
        kind_id = context.model.get_kind()
      cursor = Cursor(urlsafe=context.input.get('log_read_cursor'))
      model = context.models['5']
      entity = context.entities[kind_id]
      query = model.query(ancestor=entity.key).order(-model.logged)
      entities, cursor, more = query.fetch_page(self.page_size, start_cursor=cursor)
      if cursor:
        cursor = cursor.urlsafe()

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
        action_parent = entity.action.parent()
        modelclass = entity._kind_map.get(action_parent.kind())
        action_id = entity.action.id()
        if modelclass and hasattr(modelclass, '_actions'):
          for action in modelclass._actions:
            if entity.action == action.key:
              entity._action = '%s.%s' % (modelclass.__name__, action_id)
              break
        raise ndb.Return(entity)

      @ndb.tasklet
      def helper(entities):
        results = yield map(async, entities)
        raise ndb.Return(results)

      entities = helper(entities)
      entities = [entity for entity in entities.get_result()]
      context.entities[kind_id]._records = entities
      context.log_read_cursor = cursor
      context.log_read_more = more


class Entity(event.Plugin):
  
  log_entities = ndb.SuperStringProperty('5', indexed=False, repeated=True)
  static_arguments = ndb.SuperJsonProperty('6', indexed=False, required=True, default={})
  dynamic_arguments = ndb.SuperJsonProperty('7', indexed=False, required=True, default={})
  
  def run(self, context):
    if len(context.entities) and isinstance(context.entities, dict):
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
      model = context.models['5']
      write_arguments = {}
      write_arguments.update(self.static_arguments)
      for key, value in self.dynamic_arguments.items():
        write_arguments[key] = get_attr(context, value)
      for config in context.log_entities:
        arguments = {}
        kwargs = {}
        entity = config[0]
        try:
          entity_arguments = config[1]
        except:
          entity_arguments = {}
        arguments.update(write_arguments)
        arguments.update(entity_arguments)
        log_entity = arguments.pop('log_entity', True)
        if len(arguments):
          for key, value in arguments.items():
            if entity._field_permissions['_records'][key]['writable']:
              kwargs[key] = value
        record = model(parent=entity.key, agent=context.user.key, action=context.action.key, **kwargs)
        if log_entity is True:
          log_entity = entity
        if log_entity:
          record.log_entity(log_entity)
        records.append(record)
    if len(records):
      recorded = ndb.put_multi(records)
    context.log_entities = []
