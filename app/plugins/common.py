# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


def select_entities(context, selection):
  entities = []
  if len(selection):
    for kind_id in selection:
      if kind_id in context.entities:
        entities.append(context.entities[kind_id])
  else:
    entities.append(context.entities[context.model.get_kind()])
  return entities

def set_context(context):
  if not hasattr(context, 'entities'):
    context.entities = {}
  if not hasattr(context, 'values'):
    context.values = {}
  # @todo Following lines are temporary!
  context.user = context.auth.user
  domain_key = context.input.get('domain')
  if domain_key:
    context.domain = domain_key.get()
  if not hasattr(context, 'callback_payloads'):
    context.callback_payloads = []
  if not hasattr(context, 'log_entities'):
    context.log_entities = []


class Prepare(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  domain_model = ndb.SuperBooleanProperty('6', indexed=False, required=True, default=True)
  
  def run(self, context):
    set_context(context)
    if self.kind_id != None:
      if self.domain_model:
        context.entities[self.kind_id] = context.model(namespace=context.domain.key_namespace)
        context.values[self.kind_id] = context.model(namespace=context.domain.key_namespace)
      else:
        context.entities[self.kind_id] = context.model()
        context.values[self.kind_id] = context.model()
    else:
      if self.domain_model:
        context.entities[context.model.get_kind()] = context.model(namespace=context.domain.key_namespace)
        context.values[context.model.get_kind()] = context.model(namespace=context.domain.key_namespace)
      else:
        context.entities[context.model.get_kind()] = context.model()
        context.values[context.model.get_kind()] = context.model()


class Read(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  
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
  
  write_entities = ndb.SuperStringProperty('5', indexed=False, repeated=True)
  
  def run(self, context):
    entities = select_entities(context, self.write_entities)
    ndb.put_multi(entities)


class Delete(event.Plugin):
  
  delete_entities = ndb.SuperStringProperty('5', indexed=False, repeated=True)
  
  def run(self, context):
    entities = select_entities(context, self.delete_entities)
    ndb.delete_multi(entities)


class Output(event.Plugin):
  
  output_data = ndb.SuperJsonProperty('5', indexed=False, required=True, default={})
  
  def run(self, context):
    for key, value in self.output_data.items():
      context.output[key] = get_attr(context, value)


class FieldAutoUpdate(event.Plugin):  # @todo This could be made more abstract, like: set_attr(context, key, value)!
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  fields = ndb.SuperJsonProperty('6', indexed=False, required=True, default={})
  
  def run(self, context):
    for key, value in self.fields.items():
      if self.kind_id != None:
        set_attr(context.values[self.kind_id], key, value)
      else:
        set_attr(context.values[context.model.get_kind()], key, value)


class Search(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  search = ndb.SuperJsonProperty('6', indexed=False, default={})  # @todo Transform this field to include optional query parameters to include in query.
  
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
    context.next_cursor = next_cursor
    context.more = more
