# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import hashlib

from backend import io, util
from frontend import frontend_settings
from frontend.handler import base
 
class Login(base.Angular):
  
  def respond(self, provider=None):
    if provider is None:
       provider = 'google'
    data = self.get_input()
    data['login_method'] = provider
    data.update({
                 'action_model' : '11',
                 'action_id' : 'login',   
                })
    output = io.Engine.run(data)
    if 'authorization_code' in output:
      self.response.set_cookie('auth', output.get('authorization_code'), httponly=True)
    return output
  
 
class Logout(base.Angular):
    
  def respond(self):
    data = self.get_input()
    data.update({
                 'action_model' : '11',
                 'action_key' : 'logout',   
               })
    output = io.Engine.run(data)
    self.response.delete_cookie('auth')
    return output
            
    
frontend_settings.ROUTES.extend((('/login', Login, 'login'),
                 ('/login/<provider>', Login, 'login_provider'),
                 ('/logout', Logout, 'logout')))