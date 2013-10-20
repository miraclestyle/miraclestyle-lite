# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

class Address(ndb.BaseExpando):
    
    # ancestor User
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    country = ndb.KeyProperty('2', kind='core.misc.Country', required=True, indexed=False)
    city = ndb.StringProperty('3', required=True, indexed=False)
    postal_code = ndb.StringProperty('4', required=True, indexed=False)
    street_address = ndb.StringProperty('5', required=True, indexed=False)
    default_shipping = ndb.BooleanProperty('6', default=True, indexed=False)
    default_billing = ndb.BooleanProperty('7', default=True, indexed=False)
    
    _default_indexed = False
 
    EXPANDO_FIELDS = {
        'region' :  ndb.KeyProperty('8', kind='core.misc.CountrySubdivision', required=True),
        'street_address2' : ndb.StringProperty('9'),
        'email' : ndb.StringProperty('10'),
        'telephone' : ndb.StringProperty('11'),
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
 
# done!
class Collection(ndb.BaseModel):
    
    # ancestor User
    # mozda bude trebao index na primary_email radi mogucnosti update-a kada user promeni primarnu email adresu na svom profilu
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    notify = ndb.BooleanProperty('2', default=False)
    primary_email = ndb.StringProperty('3', required=True, indexed=False)
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
 

# done!
class CollectionStore(ndb.BaseModel):
    
    # ancestor User
    store = ndb.KeyProperty('1', kind='domain.sale.Store', required=True)
    collections = ndb.KeyProperty('2', kind='core.buyer.Collection', repeated=True)# soft limit 500x
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
 
    
# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class AggregateCollectionCatalog(ndb.BaseModel):
    
    # ancestor User
    # not logged
    # task queue radi agregaciju prilikom nekih promena na store-u
    # mogao bi da se uvede index na collections radi filtera: AggregateBuyerCollectionCatalog.collections = 'collection', 
    # ovaj model bi se trebao ukinuti u korist MapReduce resenja, koje bi bilo superiornije od ovog
    # composite index: ancestor:yes - catalog_published_date:desc
    store = ndb.KeyProperty('1', kind='domain.sale.Store', required=True)
    collections = ndb.KeyProperty('2', kind='core.buyer.Collection', repeated=True, indexed=False)# soft limit 500x
    catalog = ndb.KeyProperty('3', kind='domain.marketing.Catalog', required=True, indexed=False)
    catalog_cover = ndb.BlobKeyProperty('4', required=True, indexed=False)# blob ce se implementirati na GCS
    catalog_published_date = ndb.DateTimeProperty('5', required=True)
