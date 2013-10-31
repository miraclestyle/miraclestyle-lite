# -*- coding: utf-8 -*-
'''
Created on Oct 23, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import core

from webclient.route import register
from webclient.handler import Angular

class RoleManage(Angular):
    
    def respond(self):
        pass
    
class CountryList(Angular):
    
    def respond(self):
        return core.misc.Country.list()  
    
class CountryManage(Angular):
    
    def respond(self):
        args = ('id', 'name', 'active', 'code')
        return core.misc.Country.manage(**self.reqdata.get_all(args))
    
    
register(('/admin/role/manage', RoleManage),
         ('/admin/country/manage', CountryManage),
         ('/admin/country/list', CountryList))