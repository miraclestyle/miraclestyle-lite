# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings
from app.srv import event, callback
from.app.plugins import log, callback


class Prepare(event.Plugin):
  
  domain_model = ndb.SuperBooleanProperty('4', required=True, indexed=False, default=True)
  
  def run(self, context):
    if not context.entities:
      context.entities = {}
    if self.domain_model:
      context.entities[context.model.get_kind()] = context.model(namespace=context.domain.key_namespace)
    else:
      context.entities[context.model.get_kind()] = context.model()


class Read(event.Plugin):
  
  def run(self, context):
    entity_key = context.input.get('key')
    context.entities[context.model.get_kind()] = entity_key.get()


class Write(event.Plugin):
  
  write_entities = ndb.SuperStringProperty('4', repeated=True, indexed=False)
  
  @ndb.transactional(xg=True)
  def run(self, context):
    entities = []
    if len(self.write_entities):
      for kind_id in self.write_entities:
        if kind_id in context.entities:
          entities.append(context.entities[kind_id])
    else:
      for kind_id, entity in context.entities.items():
        entities.append(entity)
    ndb.put_multi(entities)
    log.write(context)
    callback.execute(context)


class Delete(event.Plugin):
  
  delete_entities = ndb.SuperStringProperty('4', repeated=True, indexed=False)
  
  @ndb.transactional(xg=True)
  def run(self, context):
    entities = []
    if len(self.delete_entities):
      for kind_id in self.delete_entities:
        if kind_id in context.entities:
          entities.append(context.entities[kind_id])
    else:
      for kind_id, entity in context.entities.items():
        entities.append(entity)
    ndb.delete_multi(entities)
    log.write(context)
    callback.execute(context)


class Output(event.Plugin):
  
  def run(self, context):
    context.output['entity'] = context.entities[context.model.get_kind()]


class Field(ndb.BaseModel):
  
  name = ndb.SuperStringProperty('1', required=True, indexed=False)
  value = ndb.SuperStringProperty('2', required=True, indexed=False)


class FieldAutoUpdate(event.Plugin):
  
  fields = ndb.SuperLocalStructuredProperty(Field, '4', repeated=True, indexed=False)
  
  def run(self, context):
    for field in self.fields:
      setattr(context.values, field.name, field.value)


class Search(event.Plugin):
  
  search_filter_callback = ndb.SuperStringProperty('4', required=True, indexed=False)
  search_entities_callback = ndb.SuperStringProperty('5', required=True, indexed=False)
  
  def run(self, context):
    if context.entity.key:
      namespace = context.entity.key_namespace
    query = context.model.query(namespace=namespace)  # @todo not sure if we should extract model from entity (model = context.entity.__class__)?
    search = context.input.get('search')
    if search:
      filters = search.get('filters')
      order_by = search.get('order_by')
      args = []
      for _filter in filters:
        field = getattr(model, _filter['field'])
        op = _filter['operator']
        value = _filter['value']
        if op == '==': # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this algo needs improvements
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
      order_by_field = getattr(context.model, order_by['field'])  # @todo context.model vs. context.entity.__class__ ?
      asc = order_by['operator'] == 'asc'
      if asc:
        query = query.order(order_by_field)
      else:
        query = query.order(-order_by_field)
    if self.search_filter_callback:
      query = self.search_filter_callback(context, query)  # @todo Not sure how to deal with this in plugin?
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    entities, next_cursor, more = query.fetch_page(settings.SEARCH_PAGE, start_cursor=cursor)
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    # @todo Not sure how to deal with remaining lines in this in plugin? This run() has to be broken down for compliancy!
    if self.search_entities_callback:
      entities = self.search_entities_callback(context, entities)
    for entity in entities:
      context.rule.entity = entity
      rule.Engine.run(context)
      rule.read(entity)
    context.output['entities'] = entities
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
