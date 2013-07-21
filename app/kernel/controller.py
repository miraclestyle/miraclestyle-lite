# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import urllib2
import json
import logging

from app import ndb

from app import settings
from app.request import Segments, Handler
from app.kernel.models import User, UserIdentity, UserEmail, UserIPAddress
from app.kernel.forms import TestForm
from webapp2_extras.i18n import _

from oauth2client.client import OAuth2WebServerFlow


class UnitTests(Handler):
    
      def respond(self):
          
          
          localss = globals()
          
          io = []
     
          choices2 = ['UserEmail', 'UserConfig', 'UserIPAddress']
          choices = [(f, f) for f in choices2]
          
          if self.request.get('put'):
             User(state=1).put()
          
          users = [User.query().get(keys_only=True)]
          userss = []
          
          is_post = True if self.request.method == 'POST' else False
          
          def pop(ax, i):
              dictx = {}
              for k, v in ax._properties.items():
      
                  if isinstance(v, ndb.StringProperty):
                     i = str(i)
                  
                  if isinstance(v, (ndb.StringProperty, ndb.TextProperty, ndb.IntegerProperty)):
                     dictx[k.__str__()] = i
          
              return dictx
          
          for user in users:
              f = TestForm(self.request.POST)
              f.models.choices = choices
              f.mode.data = user.urlsafe()
              
              io.append('Init user with key %s' % user.urlsafe())
              
              data = {'user' : user, 'form' : f}
              factory = []
              
              def run_query():
                  for c in choices2:
                      gets = localss.get(c)
                      
                      io.append('Model %s ready for factory' % c)
                     
                      if f.models.data and c in f.models.data and is_post and f.remove_all.data:
                             ndb.delete_multi(gets.query(ancestor=user).iter(keys_only=True))
                             io.append('Delete all from user %s in model %s' % (user.urlsafe(), c))
                     
                      if is_post:
                          io.append('Running query for %s %s times' % (c, f.times.data))
                          if is_post and c in f.models.data and f.times.data and not f.remove_all.data:
                             for itx in range(0, f.times.data):
                                 if f.cause_error.data and int(f.cause_error.data) == itx:
                                     raise Exception('foobar')
                                 ax = gets(parent=user)
                                 ax.populate(**pop(ax, itx))
                                 pk = ax.put()
                                 io.append('Wrote model %s, to User, iteration %s, got id %s' % (c, itx, pk.integer_id()))
                
                            
              if f.transaction.data:
                         io.append('Started runnig in transaction')
                         ndb.transaction(run_query)
                         io.append('Completed running transaction')
              else:
                         io.append('Run query without transaction')
                         run_query()
                         io.append('Complete query without transaction')
                     
                  
              for c in choices2:
                  io.append('Querying results for %s' % c)
                  gets = localss.get(c)
                  items = gets.query(ancestor=user).iter()
                  factory.append({'title' : c, 'children' : items})
                  
              data['children'] = factory
              userss.append(data)
                  
                  
              
          self._common['users'] = userss
          self._common['io'] = io
          self.render('tests/index.html')
 
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
          
          provider_id = settings.MAP_IDENTITIES[provider]
          
          if provider_id and self.session.has_key(keyx):
             if User.is_logged():
                self.response.write('Already logged in %s' % User.get_current_user().key.urlsafe()) 
                return
          
             try:
                 data = getattr(self, '_login_%s_get_creds' % provider)(self.session[keyx].access_token)
             except urllib2.HTTPError, e:
                 logging.exception(e)
                 del self.session[keyx]
             else:
                 relate = UserIdentity.md5_get_by_id(identity=data.get('id'), provider=provider_id)
                 relate2 = UserEmail.md5_get_by_id(email=data.get('email'))
                 user_is_new = True
                 
                 try:
                    user = None
                    if relate or relate2:
                        
                       if relate:
                          user = relate.key.parent().get()
                       if relate2 and not user:
                          user = relate2.key.parent().get()
                          
                       if user is not None:
                          user_is_new = False
                            
                 except KeyError, e:
                     raise e
                 else:
                     @ndb.transactional(xg=True)
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
                                 if relate:
                                    if not relate2:
                                       put_email = True  
                                       
                                 if relate2:
                                    if not relate:
                                       put_identity = True
                                       user_email = relate2
                                 
                             if put_email:
                                user_email = UserEmail(parent=user.key, id=UserEmail.md5_create_key(email=data.get('email')), primary=user_is_new, email=data.get('email'))
                                user_email.put()
                                    
                             if put_identity:
                                ident = UserIdentity(parent=user.key, id=UserIdentity.md5_create_key(identity=data.get('id'), provider=provider_id), identity=str(data.get('id')), provider=str(provider_id))
                                if put_email or relate2:
                                   ident.user_email = user_email.key
                                ident.put()
                                 
                             if put_ipaddress:
                                UserIPAddress(parent=user.key, ip_address=self.request.remote_addr).put()
                                
                             user.new_event(2, state=user.state)
                             
                             return user
                             
                     user = run_save(user, user_is_new, relate, relate2)
                     self.session[settings.USER_SESSION_KEY] = user.key
                     self.response.write('Successfully logged in, %s' % user.key.urlsafe())
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
          
          current = User.get_current_user()
    
          logging.info(current)
        
          for p, v in self.get_flows.items():
              self._common[p] = v.step1_get_authorize_url()
           
          return self.render('user/authorize.html', self._common)