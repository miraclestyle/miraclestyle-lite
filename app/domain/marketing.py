# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import datetime

from app import ndb, settings
from app.core.misc import Image
from app.domain.acl import Domain, NamespaceDomain
from app.domain.sale import Company

from google.appengine.ext import blobstore

# done!
class CatalogImage(Image, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 36
    
    # ancestor DomainCatalog (namespace Domain)
    # composite index: ancestor:yes - sequence
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
     
     
    @classmethod
    def manage(cls, create, values, **kwds):
        
        ## this should be multiple upload thing, this needs work :@
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
            skip = ('image',)
            
            if values.get('upload_url') or not values.get('image'):
               response['upload_url'] = blobstore.create_upload_url(values.get('upload_url'), gs_bucket_name=settings.COMPANY_LOGO_BUCKET)
               return response
            
            new_image = 'image' in values
 
            response.process_input(values, cls, skip=skip, convert=[('catalog', Catalog, True)])
      
            if response.has_error():
               return response
       
            entity = cls.prepare(create, values, skip=skip)
            
            if entity is None:
               return response.not_found()
             
            if not create:
  
               if not entity.domain_is_active:
                  response.error('domain', 'not_active') 
               
               catalog = entity.parent().get()   
               if not catalog or not catalog.is_usable:
                  response.error('catalog', 'not_unpublished')
 
               if response.has_error():
                  return response
                
               if current.has_permission('update', entity):
                   
                   if new_image:
                      blobstore.delete(entity.image)
                      entity.image = values.get('image')
  
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
                
               response.process_input(values, cls)
               
               if response.has_error():
                  return response
               
               entity = cls.prepare(create, values, parent=values.get('catalog'))
 
               catalog = values.get('catalog')
               
               if not new_image:
                  response.required('image')
 
               if not catalog:
                  response.required('catalog')
             
               if response.has_error():
                  return response
  
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
    
    
    @classmethod
    def delete(cls, values, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
       
                  if current.has_permission('delete', entity):
                     
                     catalog = entity.parent().get()
                     
                     if not catalog or not catalog.is_usable:
                        response.error('catalog', 'not_unpublished')
                     
                     if response.has_error():
                        return response
                      
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

class Catalog(ndb.BaseExpando, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 35
    
    # root (namespace Domain)
    # https://support.google.com/merchants/answer/188494?hl=en&hlrm=en#other
    # composite index: ???
    company = ndb.SuperKeyProperty('1', kind='app.domain.sale.Company', required=True)
    name = ndb.SuperStringProperty('2', required=True)
    publish_date = ndb.SuperDateTimeProperty('3')# today
    discontinue_date = ndb.SuperDateTimeProperty('4')# +30 days
    updated = ndb.SuperDateTimeProperty('5', auto_now=True)
    created = ndb.SuperDateTimeProperty('6', auto_now_add=True)
    state = ndb.SuperIntegerProperty('7', required=True)
 
    # Expando
    # cover = blobstore.BlobKeyProperty('8', required=True)# blob ce se implementirati na GCS
    # cost = DecimalProperty('9', required=True)
    # Search improvements
    # product count per product category
    # rank coefficient based on store feedback
    
    EXPANDO_FIELDS = {
       'cover' :  ndb.SuperKeyProperty('8', kind=CatalogImage, required=True),# blob ce se implementirati na GCS
       'cost' : ndb.SuperDecimalProperty('9', required=True)
             
    }
  
    OBJECT_DEFAULT_STATE = 'unpublished'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'unpublished' : (1, ),
        'locked' : (2, ),
        'published' : (3, ),
        'discontinued' : (4, ),
    }
    
    # nedostaju akcije za dupliciranje catalog-a, za clean-up, etc...
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'lock' : 3,
       'publish' : 4,
       'discontinue' : 5,
       'log_message' : 6,
       'duplicate' : 7,
    }
    
    OBJECT_TRANSITIONS = {
        'lock' : {
            'from' : ('unpublished',),
            'to' : ('locked',),
         },
        'publish' : {
           'from' : ('locked', ),
           'to'   : ('published',),
        },
        'discontinue' : {
           'from' : ('locked', 'published', ),
           'to'   : ('discontinued',),
        },
    }
    
    @property
    def is_usable(self):
        return self.get_state == 'unpublished'

    @classmethod
    def duplicate(cls, values, **kwds):
        pass
    
    @classmethod
    def list(cls, values, **kwds):
        response = ndb.Response()
        response.process_input(values, cls, only=False, convert=[('domain', ndb.factory('app.domain.acl.Domain'))])
        if response.has_error():
           return response
        response['items'] = cls.query(namespace=values.get('domain').urlsafe()).fetch()
        return response
      

    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
            
            only = ('name',)
            response.process_input(values, cls, only=only, convert=[('company', Company, True)])
      
            if response.has_error():
               return response
  
            entity = cls.prepare(create, values, only=only)
            
            if entity is None:
               return response.not_found()
            
            if entity and entity.loaded():
       
               if not entity.domain_is_active:
                  response.error('domain', 'not_active') 
                  
               if not entity.is_usable:
                  response.error('catalog', 'not_unpublished')
                  
               if not entity.key.parent().is_usable:
                  response.error('company', 'not_open')
                   
               if response.has_error():
                  return response
                
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               
               company = values.get('company').get()
               
               entity = cls.prepare(create, values, only=('name', 'company'), namespace=company.key.namespace())
           
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
        except Exception as e:
            response.transaction_error(e)
            
        return response  
    
    
    @classmethod
    def log_message(cls, values, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)  
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
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
    
    # Ova akcija zakljucava unpublished catalog. Ovde cemo dalje opisati posledice zatvaranja...
    @classmethod
    def lock(cls, values, **kwds):
        """
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'publish-DomainCatalog'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        # radimo update catalog-a sa novim cover-om - ovde cemo verovatno raditi i presnimavanje entiteta iz store-a za koji je zakacen catalog, i svega ostalog sto je neophodno.
        catalog_cover = DomainCatalogImage.query(ancestor=catalog_key).order(DomainCatalogImage.sequence).fetch(1, keys_only=True)
        catalog.cover = catalog_cover
        catalog_key = catalog.put()
        object_log = ObjectLog(parent=catalog_key, agent=agent_key, action='update', state=catalog.state, log=catalog)
        object_log.put()
        # zakljucavamo catalog
        catalog.state = 'locked'
        catalog_key = catalog.put()
        object_log = ObjectLog(parent=catalog_key, agent=agent_key, action='lock', state=catalog.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
        """
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
                
               # check if user can do this
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
              
               current = ndb.get_current_user()
          
               if current.has_permission('lock', entity) or current.has_permission('sudo', entity):
                      
                      cover = CatalogImage.query(ancestor=entity.key).order(-CatalogImage.sequence).get(keys_only=True)
                      
                      if cover:
                         entity.cover = cover
                      
                      entity.new_action('lock', state='locked', message=values.get('message'), note=values.get('note'))
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
        
    # Ova akcija objavljuje locked catalog. Ovde cemo dalje opisati posledice zatvaranja...
    @classmethod
    def publish(cls, values, **kwds):
        """
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'publish-DomainCatalog'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'locked'.
        catalog.state = 'published'
        catalog_key = catalog.put()
        object_log = ObjectLog(parent=catalog_key, agent=agent_key, action='publish', state=catalog.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
        """
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
                
               # check if user can do this
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
              
               current = ndb.get_current_user()
          
               if current.has_permission('publish', entity) or current.has_permission('sudo', entity):
                      entity.publish_date = datetime.datetime.today()
                      entity.new_action('publish', state='published', message=values.get('message'), note=values.get('note'))
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
    
    # Ova akcija prekida objavljen catalog. Ovde cemo dalje opisati posledice zatvaranja...
    @classmethod
    def discontinue(cls, values, **kwds):
        """
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'discontinue-DomainCatalog',
        # ili agent koji ima globalnu dozvolu 'sudo-DomainCatalog'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'locked' ili catalog.state == 'published'.
        catalog.state = 'discontinued'
        catalog_key = catalog.put()
        object_log = ObjectLog(parent=catalog_key, agent=agent_key, action='discontinue', state=catalog.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()  
        """
         
        response = ndb.Response()
         
        @ndb.transactional(xg=True)
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
                
               # check if user can do this
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
              
               current = ndb.get_current_user()
          
               if current.has_permission('discontinue', entity) or current.has_permission('sudo', entity):
                      entity.new_action('discontinue', state='discontinued', message=values.get('message'), note=values.get('note'))
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
class CatalogPricetag(ndb.BaseModel, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 34
    
    # ancestor DomainCatalog (namespace Domain)
    product_template = ndb.SuperKeyProperty('1', kind='app.domain.product.Template', required=True, indexed=False)
    container_image = ndb.SuperKeyProperty('2', kind=CatalogImage, required=True, indexed=False)# blob ce se implementirati na GCS
    source_width = ndb.SuperFloatProperty('3', required=True, indexed=False)
    source_height = ndb.SuperFloatProperty('4', required=True, indexed=False)
    source_position_top = ndb.SuperFloatProperty('5', required=True, indexed=False)
    source_position_left = ndb.SuperFloatProperty('6', required=True, indexed=False)
    value = ndb.SuperStringProperty('7', required=True, indexed=False)# $ 19.99 - ovo se handla unutar transakcije kada se radi update na unit_price od ProductTemplate ili ProductInstance
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }

     
    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
            
            response.process_input(values, cls, convert=[('catalog', Catalog, True)])
      
            if response.has_error():
               return response
 
            entity = cls.preare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if entity and entity.loaded():
  
               if not entity.domain_is_active:
                  response.error('domain', 'not_active') 
               
               catalog = entity.parent().get()
               
               if not catalog or not catalog.is_usable:
                  response.error('catalog', 'not_unpublished')
               
                    
               if response.has_error():
                  return response
                
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
        
               catalog = values.get('catalog')
               
               response.process_input(values, cls)
      
               if not catalog:
                  response.required('catalog')
               
               if response.has_error():
                  return response
                   
               entity = cls.prepare(create, values, parent=catalog)
     
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
    
    
    @classmethod
    def delete(cls, values, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
       
                  if current.has_permission('delete', entity):
                      
                     catalog = entity.parent().get()
                     
                     if not catalog or not catalog.is_usable:
                        response.error('catalog', 'not_unpublished')
                        
                     if response.has_error():
                        return response
                      
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

    