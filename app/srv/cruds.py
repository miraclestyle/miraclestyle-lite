# -*- coding: utf-8 -*-
'''
Created on Apr 2, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)

THIS IS BRUTE 'HACK' THAT BRAKES ESTABLISHED ARCHITECTURAL PATTERN!
ALTHOUGH IT RESEMBLES TO A COMPLEMENTARY SERVICE, IN FACT IT ISN'T,
AS IT CREATES LOGICAL DEPENDENCY OF MODEL HOSTED FUNCTIONS!
IT WAS CREATED TO TEMPORARY REMEDY CODE REDUNDANCY ISSUE!
'''

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings
from app.srv import log, callback

def get_rule(): 
  # hack for circular behaviour
  from app.srv import rule
  return rule


class Context():
  
  def __init__(self):
    self.entity = None
    self.values = {}
    self.notify = True
    self.search_entities_callback = None
    self.search_filter_callback = None


class Engine():
  
  @classmethod
  def create(cls, context):
    rule = get_rule()
    entity = context.cruds.entity
    if not context.rule.entity:
      context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      rule.write(entity, context.cruds.values)
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
      rule.read(entity)
      context.output['entity'] = entity
      if context.cruds.notify:
        context.callback.payloads.append(('notify',
                                          {'action_key': 'initiate',
                                           'action_model': '61',
                                           'caller_entity': entity.key.urlsafe()}))
        callback.Engine.run(context)
    
    transaction()
  
  @classmethod
  def update(cls, context):
    rule = get_rule()
    entity_key = context.input.get('key')
    entity = entity_key.get()
    if not context.rule.entity:
      context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      rule.write(entity, context.cruds.values)
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
      rule.read(entity)
      context.output['entity'] = entity
      if context.cruds.notify:
        context.callback.payloads.append(('notify',
                                          {'action_key': 'initiate',
                                           'action_model': '61',
                                           'caller_entity': entity.key.urlsafe()}))
        callback.Engine.run(context)
    
    transaction()
  
  @classmethod
  def read(cls, context):
    rule = get_rule()
    entity_key = context.input.get('key')
    entity = entity_key.get()
    if not context.rule.entity:
      context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    rule.read(entity)
    context.output['entity'] = entity
  
  @classmethod
  def prepare(cls, context):
    rule = get_rule()
    entity = context.cruds.entity
    if not context.rule.entity:
      context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    context.output['entity'] = entity
  
  @classmethod
  def delete(cls, context):
    rule = get_rule()
    entity_key = context.input.get('key')
    entity = entity_key.get()
    if not context.rule.entity:
      context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      entity.key.delete()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
      rule.read(entity)
      context.output['entity'] = entity
      if context.cruds.notify:
        context.callback.payloads.append(('notify',
                                          {'action_key': 'initiate',
                                           'action_model': '61',
                                           'caller_entity': entity.key.urlsafe()}))
        callback.Engine.run(context)
    
    transaction()
  
  @classmethod
  def read_records(cls, context):
    rule = get_rule()
    entity_key = context.input.get('key')
    next_cursor = context.input.get('next_cursor')
    entity = entity_key.get()
    if not context.rule.entity:
      context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    entities, next_cursor, more = log.Record.get_records(entity, next_cursor)
    entity._records = entities
    rule.read(entity)
    context.output['entity'] = entity
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
  
  @classmethod
  def search(cls, context):
    rule = get_rule()
    namespace = None
    entity = context.cruds.entity
    model = entity.__class__
    if not context.rule.entity:
      context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    query = model.query(namespace=entity.key_namespace)
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
      order_by_field = getattr(model, order_by['field'])
      asc = order_by['operator'] == 'asc'
      if asc:
        query = query.order(order_by_field)
      else:
        query = query.order(-order_by_field)
    
    if context.cruds.search_filter_callback:
       query = context.cruds.search_filter_callback(context, query) # callback for query filter
       
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    entities, next_cursor, more = query.fetch_page(settings.SEARCH_PAGE, start_cursor=cursor)
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    if context.cruds.search_entities_callback:
      entities = context.cruds.search_entities_callback(context, entities) # callback for entities, make changes before .read
    for entity in entities:
      context.rule.entity = entity
      rule.Engine.run(context)
      rule.read(entity)
    context.output['entities'] = entities
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
