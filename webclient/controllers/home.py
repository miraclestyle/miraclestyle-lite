# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular

class HomePage(Angular):
    
    def respond(self):
        self.data['hello'] = 'homepage'
        
        
        
register(('/', HomePage, 'index'))