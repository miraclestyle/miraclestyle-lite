# -*- coding: utf-8 -*-
'''
Created on Feb 17, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb, util
from app.srv import io
from webclient import handler

class RunConfiguration(handler.Base):

    def respond(self):
        
        util.logger('Begin Setup configuration.run()')
            
        input = self.get_input()
        configuraiton_key = ndb.Key(urlsafe=input.get('configuration_key'))
        config = configuraiton_key.get()
        config.run()
        
        util.logger('End Setup configuration.run()')
        

class IOEngineRun(handler.Base):
     
     def respond(self):
         util.logger('Begin IOEngineRun execute')
         
         input = self.get_input()
         io.Engine.taskqueue_run(input)
         
         util.logger('End IOEngineRun execute')
 
handler.register(('/task/run_configuration', RunConfiguration, 'run_configuration'),
         ('/task/io_engine_run', IOEngineRun, 'io_engine_run'))