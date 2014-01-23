# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb, settings
from app.srv import uom, io, rule, log, blob

from google.appengine.api import images
from google.appengine.ext import blobstore
 

class CompanyFeedback(ndb.BaseModel):
    
    _kind = 45
    
    # LocalStructuredProperty model
    # ovaj model dozvoljava da se radi feedback trending per month per year
    # mozda bi se mogla povecati granulacija per week, tako da imamo oko 52 instance per year, ali mislim da je to nepotrebno!
    # ovde treba voditi racuna u scenarijima kao sto je napr. promena feedback-a iz negative u positive state,
    # tako da se za taj record uradi negative_feedback_count - 1 i positive_feedback_count + 1
    # najbolje je raditi update jednom dnevno, ne treba vise od toga, tako da bi mozda cron ili task queue bilo resenje za agregaciju
    month = ndb.SuperIntegerProperty('1', required=True, indexed=False)
    year = ndb.SuperIntegerProperty('2', required=True, indexed=False)
    positive_feedback_count = ndb.SuperIntegerProperty('3', required=True, indexed=False)
    negative_feedback_count = ndb.SuperIntegerProperty('4', required=True, indexed=False)
    neutral_feedback_count = ndb.SuperIntegerProperty('5', required=True, indexed=False)
    

class Company(ndb.BaseExpando):
    
    _kind = 44
    
    # root (namespace Domain)
    # composite index: ancestor:no - state,name
    parent_record = ndb.SuperKeyProperty('1', kind='44', indexed=False)
    name = ndb.SuperStringProperty('2', required=True)
    complete_name = ndb.SuperTextProperty('3')
    logo = ndb.SuperImageKeyProperty('4', required=True)# blob ce se implementirati na GCS
    updated = ndb.SuperDateTimeProperty('5', auto_now=True)
    created = ndb.SuperDateTimeProperty('6', auto_now_add=True)
    state = ndb.SuperStringProperty('7', required=True)
    
    _default_indexed = False
  
    _expando_fields = {
                      
       'country' : ndb.SuperKeyProperty('8', kind='15', required=False),
       'region' : ndb.SuperKeyProperty('9', kind='16', required=False),
       'city' : ndb.SuperStringProperty('10', required=False),
       'postal_code' : ndb.SuperStringProperty('11', required=False),
       'street' : ndb.SuperStringProperty('12', required=False),
       'email' : ndb.SuperStringProperty('14'),
       'telephone' : ndb.SuperStringProperty('15'),
       'currency' : ndb.SuperKeyProperty('16', kind=uom.Unit, required=False),
       'paypal_email' : ndb.SuperStringProperty('17'),
       'tracking_id' : ndb.SuperStringProperty('18'),
       'feedbacks' : ndb.SuperLocalStructuredProperty(CompanyFeedback, '19', repeated=False),
       'location_exclusion' : ndb.SuperBooleanProperty('20', default=False) 
    }
 
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('44', io.Action.build_key('44-0').urlsafe(), False, "not context.rule.entity.is_open"),
                                            rule.ActionPermission('44', io.Action.build_key('44-1').urlsafe(), False, "not context.rule.entity.is_open"),
                                            rule.ActionPermission('44', io.Action.build_key('44-2').urlsafe(), False, "context.rule.entity.is_open"),
                                            rule.ActionPermission('44', io.Action.build_key('44-3').urlsafe(), False, "not context.rule.entity.is_open"),
                                            ])
 
    _actions = {
       'manage' : io.Action(id='44-0',
                              arguments={
                                         
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'parent_record' : ndb.SuperKeyProperty(kind='44', required=False),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'logo' : ndb.SuperImageKeyProperty(required=True),
                                 'domain' : ndb.SuperKeyProperty(kind='6'),
                                 
                                 # expando
                                 'country' : ndb.SuperKeyProperty(kind='15'),
                                 'region' : ndb.SuperKeyProperty(kind='16'),
                                 'city' : ndb.SuperStringProperty(),
                                 'postal_code' : ndb.SuperStringProperty(),
                                 'street' : ndb.SuperStringProperty(),
                                 'email' : ndb.SuperStringProperty(),
                                 'telephone' : ndb.SuperStringProperty(),
                                 'currency' : ndb.SuperKeyProperty(kind='19'),
                                 'paypal_email' : ndb.SuperStringProperty(),
                                 'tracking_id' : ndb.SuperStringProperty(),
                                 'feedbacks' : ndb.SuperLocalStructuredProperty(CompanyFeedback),
                                 'location_exclusion' : ndb.SuperBooleanProperty(),
                                 
                                 # update
                                 'key'  : ndb.SuperKeyProperty(kind='44', required=True),
                                 
                                 
                              }
                             ),
                
       'close' : io.Action(id='44-1',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='44', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'open' : io.Action(id='44-2',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='44', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'log_message' : io.Action(id='44-3',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='44', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True),
                              }
                             ),
                
       'list' : io.Action(id='44-4',
                              arguments={
                                  'domain' : ndb.SuperKeyProperty(kind='6', required=True)
                              }
                             ),
    }
    
    @property
    def is_open(self):
        return self.state == 'open'
    
    def to_dict(self, *args, **kwargs):
      
        dic = super(Company, self).to_dict(*args, **kwargs)
        
        dic['logo'] = images.get_serving_url(self.logo, 240)
        
        return dic
      
    @classmethod
    def manage(cls, args):
        action = cls._actions.get('manage')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
               create = context.args.get('create')
               
               if context.args.get('upload_url'):
                  context.response['upload_url'] = blobstore.create_upload_url(context.args.get('upload_url'), gs_bucket_name=settings.COMPANY_LOGO_BUCKET)
                  return context
               
               set_args = context.args.copy()
               
               if create:
                  entity = cls(state='open', namespace=context.auth.domain.key.urlsafe())
                  if 'logo' not in context.args:
                      return context.required('logo')
               else:
                  entity_key = context.args.get('key')
                  entity = entity_key.get()
                  del set_args['key']
                  
               del set_args['create']
                
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
                  
               entity.populate(**set_args)
               entity.put()
               
               context.status(entity)
               
               context.log.entities.append((entity, ))
               log.Engine.run(context)
               
               # mark the logo as used, if it was just uploaded
               if 'logo' in context.args:
                   blob.Manager.used_blobs(entity.logo)
               
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
    
    @classmethod
    def close(cls, args):
      
        action = cls._actions.get('close')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('key')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
               
               entity.state = 'closed'
               entity.put()
               
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
 
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
    
    @classmethod
    def open(cls, args):
      
        action = cls._actions.get('open')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('key')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
               
               entity.state = 'open'
               entity.put()
               
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
 
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
    
    @classmethod
    def log_message(cls, args):
     
        action = cls._actions.get('log_message')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('key')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
                
               entity.put() # ref project-documentation.py #L-244
  
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
               
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
    
    @classmethod
    def list(cls, args):
        action = cls._actions.get('list')
        context = action.process(args)
        
        if not context.has_error():
           
           @ndb.transactional(xg=True)
           def transaction():
               context.response['companies'] = cls.query(namespace=context.auth.domain.key.urlsafe())
              
        return context
 
 

# done!
class CompanyContent(ndb.BaseModel):
    
    _kind = 46
    
    # ancestor DomainStore (Catalog, for caching) (namespace Domain)
    # composite index: ancestor:yes - sequence
    title = ndb.SuperStringProperty('1', required=True)
    body = ndb.SuperTextProperty('2', required=True)
    sequence = ndb.SuperIntegerProperty('3', required=True)
    
    
    @classmethod
    def delete(cls, args):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
                 
                  if entity.get_state != 'open':
                     return response.error('company', 'not_open') 
                       
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response
    
    @classmethod
    def manage(cls, args):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            # domain param is not mandatory, however needs to be provided when we want to create new company
            response.process_input(values, cls, convert=[ndb.SuperKeyProperty('company', kind=Company, required=create)])
          
            if response.has_error():
               return response
 
                   
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if entity and entity.loaded():
                
               company = entity.key.parent().get()
               
               if company.get_state != 'open':
                  return response.error('company', 'not_open')
              
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
                   
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
 
               company = values.get('company')  
               if not company:
                  return response.required('company')
               
               entity = cls.prepare(create, values, parent=company)
              
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active')  
              
               company = entity.key.parent().get()
              
               if company.get_state != 'open':
                  return response.error('company', 'not_open')
                
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response  