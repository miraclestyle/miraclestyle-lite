# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb, settings
from app.srv import uom, event, rule, log, blob

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
    logo = ndb.SuperLocalStructuredImageProperty(blob.Image, '4', required=True)# blob ce se implementirati na GCS
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
       'currency' : ndb.SuperKeyProperty('16', kind=uom.Unit, required=False), # not solved
       'tracking_id' : ndb.SuperStringProperty('18'), # not solved
       'feedbacks' : ndb.SuperLocalStructuredProperty(CompanyFeedback, '19', repeated=False),
 
    }
 
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('44', event.Action.build_key('44-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'open')"),
                                            rule.ActionPermission('44', event.Action.build_key('44-4').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'open')"),
                                            rule.ActionPermission('44', event.Action.build_key('44-1').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'open')"),
                                            rule.ActionPermission('44', event.Action.build_key('44-2').urlsafe(), False, "context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'open'"),
                                            rule.ActionPermission('44', event.Action.build_key('44-3').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'open')"),
                                            ])
 
    _actions = {
       'create' : event.Action(id='44-0',
                              arguments={
 
                                 'parent_record' : ndb.SuperKeyProperty(kind='44', required=False),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'logo' : ndb.SuperLocalStructuredImageProperty(blob.Image),
                                 'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                 
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
                                 'feedbacks' : ndb.SuperLocalStructuredProperty(CompanyFeedback, required=False),
                                 'location_exclusion' : ndb.SuperBooleanProperty(),
                  
                                 # upload url
                                 'upload_url' : ndb.SuperStringProperty(),
                                 
                                 
                              }
                             ),
                
       'update' : event.Action(id='44-4',
                              arguments={
 
                                 'parent_record' : ndb.SuperKeyProperty(kind='44', required=False),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'logo' : ndb.SuperLocalStructuredImageProperty(blob.Image),
        
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
                                 'feedbacks' : ndb.SuperLocalStructuredProperty(CompanyFeedback, required=False),
                                 'location_exclusion' : ndb.SuperBooleanProperty(),
                                 
                                 # update
                                 'key'  : ndb.SuperKeyProperty(kind='44', required=True),
                                 
                                 # upload url
                                 
                                 'upload_url' : ndb.SuperStringProperty(),
                                 
                                 
                              }
                             ),
                
       'close' : event.Action(id='44-1',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='44', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'open' : event.Action(id='44-2',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='44', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
   
                
       'list' : event.Action(id='44-4',
                              arguments={
                                  'domain' : ndb.SuperKeyProperty(kind='6', required=True)
                              }
                             ),
    }
  
    def __todict__(self, *args, **kwargs):
      
        dic = super(Company, self).__todict__(*args, **kwargs)
        
        dic['logo'] = images.get_serving_url(self.logo.image, 240)
        
        return dic
      
    @classmethod
    def complete_save(cls, entity, context):
      
         upload_url = context.args.get('upload_url')
         if upload_url:
               context.response['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.COMPANY_LOGO_BUCKET)
               return context
                    
         context.rule.entity = entity
         rule.Engine.run(context)
            
         if not rule.executable(context):
           return context.not_authorized()
         
         set_args = {}
      
         for field_name in cls.get_fields():
             if field_name in context.args:
                set_args[field_name] = context.args.get(field_name)
  
         entity.populate(**set_args)
         
         ndb.make_complete_name(entity, 'name', 'parent_record')
         
            
         entity.put()
            
         context.status(entity)
            
         context.log.entities.append((entity, ))
         log.Engine.run(context)
            
         # mark the logo as used, if it was just uploaded
         if 'logo' in context.args:
             blob.Manager.used_blobs(entity.logo.image)
      
    @classmethod
    def create(cls, context):

        @ndb.transactional(xg=True)
        def transaction():
 
            domain_key = context.args.get('domain')
            domain = domain_key.get()
            entity = cls(state='open', namespace=domain.key_namespace)
            
            if 'upload_url' not in context.args: 
                if 'logo' not in context.args:
                    return context.required('logo')
 
            cls.complete_save(entity, context)
 
        try:
           transaction()
        except Exception as e:
           context.transaction_error(e)
        
        return context
      
    @classmethod
    def update(cls, context):

        @ndb.transactional(xg=True)
        def transaction():
  
            entity_key = context.args.get('key')
            entity = entity_key.get()
           
            cls.complete_save(entity, context)
            
        try:
           transaction()
        except Exception as e:
           context.transaction_error(e)
        
        return context
    
    @classmethod
    def close(cls, context):
 
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
    def open(cls, context):
   
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
    def list(cls, context):
 
        domain_key = context.args.get('domain')
        domain = domain_key.get()
           
        context.response['companies'] = cls.query(namespace=domain.key_namespace).fetch()
  
        return context
 
 

# done!
class CompanyContent(ndb.BaseModel):
    
    _kind = 46
    
    # ancestor DomainStore (Catalog, for caching) (namespace Domain)
    # composite index: ancestor:yes - sequence
    title = ndb.SuperStringProperty('1', required=True)
    body = ndb.SuperTextProperty('2', required=True)
    sequence = ndb.SuperIntegerProperty('3', required=True)


    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('46', event.Action.build_key('46-0').urlsafe(),
                                                                     False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'open')"),
                                                rule.ActionPermission('46', event.Action.build_key('46-3').urlsafe(),
                                                                     False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'open')"),                                        
                                                rule.ActionPermission('46', event.Action.build_key('46-1').urlsafe(),
                                                                     False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'open')"),
                                               ])
 

    _actions = {
       'create' : event.Action(id='46-0',
                              arguments={
                                 'title' : ndb.SuperStringProperty(required=True),
                                 'body' : ndb.SuperTextProperty(required=True),
                                 'company' : ndb.SuperKeyProperty(kind='44', required=True),
                                 'sequence' : ndb.SuperIntegerProperty(required=True),
                              }
                             ),
                
       'update' : event.Action(id='46-3',
                              arguments={
                                 
                                 'title' : ndb.SuperStringProperty(required=True),
                                 'body' : ndb.SuperTextProperty(required=True),
                                 'sequence' : ndb.SuperIntegerProperty(required=True),
                                 
                                 'key' : ndb.SuperKeyProperty(kind='46', required=True)
                              }
                             ),
                
       'delete' : event.Action(id='46-1',
                              arguments={
                                   'key' : ndb.SuperKeyProperty(kind='46', required=True)
                              }
                             ),
                
       'list' : event.Action(id='46-2',
                              arguments={
                                  'company' : ndb.SuperKeyProperty(kind='44', required=True),
                              }
                             ),
    }  
 
    @classmethod
    def list(cls, context):
 
         company_key = context.args.get('company')
         company = company_key.get()
         if not company.state == 'open':
            return context.error('company', 'not_open')
         context.response['contents'] = cls.query(ancestor=company_key).fetch()
            
         return context
         
    @classmethod
    def delete(cls, context):
         
         @ndb.transactional(xg=True)
         def transaction():
                         
              entity_key = context.args.get('key')
              entity = entity_key.get()
              context.rule.entity = entity
              rule.Engine.run(context)
              if not rule.executable(context):
                 return context.not_authorized()
               
              entity.key.delete()
              context.log.entities.append((entity,))
              log.Engine.run(context)

              context.status(entity)
              
         try:
            transaction()
         except Exception as e:
            context.transaction_error(e)
            
         return context
       
    @classmethod
    def complete_save(cls, entity, context):
      
       context.rule.entity = entity
       rule.Engine.run(context)
       
       if not rule.executable(context):
          return context.not_authorized()
       
       entity.title = context.args.get('title')
       entity.body = context.args.get('body')
       entity.sequence = context.args.get('sequence')
       entity.put()
        
       context.log.entities.append((entity, ))
       log.Engine.run(context)
          
       context.status(entity)
       
    @classmethod
    def create(cls, context):
 
         @ndb.transactional(xg=True)
         def transaction():
  
             company_key = context.args.get('company')
             entity = cls(parent=company_key)
      
             cls.complete_save(entity, context)
            
         try:
             transaction()
         except Exception as e:
             context.transaction_error(e)
         
         return context
      
    @classmethod
    def update(cls, context):
 
         @ndb.transactional(xg=True)
         def transaction():
           
             entity_key = context.args.get('key')
             entity = entity_key.get()
  
             cls.complete_save(entity, context)
            
         try:
             transaction()
         except Exception as e:
             context.transaction_error(e)
         
         return context
 