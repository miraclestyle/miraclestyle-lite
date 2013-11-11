# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
 
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
    def logs(cls, **kwds):
        response = ndb.Response()
        from app.core.log import ObjectLog
        response['items'] = ObjectLog.query(ancestor=ndb.Key(urlsafe=kwds.get('key'))).fetch()
        return response
    
    @classmethod
    def list(cls, parent=None, **kwds):
        
        response = ndb.Response()
        if parent is None:
           parent = cls.get_current_user().key
        response['items'] = cls.query(ancestor=parent).fetch()
        
        return response
     
  
    @classmethod
    def manage(cls, **kwds):
         
        response = ndb.Response()
  
        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
            
            if current.is_guest:
               return response.not_logged_in()
    
            response.validate_input(kwds, cls)
    
            if response.has_error():
               return response       
    
            entity = cls.get_or_prepare(kwds, parent=current.key)
      
            if entity and entity.loaded():
               # update
               entity.put()
               entity.new_action('update')
               entity.record_action()
            else:
               # create
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
    def delete(cls, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds)
               
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
    def list(cls, **kwds):
        response = ndb.Response()
        
        response['items'] = cls.query(ancestor=cls.get_current_user().key).fetch()
        
        return response
 
    @classmethod
    def manage(cls, **kwds):
   
        response = ndb.Response()
        
        @ndb.transactional(xg=True)
        def transaction():
            
            current = cls.get_current_user()
            
            if current.is_guest:
               return response.not_logged_in()
            
            response.validate_input(kwds, cls, skip=('primary_email',))
             
            if not response.has_error():
 
                entity = cls.get_or_prepare(kwds, parent=current.key)
                
                # we internally set primary_email, not from user input    
                entity.primary_email = current.primary_email
        
                if entity and entity.loaded():
    
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
    def delete(cls, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds)
               
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
 

# done!
class CollectionStore(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 11
    # ancestor User
    store = ndb.SuperKeyProperty('1', kind='app.domain.sale.Store', required=True)
    collections = ndb.SuperKeyProperty('2', kind='app.core.buyer.Collection', repeated=True)# soft limit 500x
   
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
               
               entity = cls.get_or_prepare(kwds)
               
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
    def manage(cls, **kwds):
        
        response = ndb.Response()
        
        @ndb.transactional
        def transaction():
            
            current = cls.get_current_user()
            
            if current.is_guest:
               return response.not_logged_in()
           
            response.validate_input(kwds, cls)
            
            if response.has_error():
               return response
            
            entity = cls.get_or_prepare(kwds)
            
            collection_keys = kwds.get('collections')
            store_key = kwds.get('store')
  
            if entity is None:
               return response.not_found()
            
            if entity.loaded():
               if entity.parent() == current.key:
                  entity.collections = []
                  
                  for c in collection_keys:
                      if c.parent() == current.key:
                         entity.collections.append(c)
                  entity.put()
                  entity.new_action('update')
                  entity.record_action()
               else:
                  return response.not_authorized()
            else:
                entity = cls(parent=current.key, collections=collection_keys, store=store_key)
                entity.put()
                entity.new_action('create')
                entity.record_action()
                
            # @todo izaziva se update AggregateBuyerCollectionCatalog preko task queue 
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response
    """
       
    # Dodaje novi store u korisnikovoj listi i odredjuje clanstvo u korisnikovim kolekcijama
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo registrovani autenticirani agent.
        buyer_collection_store = BuyerCollectionStore(parent=user_key, store=var_store, collections=var_collections)
        buyer_collection_store_key = buyer_collection_store.put()
        object_log = ObjectLog(parent=buyer_collection_store_key, agent=user_key, action='create', state='none', log=buyer_collection_store)
        object_log.put()
        # izaziva se update AggregateBuyerCollectionCatalog preko task queue
    
    # Menja clanstvo store u korisnikovim kolekcijama
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (buyer_collection_store.parent == agent).
        buyer_collection_store.collections = var_collections
        buyer_collection_store_key = buyer_collection_store.put()
        object_log = ObjectLog(parent=buyer_collection_store_key, agent=user_key, action='update', state='none', log=buyer_collection_store)
        object_log.put()
        # izaziva se update AggregateBuyerCollectionCatalog preko task queue
    
    # Brise store iz korisnikove liste
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (buyer_collection_store.parent == agent).
        object_log = ObjectLog(parent=buyer_collection_store_key, agent=user_key, action='delete', state='none')
        object_log.put()
        buyer_collection_store_key.delete()
        # izaziva se update AggregateBuyerCollectionCatalog preko task queue
        # ndb.delete_multi(AggregateBuyerCollectionCatalog.query(AggregateBuyerCollectionCatalog.store == buyer_collection_store.store, ancestor=user_key).fetch(keys_only=True))

    """
    
# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class AggregateCollectionCatalog(ndb.BaseModel):
    
    KIND_ID = 12
    
    # ancestor User
    # not logged
    # task queue radi agregaciju prilikom nekih promena na store-u
    # mogao bi da se uvede index na collections radi filtera: AggregateBuyerCollectionCatalog.collections = 'collection', 
    # ovaj model bi se trebao ukinuti u korist MapReduce resenja, koje bi bilo superiornije od ovog
    # composite index: ancestor:yes - catalog_published_date:desc
    store = ndb.SuperKeyProperty('1', kind='app.domain.sale.Store', required=True)
    collections = ndb.SuperKeyProperty('2', kind='app.core.buyer.Collection', repeated=True, indexed=False)# soft limit 500x
    catalog = ndb.SuperKeyProperty('3', kind='app.domain.marketing.Catalog', required=True, indexed=False)
    catalog_cover = ndb.SuperBlobKeyProperty('4', required=True, indexed=False)# blob ce se implementirati na GCS
    catalog_published_date = ndb.SuperDateTimeProperty('5', required=True)
