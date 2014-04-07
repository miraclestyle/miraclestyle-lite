# -*- coding: utf-8 -*-
'''
Created on Feb 17, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import util
from app.srv import io
from webclient import handler

class IOEngineRun(handler.Base):
     
     def respond(self):
         util.logger('Begin IOEngineRun execute')
         
         input = self.get_input()
         io.Engine.run(input)
         
         util.logger('End IOEngineRun execute')

 
handler.register(('/task/io_engine_run', IOEngineRun, 'io_engine_run'))