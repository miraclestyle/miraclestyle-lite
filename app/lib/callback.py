# -*- coding: utf-8 -*-
'''
Created on Jun 18, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import taskqueue


def callback(url, callbacks, caller_user=None, caller_action=None, transactional=True):
  queues = {}
  if transactional:
    callbacks = callbacks[:5]
  if len(callbacks):
    for callback in callbacks:
      data = {}
      queue_name, static_data, dynamic_data = callback
      data.update(static_data)
      for key, value in dynamic_data.items():
        data[key] = get_attr(context, value)
      if data.get('caller_user') == None:
        data['caller_user'] = caller_user
      if data.get('caller_action') == None:
        data['caller_action'] = caller_action
      if queue_name not in queues:
        queues[queue_name] = []
      queues[queue_name].append(taskqueue.Task(url=url, payload=json.dumps(data)))
  if len(queues):
    for queue_name, tasks in queues.items():
      queue = taskqueue.Queue(name=queue_name)
      queue.add(tasks, transactional=transactional)
