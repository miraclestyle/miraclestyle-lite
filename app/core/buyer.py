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
 
    # Expando
    # naredna dva polja su required!!!
    # region = ndb.KeyProperty('8', kind=CountrySubdivision, required=True)# ako je potreban string val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje 
    # region = ndb.StringProperty('8', required=True)# ako je potreban key val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje
    # street_address2 = ndb.StringProperty('9') # ovo polje verovatno ne treba, s obzirom da je u street_address dozvoljeno 500 karaktera 
    # email = ndb.StringProperty('10')
    # telephone = ndb.StringProperty('11')
 
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @classmethod
    def list(cls, parent=None):
        response = ndb.Response()
        if parent is None:
           from app import core
           parent = core.acl.User.current_user().key
        response['items'] = cls.query(ancestor=parent).fetch()
        
        return response
    
    @classmethod
    def delete(cls, **k):
        ids = k.get('id')
        
        response = ndb.Response()
        
        from app import core
        
        current = core.acl.User.current_user()
        
        to_delete = []
        for i in ids:
            try:
              key = ndb.Key(urlsafe=i)
            except:
              continue
            
            if key:
               if key.parent() == current.key:
                  to_delete.append(key)
                  
        if len(to_delete):
           to_delete = ndb.delete_multi(to_delete)
            
        response['deleted'] = to_delete
           
        return response
               
  
    @classmethod
    def manage_entity(cls, **kwds):
         
        response = ndb.Response()
 
        from app import core
        
        current = core.acl.User.current_user()
        
        if current.is_guest:
           return response.not_logged_in()
       
        kwds['default_billing'] = bool(int(kwds['default_billing']))
        kwds['default_shipping'] = bool(int(kwds['default_shipping']))
        
        try:
           country_key = ndb.Key(urlsafe=kwds['country'])
           if not country_key.get():
              raise Exception('invalid_input')
           kwds['country'] = country_key
        except:
           response.error('country', 'invalid_input')
           
        if kwds['region']:
           try:
               region_key = ndb.Key(urlsafe=kwds['region'])
               if not region_key:
                  raise Exception('invalid_input')
               kwds['region'] = region_key
           except:
               response.error('region', 'invalid_input')
               
        required = ('name', 'city', 'postal_code', 'street_address')
        for req in required:
            if not kwds[req]:
               response.error(req, 'required')
                
        if response.has_error():
           return response       
    
        entity = cls.load_from_values(kwds, get=True)
        
        @ndb.transactional(xg=True)
        def transaction():
            if entity and entity.key:
               # update
               entity.put()
               entity.new_action('update')
               entity.record_action()
            else:
               # create
               entity.parent = current.key
               entity.put()
               entity.new_action('create')
               entity.record_action()
               
            return entity
        
        response['item'] = transaction()
        return response
            
# done!
class Collection(ndb.BaseModel):
    
    KIND_ID = 10
    
    # ancestor User
    # mozda bude trebao index na primary_email radi mogucnosti update-a kada user promeni primarnu email adresu na svom profilu
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    notify = ndb.SuperBooleanProperty('2', default=False)
    primary_email = ndb.SuperStringProperty('3', required=True, indexed=False)
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
 

# done!
class CollectionStore(ndb.BaseModel):
    
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
