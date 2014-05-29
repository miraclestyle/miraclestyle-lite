# -*- coding: utf-8 -*-
'''
Created on May 29, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import util
from app.srv import io
from webclient import handler

class IOEngineCronRun(handler.Base):
     
     def respond(self, action_model, action_id):
         util.logger('Begin IOEngineCronRun execute')
         io.Engine.run({'action_model' : action_model, 'action_id' : action_id})
         util.logger('End IOEngineCronRun execute')
 
handler.register(('/cron/<action_model>/<action_id>', IOEngineCronRun, 'io_engine_cron_run'))