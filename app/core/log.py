# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
 
class ObjectLog(ndb.BaseExpando):
    
    KIND_ID = 5
    
    # high numbers for field aliases here to not conflict with logged object
    
    logged = ndb.SuperDateTimeProperty('99', auto_now_add=True)
    agent = ndb.SuperKeyProperty('98', kind='app.core.acl.User', required=True)
    action = ndb.SuperIntegerProperty('97', required=True)
 
    _default_indexed = False
 
    EXPANDO_FIELDS = {
       'message' : ndb.SuperTextProperty('96'),
       'note' : ndb.SuperTextProperty('95'),
    }
    
    # log object's each property
    def log_object(self, obj):
        for p in obj._properties:
            prop = obj._properties.get(p)
            setattr(self, p, prop._get_value(obj))
            
        return self
    
class PayPalTransactionLog(ndb.BaseExpando, ndb.Workflow):
    
    KIND_ID = 25
    
    # ancestor Order, BillingOrder
    # not logged
    # ako budemo radili analizu sa pojedinacnih ordera onda nam treba composite index: ancestor:yes - logged:desc
    logged = ndb.SuperDateTimeProperty('1', auto_now_add=True)
    txn_id = ndb.SuperStringProperty('2', required=True)
    
    _default_indexed = False
 
    # Expando
    # ipn_message = ndb.TextProperty('3', required=True)
  
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
    }
    
    

# done!
class BillingLog(ndb.Model):
    
    KIND_ID = 26
    
    # root (namespace Domain) / ancestor Domain ?
    # key za BillingLog ce se graditi na sledeci nacin:
    # key: namespace=domain.key, id=str(reference_key) ili mozda neki drugi destiled id iz key-a
    # idempotency je moguc ako se pre inserta proverava da li postoji record sa id-jem reference_key
    # not logged
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    amount = ndb.SuperDecimalProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    balance = ndb.SuperDecimalProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query