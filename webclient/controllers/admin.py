# -*- coding: utf-8 -*-
'''
Created on Oct 23, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import core

from webclient.route import register
from webclient.handler import Angular

class RoleManager(Angular):
    
    def respond(self):
        pass
    
class CountryManager(Angular):
    
    def respond(self):
        args = ('id', 'name', 'active', 'code')
        return core.misc.Country.manage(**self.reqdata.get_all(args))
    
    
register(('/admin/manage_role', RoleManager),
         ('/admin/manage_country', CountryManager))