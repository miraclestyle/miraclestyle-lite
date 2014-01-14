# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.srv import auth
from webclient.route import register
from webclient.handler import Angular

class Login(Angular):
  
    def respond(self, provider):
      
           data = self.reqdata.get_combined_params()
           data['login_method'] = provider
           
           context = auth.User.login(data)
         
           if 'authorization_code' in context.response:
               self.response.set_cookie('auth', context.response.get('authorization_code'), httponly=True)
           
           return context.response
            
 
class Logout(Angular):
    
    def respond(self):
 
        context = auth.User.logout(self.reqdata.get_combined_params())
        
        self.response.delete_cookie('auth')
        
        return context.response
            
    
register((r'/login', Login, 'login'),
         (r'/login/<provider>', Login, 'login_provider'),
         (r'/logout', Logout, 'logout'))