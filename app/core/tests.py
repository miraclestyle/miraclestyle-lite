# -*- coding: utf-8 -*-
'''
Created on Oct 13, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.pyson import Eval 

class TestModel(ndb.BaseModel, ndb.Workflow):
    
    OBJECT_DEFAULT_STATE = 'active'
    
    OBJECT_STATES = {
        'active' : (1, ),
        'suspended' : (2, ),
    }
    
    OBJECT_ACTIONS = {
       'activate' : 1,
       'suspend'  : 2,
       'register' : 3,
    }
    
    OBJECT_TRANSITIONS = {
                          
        'activate' : {
             # from where to where this transition can be accomplished?
            'from' : ('suspended',),
            'to' : ('activate',),
         },
   
    }      
    
    name = ndb.SuperStringProperty(writable=Eval('name') != 'Foo')
    state = ndb.SuperIntegerProperty()
    sp = ndb.SuperStringProperty()