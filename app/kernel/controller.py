# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import logging

from google.appengine.api import urlfetch
 
from webapp2_extras.i18n import _ 
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError
 
from app import ndb

from app import settings
from app.request import Segments, Handler
from app.kernel.models import User, UserIdentity, UserEmail, UserIPAddress
 
class Tests(Segments):
    
      def segment_test(self):
 
          user = User.get_current_user()
  
          if self.request.get('a'):
             user.logout()
             del self.session[settings.USER_SESSION_KEY]
             user = False
          
          if not user:
             self.response.write('Please login<br />')
          else:
             self.response.write('Hello %s' % user.primary_email)
             self.response.write('<br /><a href="?a=1">Logout</a><br />')
  
          self.response.write('<br />Test')
 
 
class Login(Segments):
    
      providers = ['facebook', 'google']
      
      def _login_google_get_creds(self, ac):
        data = urlfetch.fetch('%s?access_token=%s' % (getattr(settings, 'GOOGLE_OAUTH2_USERINFO'), ac))
        assert data.status_code == 200
        data = json.loads(data.content)
        return {'id' : data['id'], 'email' : data['email'], 'raw' : data}
    
      def _login_facebook_get_creds(self, ac):
        data = urlfetch.fetch('%s?access_token=%s' % (getattr(settings, 'FACEBOOK_OAUTH2_USERINFO'), ac))
        assert data.status_code == 200
        data = json.loads(data.content)
        return {'id' : data['id'], 'email' : data['email'], 'raw' : data}
      
      @property
      def get_flows(self):
          flows = {}
          for p in self.providers:
              conf = getattr(settings, '%s_OAUTH2' % p.upper())
              if conf:
                   if conf['redirect_uri'] == False:
                      conf['redirect_uri'] = self.uri_for('login', provider=p, segment='exchange', _full=True)
              flows[p] = OAuth2WebServerFlow(**conf)
          return flows
      
      def before(self):
          provider = self.request.route_kwargs.get('provider', None)
          if not provider:
             return
         
          if provider not in self.providers:
             self.abort(403)
   
      def segment_exchange(self, provider):
          
          flow = self.get_flows[provider]
          code = self.request.GET.get('code')
          error = self.request.GET.get('error')
          keyx = 'oauth2_%s' % provider
          
          user = None
          save_in_session = True
          record_login_event = True
          user_is_new = False
          
          provider_id = settings.MAP_IDENTITIES[provider]
          
          if provider_id and self.session.has_key(keyx):
             
             user = User.get_current_user()
             if user:
                self.response.write('Already logged in %s' % user.key.urlsafe()) 
                save_in_session = False
                record_login_event = False
          
             try:
                 data = getattr(self, '_login_%s_get_creds' % provider)(self.session[keyx].access_token)
                 self.response.write(data)
             except (AssertionError, TypeError), e:
                 del self.session[keyx]
             except Exception, e:
                 logging.info(e)
                 try:
                   del self.session[keyx]
                 except:
                     pass
             else:
                 relate = None
                 relate2 = None
                 
                 the_id = '%s-%s' % (data.get('id'), provider_id)   
                 email = data.get('email')
                 
                 relate = UserIdentity.query(UserIdentity.identity==the_id).get_async()
                 relate2 = UserEmail.query(UserEmail.email==email).get_async()
                 
                 relate = relate.get_result() 
                 relate2 = relate2.get_result() 
          
                 if (relate or relate2):
                     if relate:
                         user = relate.key.parent().get()
                          
                     if relate2 and not user:
                         user = relate2.key.parent().get()
                          
                 if user:
                    user_is_new = False
                 else:
                    user_is_new = True
            
                 @ndb.transactional
                 def run_save(user, user_is_new, relate, relate2):
                         
                     put_identity = False
                     put_ipaddress = True
                     put_email = False
                     
                     if user_is_new:
                         user = User(state=1)
                         user.put()
                        
                         user.new_state(1, event=0)
                         user.new_event(1, state=1)
                         
                         put_email = True
                         put_identity = True
                     else:
                         
                         if not relate and not relate2:
                            put_email = True
                            put_identity = True
                         
                         if relate:
                            if not relate2:
                               put_email = True  
                               
                         if relate2:
                            if not relate:
                               put_identity = True
                               user_email = relate2
                         
                     if put_email:
                        user_email = UserEmail(parent=user.key, primary=user_is_new, email=email)
                        user_email.put()
                            
                     if put_identity:
                        ident = UserIdentity(parent=user.key, identity=the_id)
                        if put_email or relate2:
                           ident.user_email = user_email.key
                        ident.put()
                         
                     if put_ipaddress and record_login_event:
                        UserIPAddress(parent=user.key, ip_address=self.request.remote_addr).put()
                
                     if record_login_event:   
                        user.new_event(2, state=user.state)
                     
                     return user
                      
                 user = run_save(user, user_is_new, relate, relate2)
                 if save_in_session:
                     self.session[settings.USER_SESSION_KEY] = user.key
                 self.response.write('Successfully logged in, %s' % user.key.urlsafe())
                 return
             finally:
                 pass
 
          if error:
             self.response.write(_('You rejected access to your account.'))
          elif code:
             try: 
                 creds = flow.step2_exchange(code)
                 self.session[keyx] = creds
                 if creds.access_token and not hasattr(self, 'recursion'):
                    self.recursion = 1
                    self.segment_exchange(provider)
                 return
             except FlowExchangeError:
                 pass
          return self.redirect(flow.step1_get_authorize_url())
           
      def segment_authorize(self, provider=''):
 
          for p, v in self.get_flows.items():
              self._common[p] = v.step1_get_authorize_url()
           
          return self.render('user/authorize.html', self._common)