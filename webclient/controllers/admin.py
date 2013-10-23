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
        
        data = {
          'current_user' : self.current_user,
        }
        
        response = {}
        
        if action == 'list':
           self.data['roles'] = core.acl.Role.list_roles()
        
        if action == 'create':
            data.update({
              'name' : self.request.get('name'),
              'actions' : self.request.get_all('actions'),
              'kind_id' : self.request.get('kind_id'),             
            })
            
            response = core.acl.Role.create(**data)
            if 'create' in response:
               response['created_role'] = True
             
        self.data['response'] = response
    
    
    
register(('/admin/manage_role/<action>', RoleManager))