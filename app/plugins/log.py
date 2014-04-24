# -*- coding: utf-8 -*-
'''
Created on Apr 17, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings
from app.srv import event
from app.srv.log import Record


def write(context):
  """We always call log.write() from within a transaction, 
  because it is a helper function, not an independent function!
  
  """
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


class Write(event.Plugin):
  
  log_entity = ndb.SuperBooleanProperty('4', required=True, indexed=False, default=True)
  arguments = ndb.SuperStringProperty('5', repeated=True, indexed=False)
  
  def run(self, context):
    if not context.log.entities:
      context.log.entities = []
    if context.entity:
      arguments = {}
      if self.log_entity:
        arguments['log_entity'] = True
      else:
        arguments['log_entity'] = False
      if len(self.arguments):
        for argument in self.arguments:
          if context.entity._field_permissions['_records'][argument]['writable']:
            arguments[argument] = context.input.get(argument)
      context.log.entities.append((context.entity, arguments))
