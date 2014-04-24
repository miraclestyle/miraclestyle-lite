# -*- coding: utf-8 -*-
'''
Created on Apr 17, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import taskqueue

from app import ndb
from app.srv import event

def prepare_attr(entity, field_path):
  fields = field_path.split('.')
  last_field = fields[-1]
  drill = fields[:-1]
  i = -1
  while not last_field:
    i = i - 1
    last_field = fields[i]
    drill = fields[:i]
  for field in drill:
    if field:
      if isinstance(entity, dict):
        try:
          entity = entity[field]
        except KeyError as e:
          return None
      elif isinstance(entity, list):
        try:
          entity = entity[int(field)]
        except KeyError as e:
          return None
      else:
        try:
          entity = getattr(entity, field)
        except ValueError as e:
          return None
  return (entity, last_field)

def set_attr(entity, field_path, value):
  entity, last_field = prepare_attr(entity, field_path)
  if isinstance(entity, dict):
    entity[last_field] = value
  elif isinstance(entity, list):
    entity.insert(int(last_field), value)
  else:
    setattr(entity, last_field, value)

def get_attr(entity, field_path):
  entity, last_field = prepare_attr(entity, field_path)
  if isinstance(entity, dict):
    return entity.get(last_field)
  elif isinstance(entity, list):
    return entity[int(last_field)]
  else:
    return getattr(entity, last_field)

def execute(context, payloads, transactional=None):
  queues = {}
  url = '/task/io_engine_run'
  if not isinstance(payloads, (list, tuple)):
    payloads = [payloads]
  if transactional is None:
    transactional = ndb.in_transaction()
  if transactional:
    payloads = payloads[:5]
  if len(payloads):
    for payload in payloads:
      data = {}
      data.update(payload.internal_fields)
      for key, value in payload.external_fields.items():
        data[key] = get_attr(context, value)
      if payload.queue not in queues:
        queues[payload.queue] = []
      queues[payload.queue].append(taskqueue.Task(url=url, payload=json.dumps(data)))
  if len(queues):
    for queue_name, tasks in queues.items():
      queue = taskqueue.Queue(name=queue_name)
      queue.add(tasks, transactional=transactional)


class Payload(event.Plugin):
  
  transactional = ndb.SuperBooleanProperty('4', indexed=False, required=True, default=True)
  queue = ndb.SuperStringProperty('5', indexed=False, required=True)
  internal_fields = ndb.SuperJsonProperty('6', indexed=False, required=False, default={})  # @todo Not sure if this is the best way to store repeated key/value data pairs?
  external_fields = ndb.SuperJsonProperty('7', indexed=False, required=False, default={})  # @todo Not sure if this is the best way to store repeated key/value data pairs?
  
  def run(self, context):
    execute(context, self, self.transactional)
