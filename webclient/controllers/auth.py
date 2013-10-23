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
 
        usr = core.acl.User
        if provider is not None:
           code = self.request.get('code')
           error = self.request.get('error')
           command = {'login_method' : provider,
                      'redirect_uri' : self.uri_for('login_provider', provider=provider, _full=True),
                      'ip' : self.request.remote_addr,
                      'current_user' : self.current_user,
           }
           if code:
              command['code'] = code
              
           if error:
              command['error'] = error
           response = usr.login(**command)
           logged_in = response.get('logged_in')
           if logged_in:
              self.set_current_user(logged_in)
              
           self.data['response'] = response
           
        self.data['providers'] = settings.LOGIN_METHODS
 
class Logout(Angular):
    
    def respond(self):
        current = self.current_user
        if not current.is_guest:
           response = current.logout()
           self.data['status'] = response
        else:
           self.data['status'] = {'already_logged_out' : True}
            
    
register((r'/login', Login, 'login'),
         (r'/login/<provider>', Login, 'login_provider'),
         (r'/logout', Logout, 'logout'))