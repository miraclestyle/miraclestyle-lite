# -*- coding: utf-8 -*-
'''
Created on Apr 17, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import taskqueue

from app import ndb


def execute(context):
  queues = {}
  url = '/task/io_engine_run'
  if context.callback.transactional is None:
    context.callback.transactional = ndb.in_transaction()
  if context.callback.transactional:
    context.callback.payloads = context.callback.payloads[:5]
  if len(context.callback.payloads):
    for payload in context.callback.payloads:
      queue_name, data = payload
      if data['caller_entity'].key:
        data['caller_entity'] = data['caller_entity'].key.urlsafe()
      if context.user.key:
        data['caller_user'] = context.user.key.urlsafe()
      data['caller_action'] = context.action.key.urlsafe()
      try:
        kwargs = payload[2]
      except IndexError as e:
        kwargs = {}
      if queue_name not in queues:
        queues[queue_name] = []
      queues[queue_name].append(taskqueue.Task(url=url, payload=json.dumps(data), **kwargs))
  if len(queues):
    for queue_name, tasks in queues.items():
      queue = taskqueue.Queue(name=queue_name)
      queue.add(tasks, transactional=context.callback.transactional)
  context.callback.payloads = []


class Prepare(event.Plugin):
  
  queue_name = ndb.SuperStringProperty('4', required=True, indexed=False)
  transactional = ndb.SuperBooleanProperty('5', required=True, indexed=False, default=True)
  action_key = ndb.SuperStringProperty('6', required=True, indexed=False)
  action_model = ndb.SuperStringProperty('7', required=True, indexed=False)
  
  def run(self, context):
    if not context.callback.payloads:
      context.callback.payloads = []
    context.callback.transactional = self.transactional
    if context.entity:
      context.callback.payloads.append((self.queue_name,
                                        {'action_key': self.action_key,
                                         'action_model': self.action_model,
                                         'caller_entity': context.entity}))
