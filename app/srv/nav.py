# -*- coding: utf-8 -*-
'''
Created on Feb 24, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings
from app.srv import rule, event, log


class Filter(ndb.BaseExpando):
 
  # Local structured property
  
  name = ndb.SuperStringProperty('1', required=True) # name that is visible on the link
  kind = ndb.SuperStringProperty('2', required=True) # which model (entity kind) this filter affects
  query = ndb.SuperJsonProperty('3', required=True, default={}) # query parameters that are passed to search function of the model
 

class Widget(ndb.BaseExpando):
  
  _kind = 62
  
  # root (namespace Domain)
  
  name = ndb.SuperStringProperty('1', required=True) # name of the fieldset
  sequence = ndb.SuperIntegerProperty('2', required=True) # global sequence for ordering purposes
  active = ndb.SuperBooleanProperty('3', default=True) # whether this item is active or not
  role = ndb.SuperKeyProperty('4', kind='60', required=True) # to which role this group is attached
  search_form = ndb.SuperBooleanProperty('5', default=True) # whether this group is search form or set of filter buttons/links
  filters = ndb.SuperLocalStructuredProperty(Filter, '6', repeated=True)
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('62', repeated=True),
    '_records_next_cursor': ndb.SuperStringProperty(),
    '_records_more': ndb.SuperBooleanProperty()
  }
  
  _global_role = rule.GlobalRole(
    permissions=[
                 
      rule.ActionPermission('62', event.Action.build_key('62-0').urlsafe(), True,
                            "not context.auth.user._is_guest"),
  
      rule.ActionPermission('62', event.Action.build_key('62-7').urlsafe(), True,
                            "context.auth.user._root_admin or context.auth.user.key == context.rule.entity.key"),
      rule.FieldPermission('62', '_records', True, True, 'True'),
      rule.FieldPermission('62', '_records.note', False, False, 'not context.auth.user.root_admin'),
      rule.FieldPermission('62', '_records.note', True, True, 'context.auth.user.root_admin')
      ]
  )
  
  
  _actions = {'build_menu' : event.Action(id='62-0',
                                          arguments={
                                            'domain' : ndb.SuperKeyProperty(kind='6', required=True)
                                        }),
              'search' : event.Action(id='62-1',
                                      arguments={
                                         'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                         'next_cursor' : ndb.SuperStringProperty(),
                                        }),
              
              'create' : event.Action(id='62-2', 
                                      arguments={
                                        'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                        'name' : ndb.SuperStringProperty(required=True), # name of the fieldset
                                        'sequence' : ndb.SuperIntegerProperty(required=True), # global sequence for ordering purposes
                                        'active' : ndb.SuperBooleanProperty(default=True), # whether this item is active or not
                                        'role' : ndb.SuperKeyProperty(kind='60', required=True), # to which role this group is attached
                                        'search_form' : ndb.SuperBooleanProperty(default=True), # whether this group is search form or set of filter buttons/links
                                        'filters' : ndb.SuperJsonProperty(),                  
                                      }),
              'read' : event.Action(id='62-3', 
                                    arguments={
                                        'key' : ndb.SuperKeyProperty(kind='62', required=True),
                                      }),
              'update' : event.Action(id='62-4', 
                                      arguments={
                                        'key' : ndb.SuperKeyProperty(kind='62', required=True),
                                        'name' : ndb.SuperStringProperty(required=True),  
                                        'sequence' : ndb.SuperIntegerProperty(required=True), 
                                        'active' : ndb.SuperBooleanProperty(default=True), 
                                        'role' : ndb.SuperKeyProperty(kind='60', required=True), 
                                        'search_form' : ndb.SuperBooleanProperty(default=True),
                                        'filters' : ndb.SuperJsonProperty(),                  
                                      }),
              'delete' : event.Action(id='62-5', 
                                      arguments={
                                        'key' : ndb.SuperKeyProperty(kind='62', required=True),
                                      }),
              'prepare' : event.Action(id='62-6', 
                                       arguments={
                                        'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                       }),
              'read_records': event.Action(
                id='62-7',
                arguments={
                  'key': ndb.SuperKeyProperty(kind='62', required=True),
                  'next_cursor': ndb.SuperStringProperty()
                  }
                ),
              
             }
  
  @classmethod
  def selection_roles_helper(cls, namespace):
    return rule.DomainRole.query(rule.DomainRole.active == True, namespace=namespace).fetch()
  
  
  @classmethod
  def _complete_save_helper(cls, entity, context, create):
      
    context.rule.entity = entity
    rule.Engine.run(context)
   
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    role_key = context.input.get('role')
    role = role_key.get()
    
    if role.key_namespace != entity.key_namespace: # both the role and the entity namespace must match, this could be done with rule engine maybe? idk
       raise rule.ActionDenied(context)
     
    filters = []
  
    input_filters = context.input.get('filters')
    
    for filter_data in input_filters:
       filters.append(Filter(**filter_data))
    
    values = {
      'name' : context.input.get('name'),
      'sequence' : context.input.get('sequence'),
      'active' : context.input.get('active'),
      'role' : role_key,
      'search_form' : context.input.get('search_form'),
      'filters' : filters,          
    }
     
    if not create:
       rule.write(entity, values)
    else:
       entity.populate(**values)
       
    entity.put()
    
    context.log.entities.append((entity,))
    
    log.Engine.run(context)
    
    context.output['entity'] = entity
       
  @classmethod
  def create(cls, context):
 
    @ndb.transactional(xg=True)
    def transaction():
      
      domain_key = context.input.get('domain')

      domain = domain_key.get()
      entity = cls(namespace=domain.key_namespace)
     
      cls._complete_save_helper(entity, context, True)  
           
    transaction()
        
    return context
  
  @classmethod
  def update(cls, context):
 
    @ndb.transactional(xg=True)
    def transaction():
    
      entity_key = context.input.get('key')
      entity = entity_key.get()
    
      cls._complete_save_helper(entity, context, False)
       
    transaction()
        
    return context
  
  
  @classmethod
  def prepare(cls, context):
    
    domain_key = context.input.get('domain')
    domain = domain_key.get()
 
    entity = cls(namespace=domain.key_namespace)
    
    context.rule.entity = entity
    
    rule.Engine.run(context)
    
    if not rule.executable(context):
      raise rule.ActionDenied(context)
 
    context.output['entity'] = entity
    context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
    
    return context
  
  @classmethod
  def read(cls, context):
    
    entity_key = context.input.get('key')
    entity = entity_key.get()
    
    context.rule.entity = entity
    
    rule.Engine.run(context)
    
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    rule.read(entity)
    
    context.output['entity'] = entity
    context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
    
    return context
  
  
  @classmethod
  def delete(cls, context):
    
    entity_key = context.input.get('key')
    entity = entity_key.get()
    
    context.rule.entity = entity
    rule.Engine.run(context)
    
    if not rule.executable(context):
      raise rule.ActionDenied(context)
     
    @ndb.transactional(xg=True)
    def transaction():
    
      entity.key.delete()
      context.log.entities.append((entity,))
      log.Engine.run(context)
   
      context.output['entity'] = entity
       
    transaction()
        
    return context
 
     
  
  @classmethod
  def search(cls, context):
    
    context.rule.entity = cls()
    rule.Engine.run(context)
    
    if not rule.executable(context):
       raise rule.ActionDenied(context)
    
    domain_key = context.input.get('domain')
    urlsafe_cursor = context.input.get('next_cursor')
    cursor = Cursor(urlsafe=urlsafe_cursor)
    
    query = cls.query(namespace=domain_key.urlsafe()).order(cls.sequence)
    
    entities, next_cursor, more = query.fetch_page(settings.DOMAIN_ADMIN_PER_PAGE, start_cursor=cursor)
 
    for entity in entities:
       context.rule.entity = entity
       rule.Engine.run(context)
       rule.read(entity)
    
    if next_cursor:
       next_cursor = next_cursor.urlsafe()
    
    context.output['entities'] = entities
    context.output['next_cursor'] = next_cursor
    context.output['more'] = more
 
    return context
  
  
  @classmethod
  def read_records(cls, context):
    entity_key = context.input.get('key')
    next_cursor = context.input.get('next_cursor')
    entity = entity_key.get()
    context.rule.entity = entity
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    entities, next_cursor, more = log.Record.get_records(entity, next_cursor)
    entity._records = entities
    entity._records_next_cursor = next_cursor
    entity._records_more = more
    rule.read(entity)
    context.output['entity'] = entity
    return context
  
  
  @classmethod
  def build_menu(cls, context):
    
    context.rule.entity = cls()
    rule.Engine.run(context)
    
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    
    domain_key = context.input.get('domain')
    domain = domain_key.get()
    
    domain_user_key = rule.DomainUser.build_key(context.auth.user.key_id_str, namespace=domain.key.urlsafe())
    domain_user = domain_user_key.get()
    
    if domain_user:
 
      widgets = cls.query(cls.active == True,
                          cls.role.IN(domain_user.roles),
                          namespace=domain.key_namespace).order(cls.sequence).fetch()
                         
      context.output['menu'] = widgets
      context.output['domain'] = domain
    
    return context