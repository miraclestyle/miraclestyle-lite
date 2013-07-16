# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import urllib2
import json

from app import db

from app import settings
from app.request import Segments
from app.kernel.models import User, UserIdentity, UserEmail
from webapp2_extras.i18n import _

from oauth2client.client import OAuth2WebServerFlow
 
class Login(Segments):
    
      providers = ['facebook', 'google']
      
      def _login_google_get_creds(self, ac):
        data = urllib2.urlopen('%s?access_token=%s' % (getattr(settings, 'GOOGLE_OAUTH2_USERINFO'), ac)).read()
        if data:
           data = json.loads(data)
        return {'id' : data['id'], 'email' : data['email'], 'raw' : data}
    
      def _login_facebook_get_creds(self, ac):
        data = urllib2.urlopen('%s?access_token=%s' % (getattr(settings, 'FACEBOOK_OAUTH2_USERINFO'), ac)).read()
        if data:
           data = json.loads(data)
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
          
          if self.session.has_key(keyx):
             
             if self.session.has_key(settings.USER_SESSION_KEY):
                self.response.write('Already logged in %s' % self.session[settings.USER_SESSION_KEY]) 
                return
              
             try:
                 data = getattr(self, '_login_%s_get_creds' % provider)(self.session[keyx].access_token)
             except urllib2.HTTPError:
                 del self.session[keyx]
             else:
                 relate = UserIdentity.all().filter('identity =', data.get('id')).get()
                 relate2 = UserEmail.all().filter('email =', data.get('email')).get()
                 user_is_new = False
                 try:
                    if not (relate and relate2):
                         user = User(state=1)
                         user.put()
                         user_is_new = True
                         user.new_state(1, event=0)
                         user.new_event(1, state=1)
                    else:
                         user = None
                         if relate:
                            user = relate.user
                         if relate2 and not user:
                            user = relate2.user
                            
                 except Exception, e:
                     raise e
                 else:
                     @db.transactional(xg=True)
                     def run_save(user, user_is_new, relate, relate2):
                         
                             if user_is_new:
                                 user_email = UserEmail(user=user, primary=True, email=data.get('email')).put()
                                 UserIdentity(user=user, identity=data.get('id'), user_email=user_email, provider=settings.MAP_IDENTITIES[provider]).put()      
                                 
                             if relate:
                                user = relate.user
                                if not relate2:
                                   UserEmail(user=user, email=data.get('email')).put()
                                   
                             if relate2:
                                user = relate2.user
                                if not relate:
                                   UserIdentity(user=user, identity=data.get('id'), user_email=relate2, provider=settings.MAP_IDENTITIES[provider]).put()      
                             
                             user.new_event(2, state=user.state)
                             
                             return user
                             
                     user = run_save(user, user_is_new, relate, relate2)
                     self.session[settings.USER_SESSION_KEY] = user.key()
                     self.response.write('Successfully logged in')
                     return
                
             finally:
                 pass
 
          if error:
             self.response.write(_('You rejected access to your account.'))
          elif code:
             creds = flow.step2_exchange(code)
             self.session[keyx] = creds
             if creds.access_token and not hasattr(self, 'recursion'):
                self.recursion = 1
                self.segment_exchange(provider)
          else:
             return self.redirect(flow.step1_get_authorize_url())
           
      def segment_authorize(self, provider=''):
          for p, v in self.get_flows.items():
              self._common[p] = v.step1_get_authorize_url()
           
          return self.render('user/authorize.html', self._common)