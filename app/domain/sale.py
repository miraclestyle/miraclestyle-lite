# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.core.misc import Location
from app.domain.acl import NamespaceDomain

# done!
class Carrier(ndb.BaseModel, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 49
    
    # root (namespace Domain)
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L27
    # http://hg.tryton.org/modules/carrier/file/tip/carrier.py#l10
    # composite index: ancestor:no - active,name
    name = ndb.SuperStringProperty('1', required=True)
    active = ndb.SuperBooleanProperty('2', default=True)
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @classmethod
    def delete(cls, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds, only=False, populate=False)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
  
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
    def manage(cls, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
     
            # domain param is not mandatory, however needs to be provided when we want to create new company
            response.validate_input(kwds, cls, convert=[('domain', ndb.Key, True)])
          
            if response.has_error():
               return response
  
            entity = cls.get_or_prepare(kwds)
            
            if entity is None:
               return response.not_found()
             
            if entity and entity.loaded():
 
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
                   
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
                
               domain = kwds.get('domain')
               if not domain:
                  return response.requred('domain')
         
               entity = cls.get_or_prepare(kwds, namespace=domain.urlsafe())
              
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active')  
   
                
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
     

# done!
class CarrierLineRule(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 51
    
    # LocalStructuredProperty model
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L226
    # ovde se cuvaju dve vrednosti koje su obicno struktuirane kao formule, ovo je mnogo fleksibilnije nego hardcoded struktura informacija koje se cuva kao sto je bio prethodni slucaj
    condition = ndb.SuperStringProperty('1', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: True ili weight[kg] >= 5 ili volume[m3] = 0.002
    price = ndb.SuperStringProperty('2', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: amount = 35.99 ili amount = weight[kg]*0.28
    # weight - kg; volume - m3; ili sta vec odlucimo, samo je bitno da se podudara sa measurementsima na ProductTemplate/ProductInstance
     

# done!
class CarrierLine(ndb.BaseExpando, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 50
    
    # ancestor DomainCarrier (namespace Domain)
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L170
    # composite index: ancestor:yes - sequence; ancestor:yes - active,sequence
    name = ndb.SuperStringProperty('1', required=True)
    sequence = ndb.SuperIntegerProperty('2', required=True)
    location_exclusion = ndb.SuperBooleanProperty('3', default=False, indexed=False)
    active = ndb.SuperBooleanProperty('4', default=True)
    
    _default_indexed = False
  
    # Expando
    # locations = ndb.LocalStructuredProperty(Location, '5', repeated=True)# soft limit 300x
    # rules = ndb.LocalStructuredProperty(CarrierLineRule, '6', repeated=True)# soft limit 300x
    
    EXPANDO_FIELDS = {
       'locations' : ndb.LocalStructuredProperty(Location, '5', repeated=True),
       'rules' : ndb.LocalStructuredProperty(CarrierLineRule, '6', repeated=True)           
    }
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }

    @classmethod
    def delete(cls, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds, only=False, populate=False)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
  
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
    def manage(cls, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
     
            # domain param is not mandatory, however needs to be provided when we want to create new company
            response.validate_input(kwds, cls, convert=[('domain', ndb.Key, True)])
          
            if response.has_error():
               return response
  
            entity = cls.get_or_prepare(kwds)
            
            if entity is None:
               return response.not_found()
             
            if entity and entity.loaded():
 
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
                   
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
                
               domain = kwds.get('domain')
               if not domain:
                  return response.requred('domain')
         
               entity = cls.get_or_prepare(kwds, namespace=domain.urlsafe())
              
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active')  
   
                
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
    name = ndb.SuperStringProperty('1', required=True)
    logo = ndb.SuperBlobKeyProperty('2', required=True)# blob ce se implementirati na GCS
    updated = ndb.SuperDateTimeProperty('3', auto_now=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True)
    state = ndb.SuperIntegerProperty('5', required=True)
    
    _default_indexed = False
 
    EXPANDO_FIELDS = {
                      
       'country' : ndb.SuperKeyProperty('7', kind='app.core.misc.Country', required=True),
       'region' : ndb.SuperKeyProperty('8', kind='app.core.misc.CountrySubdivision', required=True),
       'city' : ndb.SuperStringProperty('10', required=True),
       'postal_code' : ndb.SuperStringProperty('11', required=True),
       'street_address' : ndb.SuperStringProperty('12', required=True),
       'street_address2' : ndb.SuperStringProperty('12', required=True),
       'email' : ndb.SuperStringProperty('14'),
       'telephone' : ndb.SuperStringProperty('15'),
       
       'currency' : ndb.SuperKeyProperty('16', kind='app.core.misc.Country', required=True),
       'paypal_email' : ndb.SuperStringProperty('17'),
       
       'tracking_id' : ndb.SuperStringProperty('18'),
       'feedbacks' : ndb.SuperLocalStructuredProperty(CompanyFeedback, '19', repeated=True),
       
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
       'sudo' : 5, # Ovo je samo ako nam bude trebala kontrola nad DomainStore. 
       'log_message' : 6, # Ovo je samo ako nam bude trebala kontrola nad DomainStore. 
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
        # Ovo je samo ako nam bude trebala kontrola nad DomainStore. 
        'su_open' : {
            'from' : ('su_closed', 'closed',),
            'to' : ('open',),
         },
         # Ovo je samo ako nam bude trebala kontrola nad DomainStore. 
        'su_close' : {
           'from' : ('open', 'closed',),
           'to'   : ('su_closed',),
        },
    }
    
    
    @classmethod
    def manage(cls, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
            
            # domain param is not mandatory, however needs to be provided when we want to create new company
            response.validate_input(kwds, cls, only=('name', 'logo'), convert=[('domain', ndb.Key, True)])
          
            if response.has_error():
               return response
  
            entity = cls.get_or_prepare(kwds)
            
            if entity is None:
               return response.not_found()
             
            if entity and entity.loaded():
 
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
              
               if not entity.get_state != 'open':
                  return response.error('company', 'not_open') 
                
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
                
               domain = kwds.get('domain')
               
               if not domain:
                  return response.required('domain')
                   
               entity = cls.get_or_prepare(kwds, namespace=domain.urlsafe())
     
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active')
            
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
        
  
    # Ova akcija suspenduje ili aktivira domenu. Ovde cemo dalje opisati posledice suspenzije
    @classmethod
    def sudo(cls, **kwds):
        
        response = ndb.Response()
        
        @ndb.transactional(xg=True) 
        def transaction(): 
            entity = cls.get_or_prepare(kwds, populate=False, only=False)
            if entity and entity.loaded():
               # check if user can do this
               
               current = cls.get_current_user()
               if current.has_permission('sudo', entity):
                      state = kwds.get('state')
                      entity.new_action('sudo', state=state, message=kwds.get('message'), note=kwds.get('note'))
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
    def log_message(cls, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)  
        def transaction(): 
            entity = cls.get_or_prepare(kwds, populate=False, only=False)
            if entity and entity.loaded():
               # check if user can do this
               
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active')
    
               current = cls.get_current_user()
               if current.has_permission('log_message', entity):
                      entity.new_action('log_message', message=kwds.get('message'), note=kwds.get('note'))
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
    def close(cls, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)
        def transaction(): 
            entity = cls.get_or_prepare(kwds, populate=False, only=False)
            if entity and entity.loaded():
                
               # check if user can do this
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
              
               current = cls.get_current_user()
          
               if entity.get_state not in ('open',):
                  return response.not_authorized()
               
               if current.has_permission('close', entity):
                      entity.new_action('close', state='closed', message=kwds.get('message'), note=kwds.get('note'))
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
    def open(cls, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)
        def transaction(): 
            entity = cls.get_or_prepare(kwds, populate=False, only=False)
            if entity and entity.loaded():
               # check if user can do this
             
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
               
               current = cls.get_current_user()
          
               if entity.get_state not in ('closed',):
                  return response.not_authorized()
               
               if current.has_permission('open', entity):
                      entity.new_action('open', state='open', message=kwds.get('message'), note=kwds.get('note'))
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
    def delete(cls, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds, only=False, populate=False)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
                 
                  if not entity.get_state != 'open':
                     return response.error('store', 'not_open') 
                       
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
    def manage(cls, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
     
            # domain param is not mandatory, however needs to be provided when we want to create new company
            response.validate_input(kwds, cls, convert=[('domain', ndb.Key, True), ('company', ndb.Key, True)])
          
            if response.has_error():
               return response
 
                   
            entity = cls.get_or_prepare(kwds)
            
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
                
               domain = kwds.get('domain')
               if not domain:
                  return response.requred('domain')
                
               company = kwds.get('company')  
               if not company:
                  return response.required('company')
               
               entity = cls.get_or_prepare(kwds, namespace=domain.urlsafe(), parent=company)
              
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
     

# done!
class CompanyShippingExclusion(Location, ndb.Workflow):
    
    KIND_ID = 47
    
    # ancestor DomainStore (DomainCatalog, for caching) (namespace Domain)
    # ovde bi se indexi mozda mogli dobro iskoristiti?
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @classmethod
    def delete(cls, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds, only=False, populate=False)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
                 
                  if not entity.get_state != 'open':
                     return response.error('store', 'not_open') 
                       
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
    def manage(cls, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
     
            # domain param is not mandatory, however needs to be provided when we want to create new company
            response.validate_input(kwds, cls, convert=[('domain', ndb.Key, True), ('company', ndb.Key, True)])
          
            if response.has_error():
               return response
 
                   
            entity = cls.get_or_prepare(kwds)
            
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
                
               domain = kwds.get('domain')
               if not domain:
                  return response.requred('domain')
                
               company = kwds.get('company')  
               if not company:
                  return response.required('company')
               
               entity = cls.get_or_prepare(kwds, namespace=domain.urlsafe(), parent=company)
              
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
   

# done!
class Tax(ndb.BaseExpando, ndb.Workflow):
    
    KIND_ID = 48
    
    # root (namespace Domain)
    # composite index: ancestor:no - active,sequence
    name = ndb.SuperStringProperty('1', required=True)
    sequence = ndb.SuperIntegerProperty('2', required=True)
    amount = ndb.SuperStringProperty('3', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: 17.00[%] ili 10.00[c] gde je [c] = currency
    location_exclusion = ndb.SuperBooleanProperty('4', default=False, indexed=False)# applies to all locations except/applies to all locations listed below
    active = ndb.SuperBooleanProperty('5', default=True)
    
    _default_indexed = False
  
    EXPANDO_FIELDS = {
                      
       'locations' : ndb.SuperLocalStructuredProperty(Location, '6', repeated=True),
       'product_categories' : ndb.SuperKeyProperty('7', kind='app.core.misc.ProductCategory', repeated=True),
       'carriers' : ndb.SuperKeyProperty('8', kind=Carrier, repeated=True)
                  
    }
  
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @classmethod
    def delete(cls, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds, only=False, populate=False)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
  
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
    def manage(cls, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
     
            # domain param is not mandatory, however needs to be provided when we want to create new company
            response.validate_input(kwds, cls, convert=[('domain', ndb.Key, True)])
          
            if response.has_error():
               return response
  
            entity = cls.get_or_prepare(kwds)
            
            if entity is None:
               return response.not_found()
             
            if entity and entity.loaded():
 
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
                   
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
                
               domain = kwds.get('domain')
               if not domain:
                  return response.requred('domain')
         
               entity = cls.get_or_prepare(kwds, namespace=domain.urlsafe())
              
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active')  
   
                
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