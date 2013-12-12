# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb, settings
from app.domain.acl import NamespaceDomain, Domain

from google.appengine.api import images
from google.appengine.ext import blobstore
  

class CompanyFeedback(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 45
    
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
    

class Company(ndb.BaseExpando, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 44
    
    # root (namespace Domain)
    # composite index: ancestor:no - state,name
    parent_record = ndb.SuperKeyProperty('1', kind='44', indexed=False)
    name = ndb.SuperStringProperty('2', required=True)
    logo = ndb.SuperImageKeyProperty('3', required=True)# blob ce se implementirati na GCS
    updated = ndb.SuperDateTimeProperty('4', auto_now=True)
    created = ndb.SuperDateTimeProperty('5', auto_now_add=True)
    state = ndb.SuperIntegerProperty('6', required=True)
    
    _default_indexed = False
  
    EXPANDO_FIELDS = {
                      
       'country' : ndb.SuperKeyProperty('7', kind='app.core.misc.Country', required=False),
       'region' : ndb.SuperKeyProperty('8', kind='app.core.misc.CountrySubdivision', required=False),
       'city' : ndb.SuperStringProperty('10', required=False),
       'postal_code' : ndb.SuperStringProperty('11', required=False),
       'street_address' : ndb.SuperStringProperty('12', required=False),
       'street_address2' : ndb.SuperStringProperty('12', required=False),
       'email' : ndb.SuperStringProperty('14'),
       'telephone' : ndb.SuperStringProperty('15'),
       
       'currency' : ndb.SuperKeyProperty('16', kind='app.core.misc.Currency', required=False),
       'paypal_email' : ndb.SuperStringProperty('17'),
       
       'tracking_id' : ndb.SuperStringProperty('18'),
       'feedbacks' : ndb.SuperLocalStructuredProperty(CompanyFeedback, '19', repeated=False),
       
       'location_exclusion' : ndb.SuperBooleanProperty('20', default=False) 
    }
  
    OBJECT_DEFAULT_STATE = 'open'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'open' : (1, ),
        'closed' : (2, ),
        'su_closed' : (3, ), # Ovo je samo ako nam bude trebala kontrola nad DomainStore. 
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'close' : 3,
       'open' : 4,
       'log_message' : 5, # Ovo je samo ako nam bude trebala kontrola nad DomainStore.
       'su_open' : 6,
       'su_close' : 7,
    }
    
    OBJECT_TRANSITIONS = {
        'open' : {
            'from' : ('closed',),
            'to' : ('open',),
         },
        'close' : {
           'from' : ('open', ),
           'to'   : ('closed',),
        },
  
    }
    
    @property
    def is_usable(self):
        return self.get_state == 'open'
    
    def to_dict(self, *args, **kwargs):
        dic = super(Company, self).to_dict(*args, **kwargs)
        
        dic['logo'] = images.get_serving_url(self.logo, 240)
        
        return dic
    
    @classmethod
    def list(cls, values, **kwds):
        response = ndb.Response()
        response.process_input(values, cls, only=False, convert=[('domain', Domain)])
        if response.has_error():
           return response
        response['items'] = cls.query(namespace=values.get('domain').urlsafe()).fetch()
        return response
    
    
    @classmethod
    def manage(cls, create, values, **kwdss):
       
        response = ndb.Response()
        do_not_delete = []

        @ndb.transactional(xg=True)
        def transaction():
             
            if values.get('upload_url'):
               response['upload_url'] = blobstore.create_upload_url(values.get('upload_url'), gs_bucket_name=settings.COMPANY_LOGO_BUCKET)
               return response 
             
            current = ndb.get_current_user()
            
            # domain param is not mandatory, however needs to be provided when we want to create new company
            only = ['name', 'country', 'region', 'city', 'postal_code', 'street_address',
                    'street_address2', 'email', 'telephone', 'currency', 'paypal_email', 'tracking_id']
        
            if 'logo' in values or create:
                only.append('logo')
        
            response.process_input(values, cls, only=only, convert=[('domain', Domain, not create)])
      
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values, only=only)
             
            if entity is None:
               return response.not_found()
             
            if entity and entity.loaded():
                
               new_logo = 'logo' in values
           
               if not entity.domain_is_active:
                  response.error('domain', 'not_active') 
              
               if entity.get_state != 'open':
                  response.error('company', 'not_open') 
                  
               if response.has_error():
                  return response
                
               if current.has_permission('update', entity):
                   
                   if new_logo:
                      blobstore.delete(entity.logo)
                      entity.logo = values.get('logo')
                      do_not_delete.append(entity.logo)
                       
                   
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
                
               domain = values.get('domain')
       
               if not domain:
                  response.required('domain')
                  
               if response.has_error():
                  return response
                   
               entity = cls.prepare(create, values, namespace=domain.urlsafe())
     
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active')
            
               if current.has_permission('create', entity): 
                   entity.set_state(cls.OBJECT_DEFAULT_STATE)
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
            ndb.BlobManager.field_storage_used_blob(do_not_delete)
        except Exception as e:
            response.transaction_error(e)
            
        return response  
 
 
    @classmethod
    def log_message(cls, create, values, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)  
        def transaction(): 
            entity = cls.prepare(create, values, get_only=True)
            if entity and entity.loaded():
               # check if user can do this
               
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active')
    
               current = ndb.get_current_user()
               if current.has_permission('log_message', entity):
                      entity.new_action('log_message', message=values.get('message'), note=values.get('note'))
                      entity.record_action()
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
    def close(cls, values, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
                
               # check if user can do this
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
              
               current = ndb.get_current_user()
           
               if current.has_permission('close', entity):
                      entity.new_action('close', state='closed', message=values.get('message'), note=values.get('note'))
                      entity.put()
                      entity.record_action()
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
    def open(cls, values, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
               # check if user can do this
             
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
               
               current = ndb.get_current_user()
         
               if current.has_permission('open', entity):
                      entity.new_action('open', state='open', message=values.get('message'), note=values.get('note'))
                      entity.put()
                      entity.record_action()
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
 

# done!
class CompanyContent(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 46
    
    # ancestor DomainStore (Catalog, for caching) (namespace Domain)
    # composite index: ancestor:yes - sequence
    title = ndb.SuperStringProperty('1', required=True)
    body = ndb.SuperTextProperty('2', required=True)
    sequence = ndb.SuperIntegerProperty('3', required=True)
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @classmethod
    def delete(cls, values, **kwdss):
 
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
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            # domain param is not mandatory, however needs to be provided when we want to create new company
            response.process_input(values, cls, convert=[('domain', Domain, True), ('company', Company, True)])
          
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