# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os

from app import core

from webclient.route import register
from webclient.handler import Angular

class HomePage(Angular):
    
    def respond(self):
        return {'os.environ' : dict(os.environ), 'user' : core.acl.User.current_user()}
         
register(('/', HomePage, 'index'))