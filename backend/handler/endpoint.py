# -*- coding: utf-8 -*-
'''
Created on Sep 23, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import io, settings
from handler import base

class Endpoint(base.RequestHandler):
  
  def respond(self):
    output = io.Engine.run(self.get_input())
    self.send_json(output)
    
class ModelMeta(base.RequestHandler):
  
  def respond(self):
    # @todo include cache headers here
    models = io.Engine.get_schema()
    send = {}
    for kind, model in models.iteritems():
      if kind:
        try:
          int(kind)
          send[kind] = model
        except:
          pass
    self.send_json(send)
    
settings.HTTP_ROUTES.extend((('/api/endpoint', Endpoint),
                             ('/api/model_meta', ModelMeta)))