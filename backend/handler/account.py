# -*- coding: utf-8 -*-
'''
Created on Sep 23, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import hashlib

import io, util, settings
from handler import base
 
class Login(base.RequestHandler):
  
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
    self.redirect('/') # @todo there is no other way to signal back to user what he needs to do next other than just redirect him to /
  
 
class Logout(base.RequestHandler):
    
  def respond(self):
    data = self.get_input()
    data.update({
                 'action_model' : '11',
                 'action_key' : 'logout',   
               })
    output = io.Engine.run(data)
    self.response.delete_cookie('auth')
    self.redirect('/') # @todo there is no other way to signal back to user what he needs to do next other than just redirect him to /
            
    
settings.HTTP_ROUTES.extend((('/api/login', Login, 'login'),
                 ('/api/login/<provider>', Login, 'login_provider'),
                 ('/api/logout', Logout, 'logout')))