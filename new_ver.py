# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import decimal
from app import ndb

# ova klasa snima sve logove, napr: PayPal, IP adrese....
class Record(ndb.BaseExpando):
    
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
    
    # log entity's each property
    def log_entity(self, entity):
        for p in entity._properties:
            prop = entity._properties.get(p)
            v = prop._get_value(obj)
            if isinstance(v, decimal.Decimal):
               v = str(v)
            setattr(self, p, v)
            
        return self


      
class Engine:
  
  def run(self, context):
    
    records = []
    
    for entity in context.log_entities:
      record = Record(parent=entity.key, agent=context.user.key, action=context.action)
      record.log_entity(entity)
      records.append(record)
    
    if len(records):
      recorded = ndb.put_multi(records)
      context.log_entities = []
      
      
      