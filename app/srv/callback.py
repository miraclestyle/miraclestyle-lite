# -*- coding: utf-8 -*-
'''
Created on Feb 20, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import taskqueue

from app import ndb


class Context():
  
  def __init__(self):
    self.payloads = []
    self.transactional = None


class Engine:
  
  @classmethod
  def run(cls, context):
    tasks = {}
    url = '/task/io_engine_run'
    if context.callback.transactional is None:
      context.callback.transactional = ndb.in_transaction()
    if context.callback.transactional:
      context.callback.payloads = context.callback.payloads[:5]
    if len(context.callback.payloads):
      for payload in context.callback.payloads:
        queue_name, data = payload
        try:
          kwargs = payload[2]
        except IndexError as e:
          kwargs = {}
        if queue_name not in tasks:
          tasks[queue_name] = []
        tasks[queue_name].append(taskqueue.Task(url=url, payload=json.dumps(data), **kwargs))
    if len(tasks):
      for queue_name, tasks in tasks.items():
        queue = taskqueue.Queue(name=queue_name)
        queue.add(tasks, transactional=context.callback.transactional)
    context.callback.payloads = []
