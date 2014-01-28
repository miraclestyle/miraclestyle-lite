# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular
 
from app import ndb
from app.srv import event

class Submitter(Angular):
  
    def respond(self):
        return self.render('submitter.html')

class Welcome(Angular):
    
    def respond(self):
        return {}
      
class Endpoint(Angular):
    
    def respond(self):
        return event.Engine.run(self.reqdata.get_combined_params())
      
class Engine(Angular):

    def respond(self):      
        return event.Engine.taskqueue_run(self.reqdata.get_combined_params()) 
         
 
register(('/endpoint', Endpoint), 
         ('/engine_run', Engine), 
         ('/', Welcome),
         ('/submitter', Submitter))