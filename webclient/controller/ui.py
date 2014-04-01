# -*- coding: utf-8 -*-
'''
Created on Feb 5, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json

from app.srv import io

from webclient import handler
from webclient.util import JSONEncoderHTML
  
class ModelInfo(handler.Base):
  
  def respond(self):
    
    # beside the content type include the cache headers in the future
    self.response.headers['Content-Type'] = 'text/javascript'
    
    script = u"KINDS = {}; \n"
    script += u'KINDS.info = %s;' % json.dumps(io.Engine.get_schema(), indent=2, cls=JSONEncoderHTML)
     
    self.response.write(script)
      
      
handler.register(('/', handler.AngularBlank),
                 ('/model_info.js', ModelInfo))
