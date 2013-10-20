# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
 
class ObjectLog(ndb.BaseExpando):
    
    KIND = 5
    
    logged = ndb.SuperDateTimeProperty('1', auto_now_add=True)
    agent = ndb.SuperKeyProperty('2', kind='core.acl.User', required=True)
    action = ndb.SuperIntegerProperty('3', required=True)
    state = ndb.SuperIntegerProperty('4', required=True) # verovatno ide u expando
    
    _default_indexed = False
    
    EXPANDO_FIELDS = {
       'message' : ndb.TextProperty('5'),
       'note' : ndb.TextProperty('6'),
       'log' : ndb.PickleProperty('7')
    }
    
class PayPalTransactionLog(ndb.Expando):
    
    # ancestor Order, BillingOrder
    # not logged
    # ako budemo radili analizu sa pojedinacnih ordera onda nam treba composite index: ancestor:yes - logged:desc
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    txn_id = ndb.StringProperty('2', required=True)
    
    _default_indexed = False
 
    # Expando
    # ipn_message = ndb.TextProperty('3', required=True)
  
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
    }
    
    

# done!
class BillingLog(ndb.Model):
    
    # root (namespace Domain) / ancestor Domain ?
    # key za BillingLog ce se graditi na sledeci nacin:
    # key: namespace=domain.key, id=str(reference_key) ili mozda neki drugi destiled id iz key-a
    # idempotency je moguc ako se pre inserta proverava da li postoji record sa id-jem reference_key
    # not logged
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    amount = ndb.DecimalProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    balance = ndb.DecimalProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query