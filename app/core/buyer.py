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
        'region' :  ndb.SuperKeyProperty('8', kind='app.core.misc.CountrySubdivision', required=True),
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
    def manage(cls, **kwds):
         
        response = ndb.Response()
 
        from app import core
        
        current = core.acl.User.current_user()
        
        if current.is_guest:
           return response.error('user', 'user_is_guest')
        
        new_data = cls.from_multiple_values(kwds)
        
        to_put_multi = [] # puts multiple entities
        items = [] # prepares items for output
        to_create = [] # items to be newly created
        to_update = {} # items that need update
        
        i = -1
        for new in new_data:
            i += 1
            country = new.get('country')
            try:
               new['country'] = ndb.Key(urlsafe=country)
            except:
               response.error('input_error_%s' % i, 'invalid_country_input')

                   
            region = new.get('region')
            if region and len(region):
               try:
                   new['region'] = ndb.Key(urlsafe=region)
               except:
                   response.error('input_error_%s' % i, 'invalid_region_input')
         
                   
            if response.has_error('input_error_%s' % i):
               continue
               
            new['default_billing'] = bool(int(new['default_billing']))
            new['default_shipping'] = bool(int(new['default_shipping']))
            
            create = False
            key_urlsafe = new.pop('id')
            
            try:
               key = ndb.Key(urlsafe=key_urlsafe)
            except:
               create = True
            
            if create:
               # do not provide expando fields if they are empty
               for delete in ['telephone', 'email', 'street_address2', 'region']:    
                    if delete in new and not new.get(delete):
                       del new[delete]
               new['parent'] = current.key        
               to_create.append(cls(**new))
            else:
               to_update[key.urlsafe()] = new
        
        if len(to_update):
           entries = ndb.get_multi([ndb.Key(urlsafe=k) for k,v in to_update.items()])
           for ent in entries:
                # if entity is not found or its not owned by the current user, skip any manipulations to it
                if not ent or ent.key.parent() != current.key:
                   continue
                ent.populate(**to_update[ent.key.urlsafe()])
                items.append(ent)
                log = ent.new_action('update', agent=current.key, log_object=ent)
                to_put_multi.append(ent)
                to_put_multi.append(log)
               
        if len(to_create):
           # commit all creations in serial operation, however we can put here multi put because,
           # logs dont need to be displayed right away - consistency wise?
           @ndb.transactional(xg=True)
           def transaction(s, current):
               s.put()
               items.append(s)
               log = s.new_action('create', agent=current.key, log_object=s)
               log.put()
               
           for s in to_create:
               transaction(s, current)
               
        if len(to_put_multi):
           response['put_multi'] = ndb.put_multi(to_put_multi)
           
        response['items'] = items
        
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
