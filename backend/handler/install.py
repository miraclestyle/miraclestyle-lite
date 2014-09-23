# -*- coding: utf-8 -*-
'''
Created on Sep 23, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import io, settings
from handler import base

class Install(base.RequestHandler):
  
  def respond(self):
    out = []
    only = self.request.get('only', '').split(',')
    for model, action in [('12', 'update'), ('24', 'update'), ('17', 'update_unit'), ('17', 'update_currency')]:
      if only and model not in only:
        continue
      out.append(io.Engine.run({'action_model' : model, 'action_id' : action}))
    self.send_json(out)
    
settings.HTTP_ROUTES.append(('/api/install', Install))