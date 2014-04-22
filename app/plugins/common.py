# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings
from app.srv import event, callback
from.app.plugins import log, callback


def select_entities(context, entities):
  entities = []
  if len(entities):
    for kind_id in entities:
      if kind_id in context.entities:
        entities.append(context.entities[kind_id])
  else:
    entities.append(context.entities[context.model.get_kind()])
  return entities

def set_context(context):
  if not context.entities:
    context.entities = {}
  if not context.values:
    context.values = {}

def prepare_attr(entity, field_path):
  fields = field_path.split('.')
  last_field = fields[-1]
  drill = fields[:-1]
  i = -1
  while not last_field:
    i = i - 1
    last_field = fields[i]
    drill = fields[:i]
  for field in drill:
    if field:
      if isinstance(entity, dict):
        try:
          entity = entity[field]
        except KeyError as e:
          return None
      elif isinstance(entity, list):
        try:
          entity = entity[int(field)]
        except KeyError as e:
          return None
      else:
        try:
          entity = getattr(entity, field)
        except ValueError as e:
          return None
  return (entity, last_field)

def set_attr(entity, field_path, value):
  entity, last_field = prepare_attr(entity, field_path)
  if isinstance(entity, dict):
    entity[last_field] = value
  elif isinstance(entity, list):
    entity.insert(int(last_field), value)
  else:
    setattr(entity, last_field, value)

def get_attr(entity, field_path):
  entity, last_field = prepare_attr(entity, field_path)
  if isinstance(entity, dict):
    return entity.get(last_field)
  elif isinstance(entity, list):
    return entity[int(last_field)]
  else:
    return getattr(entity, last_field)


class Prepare(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('4', required=False, indexed=False)
  domain_model = ndb.SuperBooleanProperty('5', required=True, indexed=False, default=True)
  
  def run(self, context):
    set_context(context)
    if self.kind_id != None:
      if self.domain_model:
        context.entities[self.kind_id] = context.model(namespace=context.domain.key_namespace)
      else:
        context.entities[self.kind_id] = context.model()
      context.values[self.kind_id] = copy.deepcopy(context.entities[self.kind_id])
    else:
      if self.domain_model:
        context.entities[context.model.get_kind()] = context.model(namespace=context.domain.key_namespace)
      else:
        context.entities[context.model.get_kind()] = context.model()
      context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])


class Read(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('4', required=False, indexed=False)
  
  def run(self, context):
    set_context(context)
    entity_key = context.input.get('key')
    if self.kind_id != None:
      context.entities[self.kind_id] = entity_key.get()
      context.values[self.kind_id] = copy.deepcopy(context.entities[self.kind_id])
    else:
      context.entities[context.model.get_kind()] = entity_key.get()
      context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])


class Write(event.Plugin):
  
  write_entities = ndb.SuperStringProperty('4', repeated=True, indexed=False)
  
  @ndb.transactional(xg=True)
  def run(self, context):
    entities = select_entities(context, self.write_entities)
    ndb.put_multi(entities)
    log.write(context)
    callback.execute(context)


class Delete(event.Plugin):
  
  delete_entities = ndb.SuperStringProperty('4', repeated=True, indexed=False)
  
  @ndb.transactional(xg=True)
  def run(self, context):
    entities = select_entities(context, self.delete_entities)
    ndb.delete_multi(entities)
    log.write(context)
    callback.execute(context)


class Field(ndb.BaseModel):
  
  name = ndb.SuperStringProperty('1', required=True, indexed=False)
  value = ndb.SuperStringProperty('2', required=True, indexed=False)


class Output(event.Plugin):  # @todo Not sure if this plugin should have it's own (fields) structured property!
  
  fields = ndb.SuperLocalStructuredProperty(Field, '4', repeated=True, indexed=False)
  
  def run(self, context):
    for field in self.fields:
      context.output[field.value] = get_attr(context, field.name)


class FieldAutoUpdate(event.Plugin):  # @todo This could be made more abstract, like: set_attr(context, field.name, field.value)!
  
  kind_id = ndb.SuperStringProperty('4', required=False, indexed=False)
  fields = ndb.SuperLocalStructuredProperty(Field, '5', repeated=True, indexed=False)
  
  def run(self, context):
    for field in self.fields:
      if self.kind_id != None:
        set_attr(context.values[self.kind_id], field.name, field.value)
      else:
        set_attr(context.values[context.model.get_kind()], field.name, field.value)


class Search(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('4', required=False, indexed=False)
  search = ndb.SuperJsonProperty('5', required=False, indexed=False, default={})  # @todo Transform this field to include optional query parameters to include in query.
  
  def run(self, context):
    namespace = None
    if self.kind_id != None:
      model = context.entities[self.kind_id].__class__
      if context.entities[self.kind_id].key:
        namespace = context.entities[self.kind_id].key_namespace
    else:
      model = context.model
      if context.entities[context.model.get_kind()].key:
        namespace = context.entities[context.model.get_kind()].key_namespace
    query = model.query(namespace=namespace)
    search = context.input.get('search')
    if search:
      filters = search.get('filters')
      order_by = search.get('order_by')
      args = []
      for _filter in filters:
        field = getattr(model, _filter['field'])
        op = _filter['operator']
        value = _filter['value']
        if op == '==': # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this also needs improvements
          args.append(field == value)
        elif op == '!=':
          args.append(field != value)
        elif op == '>':
          args.append(field > value)
        elif op == '<':
          args.append(field < value)
        elif op == '>=':
          args.append(field >= value)
        elif op == 'IN':
          args.append(field.IN(value))
      query = query.filter(*args)
      order_by_field = getattr(model, order_by['field'])
      asc = order_by['operator'] == 'asc'
      if asc:
        query = query.order(order_by_field)
      else:
        query = query.order(-order_by_field)
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    entities, next_cursor, more = query.fetch_page(settings.SEARCH_PAGE, start_cursor=cursor)
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    context.entities = entities
    # @todo Perfectly all of the output should be handeled on one place. Output lines below should be removed when output is optimized.
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
