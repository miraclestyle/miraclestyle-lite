# -*- coding: utf-8 -*-
'''
Created on Apr 2, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings
from app.srv import rule, log

class Engine():
  
  @classmethod
  def _complete_save(cls, entity, context, create):
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    values = {}
    fields = entity.get_fields()
    for field_key in fields:
      values[field_key] = context.input.get(field_key)
    if create:
      entity.populate(**values)  # @todo We do not have field level write control here (known issue with required fields)!
    else:
      rule.write(entity, values)
    entity.put()
    context.log.entities.append((entity, ))
    log.Engine.run(context)
    rule.read(entity)
    context.output['entity'] = entity
  
  @classmethod
  def create(cls, model, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      domain_key = context.input.get('domain')
      if domain_key:
       domain = domain_key.get()
       entity = model(namespace=domain.key_namespace)
      else:
       entity = model()
      cls._complete_save(entity, context, True)
    
    transaction()
  
  @classmethod
  def update(cls, model, context):
    
    @ndb.transactional(xg=True)
    def transaction():
      entity_key = context.input.get('key')
      entity = entity_key.get()
      cls._complete_save(entity, context, False)
    
    transaction()
 
  @classmethod
  def read(cls, model, context):
    
    entity_key = context.input.get('key')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    rule.read(entity)
    context.output['entity'] = entity
  
  @classmethod
  def prepare(cls, model, context):
    domain_key = context.input.get('domain')
    if domain_key:
     domain = domain_key.get()
     entity = model(namespace=domain.key_namespace)
    else:
     entity = model()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    context.output['entity'] = entity
    return context
  
  
  @classmethod
  def delete(cls, model, context):
    
    entity_key = context.input.get('key')
    entity = entity_key.get()
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
    
    transaction()
    
    
  @classmethod
  def read_records(cls, model, context): # dunno if we shuld put also other methods then cruds
    entity_key = context.input.get('key')
    next_cursor = context.input.get('next_cursor')
    entity = entity_key.get()
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
    domain_key = context.input.get('domain')
    if domain_key:
     domain = domain_key.get()
     entity = model(namespace=domain.key_namespace)
    else:
     entity = model()
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
    for entity in entities:  # @todo Can we async this?
      context.rule.entity = entity
      rule.Engine.run(context)
      rule.read(entity)
    context.output['entities'] = entities
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
