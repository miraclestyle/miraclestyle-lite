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
    self.inputs = []
    self.payloads = []
    self.transactional = None


class Engine:
  
  @classmethod
  def run(cls, context):
    
    queue = taskqueue.Queue(name='callback')
    tasks = []
    url = '/task/io_engine_run'
    
    if context.callback.transactional is None:
      context.callback.transactional = ndb.in_transaction()
      
    if len(context.callback.inputs):
      context.callback.inputs = context.callback.inputs[:5] # this cannot be like this
      for input in context.callback.inputs:
        tasks.append(taskqueue.Task(url=url, params=input))
        
    if len(context.callback.payloads):
      context.callback.payloads = context.callback.payloads[:5] # this cannot be like this, cuz this will cut off the notify engine
      for payload in context.callback.payloads:
        tasks.append(taskqueue.Task(url=url, payload=json.dumps(payload)))
        
    if tasks:
      queue.add(tasks, transactional=context.callback.transactional)
        
    context.callback.inputs = []
    context.callback.payloads = []
