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
      if context.callback.transactional is None:
        context.callback.transactional = ndb.in_transaction()
      if context.callback.transactional:
        if len(context.callback.inputs) > 5:
          context.callback.inputs = context.callback.inputs[:5]
      for input in context.callback.inputs:
        taskqueue.add(queue_name='io', url='/task/io_engine_run', params=input, transactional=context.callback.transactional)
