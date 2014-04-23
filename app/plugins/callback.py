# -*- coding: utf-8 -*-
'''
Created on Apr 17, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import taskqueue

from app import ndb


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
      if context.user.key:
        data['caller_user'] = context.user.key.urlsafe()
      data['caller_action'] = context.action.key.urlsafe()
      data['action_model'] = payload.action_model
      data['action_key'] = payload.action_key
      kwargs = payload.kwargs
      if payload.queue not in queues:
        queues[payload.queue] = []
      queues[payload.queue].append(taskqueue.Task(url=url, payload=json.dumps(data), **kwargs))
  if len(queues):
    for queue_name, tasks in queues.items():
      queue = taskqueue.Queue(name=queue_name)
      queue.add(tasks, transactional=transactional)


class Payload(event.Plugin):  # @todo Properties need optimization!
  
  transactional = ndb.SuperBooleanProperty('4', indexed=False, required=True, default=True)
  queue = ndb.SuperStringProperty('5', indexed=False, required=True)
  action_model = ndb.SuperStringProperty('6', indexed=False, required=True)
  action_key = ndb.SuperStringProperty('7', indexed=False, required=True)
  kwargs = ndb.SuperPickleProperty('8', indexed=False, required=True, default={}, compressed=False)
  
  def run(self, context):
    execute(context, self, self.transactional)
