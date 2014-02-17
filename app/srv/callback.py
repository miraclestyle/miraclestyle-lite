from google.appengine.api import taskqueue


class Context():
  
  def __init__(self):
    self.inputs = []


class Engine:
  
  @classmethod
  def run(cls, context):
    if len(context.callback.inputs):
      for input in context.callback.inputs:
        taskqueue.add(queue_name='callback', url='/io_engine_run', params=input, transactional=True)
