# -*- coding: utf-8 -*-
'''
Created on Feb 5, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json

from app import io

from webclient import handler
from webclient.util import JSONEncoderHTML, to_json
  
class ModelInfo(handler.Base):
  
  def respond(self):
    
    # beside the content type include the cache headers in the future
    self.response.headers['Content-Type'] = 'text/javascript'
    
    models = io.Engine.get_schema()
    send = {}
    for kind, model in models.items():
      if kind:
        try:
          int(kind)
          send[kind] = model
        except:
          pass
    
    script = u"KINDS = {}; \n"
    script += u'KINDS.info = %s;' % to_json(send)
     
    self.response.write(script)
      
      
handler.register(('/', handler.AngularBlank),
                 ('/model_info.js', ModelInfo))
