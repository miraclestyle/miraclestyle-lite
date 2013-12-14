# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

# buyer is not fully done, collections are at 50%
 
class Address(ndb.BaseExpando, ndb.Workflow):
    
    KIND_ID = 9
    # ancestor User
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    country = ndb.SuperKeyProperty('2', kind='app.core.misc.Country', required=True, indexed=False)
    city = ndb.SuperStringProperty('3', required=True, indexed=False)
    postal_code = ndb.SuperStringProperty('4', required=True, indexed=False)
    street_address = ndb.SuperStringProperty('5', required=True, indexed=False)
    default_shipping = ndb.SuperBooleanProperty('6', default=True, indexed=False)
    default_billing = ndb.SuperBooleanProperty('7', default=True, indexed=False)
  
    _default_indexed = False
 
    EXPANDO_FIELDS = {
        'region' :  ndb.SuperKeyProperty('8', kind='app.core.misc.CountrySubdivision'),
        'street_address2' : ndb.SuperStringProperty('9'),
        'email' : ndb.SuperStringProperty('10'),
        'telephone' : ndb.SuperStringProperty('11'),
    }
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
 
    @classmethod
    def list(cls, values):
    
        response = ndb.Response()
        
        from app.core.acl import User
        
        response.process_input(values, cls, only=False, convert=[ndb.SuperKeyProperty('user', kind=User, required=True)])
        
        if response.has_error():
           return response
            
        parent = values.get('parent')
        
        if parent is None:
           parent = ndb.get_current_user().key
           
        response['items'] = cls.query(ancestor=parent).fetch()
        
        return response
     
    @classmethod
    def delete(cls, values, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  if entity.key.parent() == current.key:
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
        
        # if default_shipping is set to true, update all other buyer entities to default_shipping = False
        # if default_billing is set to true, update all other buyer entities to default_billing = False 
  
        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
            
            if current.is_guest:
               return response.not_logged_in()
    
            response.process_input(values, cls)
 
            if response.has_error():
               return response       
    
            entity = cls.prepare(create, values, parent=current.key)
            
            if entity is None:
               return response.not_found()
      
            if not create:
               # update
               if current.key == entity.key.parent():
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                  return response.not_authorized()
            else:
               # create
               entity.put()
               entity.new_action('create')
               entity.record_action()
               
            run = False
            if values.get('default_billing') or values.get('default_shipping'):
               run = True
               
            if run:
                  allbuyer = cls.query(ancestor=entity.key).fetch()
                  to_put = []
                  for a in allbuyer:
                      if a.key != entity.key:
                         if values.get('default_billing'):
                            a.default_billing = False
                         if values.get('default_shipping'):
                            a.default_shipping = False
                         to_put.append(a)
                         
                  ndb.put_multi(to_put)
               
            response.status(entity)
        
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response
    
            
# done!
class Collection(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 10
    
    # ancestor User
    # mozda bude trebao index na primary_email radi mogucnosti update-a kada user promeni primarnu email adresu na svom profilu
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    notify = ndb.SuperBooleanProperty('2', required=True, default=False)
    primary_email = ndb.SuperStringProperty('3', required=True, indexed=False)
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @classmethod
    def list(cls, values):
        response = ndb.Response()
        
        response['items'] = cls.query(ancestor=ndb.get_current_user().key).fetch()
        
        return response
 
    @classmethod
    def manage(cls, create, values, **kwds):
   
        response = ndb.Response()
        
        @ndb.transactional(xg=True)
        def transaction():
            
            current = ndb.get_current_user()
            
            if current.is_guest:
               return response.not_logged_in()
            
            response.process_input(values, cls, skip=('primary_email',))
             
            if not response.has_error():
 
                entity = cls.prepare(create, values, parent=current.key)
                
                # we internally set primary_email, not from user input    
                entity.primary_email = current.primary_email
                
                if entity is None:
                    return response.not_found()
        
                if not create:
    
                   if entity.key.parent() == current.key:
                       entity.put()
                       entity.new_action('update')
                       entity.record_action()
                       
                       response.status(entity)
                   else:
                       return response.not_authorized()
                   
                else:
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
                   
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
 

# done!
class CollectionCompany(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 11
    # ancestor User
    company = ndb.SuperKeyProperty('1', kind='app.domain.business.Company', required=True)
    collections = ndb.SuperKeyProperty('2', kind='app.core.buyer.Collection', repeated=True)# soft limit 500x
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @classmethod
    def delete(cls, values, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  if entity.key.parent() == current.key:
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
        
        @ndb.transactional
        def transaction():
            
            current = ndb.get_current_user()
            
            if current.is_guest:
               return response.not_logged_in()
           
            response.process_input(values, cls)
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
            
            collection_keys = values.get('collections')
            company_key = values.get('company')
  
            if entity is None:
               return response.not_found()
           
            entity.collections = []
                  
            for c in collection_keys:
                if c.parent() == current.key:
                     entity.collections.append(c)
            
            if not create:
               if entity.key.parent() == current.key:
                  entity.put()
                  entity.new_action('update')
                  entity.record_action()
               else:
                  return response.not_authorized()
            else:
                entity = cls(parent=current.key, collections=collection_keys, company=company_key)
                entity.put()
                entity.new_action('create')
                entity.record_action()
                
            # @todo izaziva se update AggregateBuyerCollectionCatalog preko task queue 
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response
  
    
# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class AggregateCollectionCatalog(ndb.BaseModel):
    
    KIND_ID = 12
    
    # ancestor User
    # not logged
    # task queue radi agregaciju prilikom nekih promena na store-u
    # mogao bi da se uvede index na collections radi filtera: AggregateBuyerCollectionCatalog.collections = 'collection', 
    # ovaj model bi se trebao ukinuti u korist MapReduce resenja, koje bi bilo superiornije od ovog
    # composite index: ancestor:yes - catalog_published_date:desc
    company = ndb.SuperKeyProperty('1', kind='app.domain.business.Company', required=True)
    collections = ndb.SuperKeyProperty('2', kind='app.core.buyer.Collection', repeated=True, indexed=False)# soft limit 500x
    catalog = ndb.SuperKeyProperty('3', kind='app.domain.marketing.Catalog', required=True, indexed=False)
    catalog_cover = ndb.SuperBlobKeyProperty('4', required=True, indexed=False)# blob ce se implementirati na GCS
    catalog_published_date = ndb.SuperDateTimeProperty('5', required=True)
