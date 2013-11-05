# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular

from app import ndb
 
class Endpoint(Angular):
    
    def respond(self):
        
        model_path = self.request.get('model')
        method = self.request.get('method')
        
        model = ndb.factory(model_path)
         
        # cruel way of calling methods, but this is just for testing purposes to avoid creating individual controllers.
        # there is no absolute final decision on how the controllers will behave, except we know they will be dumb.
        return getattr(model, method)(**self.request.params)
         
 
register(('/endpoint', Endpoint))