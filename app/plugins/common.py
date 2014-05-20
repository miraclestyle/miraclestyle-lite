# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import string

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings, memcache, util
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


class Context(event.Plugin):
  
  def run(self, context):
    # @todo Following lines are temporary, until we decide where and how to distribute them!
    context.user = context.models['0'].current_user()
    caller_user_key = context.input.get('caller_user')
    if context.user._is_taskqueue and caller_user_key:
      caller_user = caller_user_key.get()
      if caller_user:
        context.user = caller_user
    context.namespace = None
    domain_key = context.input.get('domain')
    if domain_key:
      context.domain = domain_key.get()
      context.namespace = context.domain.key_namespace
    if not hasattr(context, 'entities'):
      context.entities = {}
    if not hasattr(context, 'values'):
      context.values = {}
    if not hasattr(context, 'callback_payloads'):
      context.callback_payloads = []
    if not hasattr(context, 'log_entities'):
      context.log_entities = []
    if not hasattr(context, 'blob_delete'):
      context.blob_delete = []
    if not hasattr(context, 'blob_write'):
      context.blob_write = []


class Set(event.Plugin):
  
  static_values = ndb.SuperJsonProperty('5', indexed=False, required=True, default={})
  dynamic_values = ndb.SuperJsonProperty('6', indexed=False, required=True, default={})
  
  def run(self, context):
    for key, value in self.static_values.items():
      set_attr(context, key, value)
    for key, value in self.dynamic_values.items():
      set_attr(context, key, get_attr(context, value))


class Prepare(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  domain_model = ndb.SuperBooleanProperty('6', indexed=False, required=True, default=True)
  
  def run(self, context):
    namespace = None
    if self.kind_id != None:
      kind_id = self.kind_id
    else:
      kind_id = context.model.get_kind()
    if self.domain_model:
      namespace = context.namespace
    context.entities[kind_id] = context.model(namespace=namespace)
    context.values[kind_id] = context.model(namespace=namespace)


class Read(event.Plugin):
  
  read_entities = ndb.SuperJsonProperty('5', indexed=False, default={})
  
  def run(self, context):
    keys = []
    values = []
    if len(self.read_entities):
      for key, value in self.read_entities.items():
        keys.append(key)
        values.append(context.input.get(value))
    else:
      keys.append(context.model.get_kind())
      values.append(context.input.get('key'))
    entities = ndb.get_multi(values)
    for i, key in enumerate(keys):
      context.entities[key] = entities[i]
      context.values[key] = copy.deepcopy(context.entities[key])


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
  page_size = ndb.SuperIntegerProperty('6', indexed=False, required=True, default=10)
  search = ndb.SuperJsonProperty('7', indexed=False, default={})  # @todo Transform this field to include optional query parameters to include in query.
  
  def run(self, context):
    namespace = None
    if self.kind_id != None:
      kind_id = self.kind_id
    else:
      kind_id = context.model.get_kind()
    model = context.models[kind_id]
    if context.entities[kind_id].key:
      namespace = context.entities[kind_id].key_namespace
    value = None
    search = context.input.get('search')
    if search:
      args = []
      kwds = {}
      filters = search.get('filters')
      order_by = search.get('order_by')
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
          except ValueError as e:  # Value not in the letter scope, šččđčžćč for example.
            args.append(field == value)
      query = model.query(namespace=namespace, **kwds)
      query = query.filter(*args)
      if order_by:
        order_by_field = getattr(model, order_by['field'])
        if order_by['operator'] == 'asc':
          query = query.order(order_by_field)
        else:
          query = query.order(-order_by_field)
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    def value_is_key(value):
      if isinstance(value, list) and len(value):
        for v in value:
          if not isinstance(v, ndb.Key):
            return False
        return True
      elif isinstance(value, ndb.Key):
        return True
      else:
        return False
    if value_is_key(value):
      # this has to be done like this because there is no way to order the fetched items
      # in the order the keys were provided, the MultiQuery disallowes that http://stackoverflow.com/questions/12449197/badargumenterror-multiquery-with-cursors-requires-key-order-in-ndb
      keys = value
      if not isinstance(keys, list):
        keys = [value]
      entities = ndb.get_multi(keys)
      cursor = None
      more = False
    else:
      if self.page_size != None and self.page_size > 0:
        entities, cursor, more = query.fetch_page(self.page_size, start_cursor=cursor)
        if cursor:
          cursor = cursor.urlsafe()
      else:
        entities = query.fetch()
        cursor = None
        more = False
    context.entities = entities
    context.search_cursor = cursor
    context.search_more = more
