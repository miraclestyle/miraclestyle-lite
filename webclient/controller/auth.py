# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient import handler
from app import io
 

class Login(handler.Angular):
  
  def respond(self, provider=None):
    if provider is None:
       provider = 'google'
    data = self.get_input()
    data['login_method'] = provider
    data.update({
                 'action_model' : '0',
                 'action_id' : 'login',   
                })
    output = io.Engine.run(data)  
    if 'authorization_code' in output:
        self.response.set_cookie('auth', output.get('authorization_code'), httponly=True)
    return output
            
 
class Logout(handler.Angular):
    
  def respond(self):
    data = self.get_input()
    data.update({
                 'action_model' : '0',
                 'action_key' : 'logout',   
               })
    output = io.Engine.run(data)
    self.response.delete_cookie('auth')
    return output
            
    
handler.register((r'/login', Login, 'login'), 
         (r'/login/<provider>', Login, 'login_provider'),
         (r'/apps', handler.AngularBlank, 'apps'), 
         (r'/logout', Logout, 'logout'))