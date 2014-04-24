# -*- coding: utf-8 -*-
'''
Created on Apr 17, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import taskqueue

from app import ndb
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


class Payload(event.Plugin):
  
  queue = ndb.SuperStringProperty('5', indexed=False, required=True)
  payload_data = ndb.SuperJsonProperty('6', indexed=False, required=True, default={})
  
  def run(self, context):
    data = {}
    for key, value in self.payload_data.items():
      data[key] = get_attr(context, value)
    context.callback_payloads.append((self.queue, data))


class Exec(event.Plugin):
  
  static_data = ndb.SuperJsonProperty('5', indexed=False, required=True, default={})
  dynamic_data = ndb.SuperJsonProperty('6', indexed=False, required=True,
                                       default={'caller_user': 'context.user.key_urlsafe',
                                                'caller_action': 'context.action.key_urlsafe'})
  
  def run(self, context):
    queues = {}
    url = '/task/io_engine_run'
    if self.transactional:
      context.callback_payloads = context.callback_payloads[:5]
    if len(context.callback_payloads):
      for payload in context.callback_payloads:
        data = {}
        queue_name, payload_data = payload
        data.update(self.static_data)
        for key, value in self.dynamic_data.items():
          data[key] = get_attr(context, value)
        data.update(payload_data)
        if queue_name not in queues:
          queues[queue_name] = []
        queues[queue_name].append(taskqueue.Task(url=url, payload=json.dumps(data)))
    if len(queues):
      for queue_name, tasks in queues.items():
        queue = taskqueue.Queue(name=queue_name)
        queue.add(tasks, transactional=self.transactional)
    context.callback_payloads = []
