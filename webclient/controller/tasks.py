# -*- coding: utf-8 -*-
'''
Created on Feb 17, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb, util
from webclient.handler import Angular
from webclient.route import register

class RunSetup(Angular):

    def respond(self):      
        input = self.get_input()
        configuraiton_key = ndb.Key(urlsafe=input.get('configuration_key'))
        config = configuraiton_key.get()
        
        config.run()
        
        util.logger('Logging Setups configuration.run()')
        
        
register(('/run_configuraiton', RunSetup, 'run_setup'))