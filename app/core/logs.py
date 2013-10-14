# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.core import user

class ObjectLog(ndb.BaseExpando):
    
    logged = ndb.SuperDateTimeProperty('1', auto_now_add=True)
    agent = ndb.SuperKeyProperty('2', kind=user.User, required=True)
    action = ndb.SuperIntegerProperty('3', required=True)
    state = ndb.SuperIntegerProperty('4', required=True) # verovatno ide u expando
    
    _default_indexed = False
    
    EXPANDO_FIELDS = {
       'message' : ndb.TextProperty('5'),
       'note' : ndb.TextProperty('6'),
       'log' : ndb.PickleProperty('7')
    }
 