# -*- coding: utf-8 -*-
'''
Created on Apr 17, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import taskqueue

from app import ndb, memcache, util
from app.lib.attribute_manipulator import set_attr, get_attr


class Notify(ndb.BaseModel):
  
  dynamic_data = ndb.SuperJsonProperty('1', required=True, indexed=False, default={})
  
  def run(self, context):
    data = {}
    data.update({'action_id': 'initiate', 'action_model': '61'})
    data['caller_entity'] = context.entities[context.model.get_kind()].key_urlsafe
    for key, value in self.dynamic_data.items():
      data[key] = get_attr(context, value)
    context.callback_payloads.append(('notify', data))


class Payload(ndb.BaseModel):
  
  queue = ndb.SuperStringProperty('1', required=True, indexed=False)
  static_data = ndb.SuperJsonProperty('2', required=True, indexed=False, default={})
  dynamic_data = ndb.SuperJsonProperty('3', required=True, indexed=False, default={})
  
  def run(self, context):
    data = {}
    data.update(self.static_data)
    for key, value in self.dynamic_data.items():
      data[key] = get_attr(context, value)
    context.callback_payloads.append((self.queue, data))


class Exec(ndb.BaseModel):
  
  static_data = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  dynamic_data = ndb.SuperJsonProperty('2', indexed=False, required=True, default={})
  
  def run(self, context):
    queues = {}
    url = '/task/io_engine_run'
    if ndb.in_transaction():
      context.callback_payloads = context.callback_payloads[:5]
    if len(context.callback_payloads):
      for payload in context.callback_payloads:
        data = {}
        queue_name, payload_data = payload
        data.update(self.static_data)
        for key, value in self.dynamic_data.items():
          data[key] = get_attr(context, value)
        data.update(payload_data)
        if data.get('caller_user') == None:
          data['caller_user'] = get_attr(context, 'user.key_urlsafe')
        if data.get('caller_action') == None:
          data['caller_action'] = get_attr(context, 'action.key_urlsafe')
        if queue_name not in queues:
          queues[queue_name] = []
        queues[queue_name].append(taskqueue.Task(url=url, payload=json.dumps(data)))
    if len(queues):
      for queue_name, tasks in queues.items():
        queue = taskqueue.Queue(name=queue_name)
        queue.add(tasks, transactional=ndb.in_transaction())
    context.callback_payloads = []
