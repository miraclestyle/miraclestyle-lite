# -*- coding: utf-8 -*-
'''
Created on Oct 23, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import core

from webclient.route import register
from webclient.handler import Angular

class RoleManager(Angular):
    
    def respond(self, action):
        pass
    
    
register(('/admin/manage_role/<action>', RoleManager))