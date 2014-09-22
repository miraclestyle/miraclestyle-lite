# -*- coding: utf-8 -*-
'''
Created on Feb 5, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from backend import io
from frontend import frontend_settings
from frontend.handler import base

class ModelInfo(base.Handler):
  
  def respond(self):
    # beside the content type include the cache headers in the future
    self.response.headers['Content-Type'] = 'text/javascript'
    models = io.Engine.get_schema()
    send = {}
    for kind, model in models.iteritems():
      if kind:
        try:
          int(kind)
          send[kind] = model
        except:
          pass
    script = u"KINDS = {}; \n"
    script += u'KINDS.info = %s;' % self.json_output(send)
    self.response.write(script)
      
      
frontend_settings.ROUTES.append(('/model_info.js', ModelInfo))
