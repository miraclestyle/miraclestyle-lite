# -*- coding: utf-8 -*-
'''
Created on May 29, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import util, io
from webclient import handler

class IOEngineCronRun(handler.Base):
     
  def respond(self, action_id):
    util.log('Begin IOEngineCronRun execute')
    io.Engine.run({'action_model': '83', 'action_id': action_id})
    util.log('End IOEngineCronRun execute')
 
handler.register(('/cron/<action_id>', IOEngineCronRun, 'io_engine_cron_run'))