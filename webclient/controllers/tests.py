# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.core import tests
 
from webclient.handler import Angular
from webclient.route import register

class Tests(Angular):
 
    def respond(self):
        res = ndb.Response()
        
        testinst = ndb.Key('TestModel', 5066549580791808).get()
        
        self.data['query'] = str(tests.TestModel.query(tests.TestModel.state == 1).fetch())
        
        if self.request.get('put'):
           testinst.put()
        
        if self.request.get('update'):
           testinst.name = 'Fooxf'
           testinst.state = 'active'
           testinst.sp = 'aaa'
           testinst.put()
  
        res['test_original'] = testinst.original_values
        res['test_key'] = testinst.key
        res['user'] = 1
        res['daemons'] = 2
        res.error('name', 'demons are')
        res.error('name', 'demons are there')
  
 
        self.data['hello'] = 'World'
        self.data['responder'] = res
 

class Other(Angular):
    pass


ROUTES = register(('/tests', Tests), ('/other', Other))