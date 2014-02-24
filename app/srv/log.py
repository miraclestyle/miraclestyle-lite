# -*- coding: utf-8 -*-
'''
Created on Dec 25, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb


class Context():
  
  def __init__(self):
    self.entities = []


class Record(ndb.BaseExpando):
  
  _kind = 5
  # High numbers for field aliases are provided in order not to conflict with logged object fields!
  logged = ndb.SuperDateTimeProperty('99', auto_now_add=True)
  agent = ndb.SuperKeyProperty('98', kind='0', required=True)
  action = ndb.SuperKeyProperty('97', kind='56', required=True)
  
  _expando_fields = {
                     'message' : ndb.SuperTextProperty('96'),
                     'note' : ndb.SuperTextProperty('95'),
                     }
  
  # Log entity's each property
  def log_entity(self, entity):
    for p in entity._properties:
      prop = entity._properties.get(p)
      value = prop._get_value(entity)
      prop._set_value(self, value)
    return self


class Engine:
  
  @classmethod
  def run(cls, context, transaction=False):
    
    def log(context):
      if len(context.log.entities):
        records = []
        for config in context.log.entities:
          entity = config[0]
          try:
            kwargs = config[1]
          except:
            kwargs = None
          
          if not kwargs:
            kwargs = {}
          
          log_entity = kwargs.pop('log_entity', True)
          record = Record(parent=entity.key, agent=context.auth.user.key, action=context.action.key, **kwargs)
          if log_entity is True:
            log_entity = entity
          if log_entity:
            record.log_entity(log_entity)
          records.append(record)
          
        if len(records):
          recorded = ndb.put_multi(records)
          context.log.entities = []
    
    if (transaction):
      ndb.transaction(lambda: log(context))
    else:
      log(context)
