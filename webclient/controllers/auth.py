# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import core, settings
from webclient.route import register
from webclient.handler import Angular

class Login(Angular):
  
    def respond(self, provider=None):
 
        if provider is not None:
           command = {'login_method' : provider,
                      'redirect_uri' : self.uri_for('login_provider', provider=provider, _full=True),
                      'ip' : self.request.remote_addr,
                      'code' : self.request.get('code'),
                      'error' : self.request.get('error')
           }
             
           response = core.acl.User.login(**command)
           
           if 'authorization_code' in response:
               self.response.set_cookie('auth', response.get('authorization_code'), httponly=True)
           
           return response
            
 
class Logout(Angular):
    
    def respond(self):
        usr = core.acl.User.current_user()
        response = usr.logout(code=self.request.get('code'))
        
        self.response.delete_cookie('auth')
        
        return response
            
    
register((r'/login', Login, 'login'),
         (r'/login/<provider>', Login, 'login_provider'),
         (r'/logout', Logout, 'logout'))