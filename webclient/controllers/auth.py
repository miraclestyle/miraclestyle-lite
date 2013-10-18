# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import core
from webclient.route import register
from webclient.handler import Angular

class Login(Angular):
    
    def respond(self, provider=None):
 
        self.for_guests()

        usr = core.user.User
        if provider is not None:
           code = self.request.get('code')
           error = self.request.get('error')
           command = {'login_method' : provider,
                      'redirect_uri' : self.uri_for('login_provider', provider=provider, _full=True),
                      'ip' : self.request.remote_addr
           }
           if code:
              command.update({'code' : code})
              
           if error:
              command['error'] = error
           response = usr.login(**command)
           logged_in = response.get('logged_in')
           
           if logged_in:
              self.set_current_user(logged_in.key)
              
           self.data['response'] = response
           
        self.data['select_provider'] = 1
 
class Register(Angular):
    
    def respond(self):
        pass 
    
register((r'/login', Login, 'login'),
         (r'/login/<provider>', Login, 'login_provider'),
         (r'/register', Register, 'register'))