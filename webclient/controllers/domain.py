# -*- coding: utf-8 -*-
'''
Created on Oct 31, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.handler import Angular
from webclient.route import register

from app import domain

class DomainList(Angular):
    
    def respond(self):
        return domain.acl.Domain.list_domains()

class DomainManage(Angular):
    
    def respond(self):
        return domain.acl.Domain.manage(**self.reqdata.get_all(('id','name')))
    
    
register(('/domain/manage', DomainManage),
         ('/domain/list', DomainList))