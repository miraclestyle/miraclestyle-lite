# -*- coding: utf-8 -*-
'''
Created on Sep 23, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import io, util, settings
from handler import base

class IOEngineRun(base.RequestHandler):
  
  def respond(self):
    util.log('Begin IOEngineRun execute')
    input = self.get_input()
    io.Engine.run(input)
    util.log('End IOEngineRun execute')
    
settings.HTTP_ROUTES.append(('/api/task/io_engine_run', IOEngineRun))