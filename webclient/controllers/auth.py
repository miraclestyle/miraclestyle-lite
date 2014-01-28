# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular

from app.srv import event

class Login(Angular):
  
    def respond(self, provider):
      
           data = self.reqdata.get_combined_params()
           data['login_method'] = provider
           data.update({
                        'action_model' : 'srv.auth.User',
                        'action_key' : 'login',   
                       })
 
           context = event.Engine.run(data)  
         
           if 'authorization_code' in context.response:
               self.response.set_cookie('auth', context.response.get('authorization_code'), httponly=True)
           
           return context.response
            
 
class Logout(Angular):
    
    def respond(self):
      
        data = self.reqdata.get_combined_params()
        
        data.update({
                     'action_model' : 'srv.auth.User',
                     'action_key' : 'logout',   
                   })
 
        context = event.Engine.run(data)
        
        self.response.delete_cookie('auth')
        
        return context.response
            
    
register((r'/login/<provider>', Login, 'login_provider'),
         (r'/logout', Logout, 'logout'))