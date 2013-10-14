# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app import core
from app.pyson import Eval 

class Domain(ndb.BaseExpando):
    
    # root
    # composite index: ancestor:no - state,name
    name = ndb.StringProperty('1', required=True)
    primary_contact = ndb.KeyProperty('2', kind=core.user.User, required=True, indexed=False)
    updated = ndb.DateTimeProperty('3', auto_now=True, required=True)
    created = ndb.DateTimeProperty('4', auto_now_add=True, required=True)
    state = ndb.IntegerProperty('5', required=True)
    
    _default_indexed = False
  
    KIND = 0
    
    OBJECT_DEFAULT_STATE = 'active'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'active' : (1, ),
        'suspended' : (2, ),
        'su_suspended' : (3, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'suspend' : 3,
       'activate' : 4,
       'sudo' : 5,
       'log_message' : 6,
    }
    
    OBJECT_TRANSITIONS = {
        'activate' : {
            'from' : ('suspended',),
            'to' : ('active',),
         },
        'suspend' : {
           'from' : ('active', ),
           'to'   : ('suspended',),
        },
        'su_activate' : {
            'from' : ('su_suspended', 'suspended',),
            'to' : ('active',),
         },
        'su_suspend' : {
           'from' : ('active', 'suspended',),
           'to'   : ('su_suspended',),
        },
    }
    