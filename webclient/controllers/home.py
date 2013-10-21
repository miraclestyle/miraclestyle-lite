# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular

class HomePage(Angular):
    
    def respond(self):
        u = self.current_user
        self.data['hello'] = 'homepage'
        self.data['user'] = u
         
register(('/', HomePage, 'index'))