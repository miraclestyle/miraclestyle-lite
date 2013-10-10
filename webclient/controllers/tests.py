# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.handler import Handler
from webclient.route import register

class Tests(Handler):
    
    def respond(self):
        self.response.write('Hello World')

class Other(Handler):
    pass


ROUTES = register(None, ('/tests', Tests), ('/other', Other))