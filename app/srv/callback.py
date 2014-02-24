# -*- coding: utf-8 -*-
'''
Created on Feb 20, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.api import taskqueue

from app import ndb


class Context():
  
  def __init__(self):
    self.inputs = []
    self.transactional = None


class Engine:
  
  @classmethod
  def run(cls, context):
    if len(context.callback.inputs):
      context.callback.inputs = context.callback.inputs[:5]
      if context.callback.transactional is None:
        context.callback.transactional = ndb.in_transaction()
      queue = taskqueue.Queue(name='callback')
      tasks = []
      for input in context.callback.inputs:
        tasks.append(taskqueue.Task(url='/task/io_engine_run', params=input))
      if tasks:
        queue.add(tasks, transactional=context.callback.transactional)
