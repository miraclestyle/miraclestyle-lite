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
from app.srv import rule, log, notify


class Context():
  
  def __init__(self):
    self.model = None  # Can we put model here, instead of passing it as argument in methods!?
    self.values = {}
    self.domain_key = None
    self.notify = False
    self.search_callback = None


class Engine():
  
  @classmethod
  def create(cls, model, context):
    if context.cruds.domain_key:
      domain = context.cruds.domain_key.get()
      entity = model(namespace=domain.key_namespace)
    else:
      entity = model()
    if not context.rule.entity:
      context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    @ndb.transactional(xg=True)
    def transaction():
      entity.populate(**context.cruds.values)
      entity.put()
      context.log.entities.append((entity, ))
      log.Engine.run(context)
      rule.read(entity)
      context.output['entity'] = entity
      if context.cruds.notify:
        context.notify.entity = entity
        notify.Engine.run(context)
    
    transaction()
  
  @classmethod
  def update(cls, model, context):
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
        context.notify.entity = entity
        notify.Engine.run(context)
    
    transaction()
  
  @classmethod
  def read(cls, model, context):
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
  def prepare(cls, model, context):
    if context.cruds.domain_key:
      domain = context.cruds.domain_key.get()
      entity = model(namespace=domain.key_namespace)
    else:
      entity = model()
    if not context.rule.entity:
      context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    context.output['entity'] = entity
  
  @classmethod
  def delete(cls, model, context):
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
        context.notify.entity = entity
        notify.Engine.run(context)
    
    transaction()
  
  @classmethod
  def read_records(cls, model, context):
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
  def search(cls, model, context):
    if context.cruds.domain_key:
      domain = context.cruds.domain_key.get()
      entity = model(namespace=domain.key_namespace)
    else:
      entity = model()
    if not context.rule.entity:
      context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    query = model.query()
    search = context.input.get('search')
    if search:
      filters = search.get('filters')
      order_by = search.get('order_by')
      for _filter in filters:
        field = getattr(model, _filter['field'])
        op = _filter['operator']
        value = _filter['value']
        if op == '==': # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this algo needs improvements
          query = query.filter(field == value)
      order_by_field = getattr(model, order_by['field'])
      asc = order_by['operator'] == 'asc'
      if asc:
        query = query.order(order_by_field)
      else:
        query = query.order(-order_by_field)
    else:
      query = query.order(-model.created)
    cursor = Cursor(urlsafe=context.input.get('next_cursor'))
    entities, next_cursor, more = query.fetch_page(settings.SEARCH_PAGE, start_cursor=cursor)
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    if context.cruds.search_callback:
      entities = context.cruds.search_callback(entities)
    for entity in entities:  # @todo Can we async this?
      context.rule.entity = entity
      rule.Engine.run(context)
      rule.read(entity)
    context.output['entities'] = entities
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
