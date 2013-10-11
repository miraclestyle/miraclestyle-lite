# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.handler import Angular
from webclient.route import register

class Tests(Angular):
    
    def respond(self):
        self.data['Hello'] = 'World'

class Other(Angular):
    pass


ROUTES = register(None, ('/tests', Tests), ('/other', Other))