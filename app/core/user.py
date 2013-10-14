# -*- coding: utf-8 -*-
'''
Created on Oct 11, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.pyson import Eval
 
     
class Identity(ndb.BaseModel):
    
    # StructuredProperty model
    identity = ndb.StringProperty('1', required=True)# spojen je i provider name sa id-jem
    email = ndb.StringProperty('2', required=True)
    associated = ndb.BooleanProperty('3', default=True)
    primary = ndb.BooleanProperty('4', default=True)
          
          
class User(ndb.BaseExpando):
    
    identities = ndb.StructuredProperty(Identity, '1', repeated=True)# soft limit 100x
    emails = ndb.SuperStringProperty('2', repeated=True)# soft limit 100x
    state = ndb.SuperIntegerProperty('3', required=True)
    
    _default_indexed = False
 
    #Expando
    EXPANDO_FIELDS = {
      'roles' : ndb.KeyProperty('4', kind='DomainRole', repeated=True)                 
    }
    
    KIND_ID = 0
    
    OBJECT_DEFAULT_STATE = 'su_active'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'su_active' : (1, ),
        'su_suspended' : (2, ),
    }
    
    OBJECT_ACTIONS = {
       'register' : 1,
       'update' : 2,
       'login' : 3,
       'logout' : 4,
       'sudo' : 5,
    }
    
    OBJECT_TRANSITIONS = {
        'su_activate' : {
             # from where to where this transition can be accomplished?
            'from' : ('su_suspended',),
            'to' : ('su_active',),
         },
        'su_suspend' : {
           'from' : ('su_active', ),
           'to'   : ('su_suspended',),
        },
    }   
      
class IPAddress(ndb.BaseModel):
    
    # ancestor User
    # not logged
    # ako budemo radili per user istragu loga onda nam treba composite index: ancestor:yes - logged:desc
    logged = ndb.SuperDateTimeProperty('1', auto_now_add=True, required=True)
    ip_address = ndb.SuperStringProperty('2', required=True, indexed=False)    
    