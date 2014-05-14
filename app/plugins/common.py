# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import string

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


class Context(event.Plugin):
  
  def run(self, context):
    from app.srv import auth
    if not hasattr(context, 'entities'):
      context.entities = {}
    if not hasattr(context, 'values'):
      context.values = {}
    context.user = auth.User.current_user()
    # @todo Following lines are temporary!
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
  
  read_entities = ndb.SuperJsonProperty('5', indexed=False, default={})
  
  def run(self, context):
    if len(self.read_entities):
      for key, value in self.read_entities.items():
        entity_key = context.input.get(value)
        context.entities[key] = entity_key.get()
        context.values[key] = copy.deepcopy(context.entities[key])
    else:
      entity_key = context.input.get('key')
      context.entities[context.model.get_kind()] = entity_key.get()
      context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])


class Set(event.Plugin):
  
  static_values = ndb.SuperJsonProperty('5', indexed=False, required=True, default={})
  dynamic_values = ndb.SuperJsonProperty('6', indexed=False, required=True, default={})
  
  def run(self, context):
    for key, value in self.static_values.items():
      set_attr(context, key, value)
    for key, value in self.dynamic_values.items():
      set_attr(context, key, get_attr(context, value))


class Write(event.Plugin):
  
  write_entities = ndb.SuperStringProperty('5', indexed=False, repeated=True)
  
  def run(self, context):
    entities = []
    if len(self.write_entities):
      for kind_id in self.write_entities:
        if kind_id in context.entities:
          entities.append(context.entities[kind_id])
    else:
      entities.append(context.entities[context.model.get_kind()])
    ndb.put_multi(entities)


class Delete(event.Plugin):
  
  delete_entities = ndb.SuperStringProperty('5', indexed=False, repeated=True)
  
  def run(self, context):
    keys = []
    if len(self.delete_entities):
      for kind_id in self.delete_entities:
        if kind_id in context.entities:
          keys.append(context.entities[kind_id].key)
    else:
      keys.append(context.entities[context.model.get_kind()].key)
    ndb.delete_multi(keys)


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
      kwds = {}
      for _filter in filters:
        if _filter['field'] == 'ancestor':
          kwds['ancestor'] = _filter['value']
          continue
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
        elif op == 'contains':
          letters = list(string.printable)
          try:
            last = letters[letters.index(value[-1].lower()) + 1]
            args.append(field >= value)
            args.append(field < last)
          except ValueError as e: # i.e. value not in the letter scope, šččđčžćč for example
            args.append(field == value)
           
      query = query.filter(*args, **kwds)
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
