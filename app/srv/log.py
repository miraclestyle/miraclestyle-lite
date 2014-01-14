# -*- coding: utf-8 -*-
'''
Created on Dec 25, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

class Context():
  
  def __init__(self):
    self.entities = []
 
# ova klasa snima sve logove, napr: PayPal, IP adrese....
class Record(ndb.BaseExpando):
    
    KIND_ID = 5
    
    # high numbers for field aliases here to not conflict with logged object
    
    logged = ndb.SuperDateTimeProperty('99', auto_now_add=True)
    agent = ndb.SuperKeyProperty('98', kind='app.srv.auth.User', required=True)
    action = ndb.SuperKeyProperty('97', kind='app.srv.event.Action', required=True)
  
    _default_indexed = False
 
    _expando_fields = {
       'message' : ndb.SuperTextProperty('96'),
       'note' : ndb.SuperTextProperty('95'),
    }
    
    # log entity's each property
    def log_entity(self, entity):
        for p in entity._properties:
            prop = entity._properties.get(p)
            value = prop._get_value(entity)
            self._properties[prop._name] = prop
            setattr(self, p, value)
        return self


      
class Engine:
  
  @classmethod
  def run(cls, context):
    
    if len(context.log.entities):
      
      records = []
      
      for entity, kwargs in context.log.entities:
        
        if not kwargs:
           kwargs = {}
           
        log_entity = kwargs.pop('log_entity', True)
        record = Record(parent=entity.key, agent=context.auth.user.key, action=context.event.key, **kwargs)
        if log_entity is True:
           log_entity = entity
           
        if log_entity:
           record.log_entity(log_entity)
        records.append(record)
      
      if len(records):
        recorded = ndb.put_multi(records)
        context.log.entities = []