# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json

from google.appengine.api import urlfetch
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError
 
from app import settings, ndb
from app.core import logger
from app.request import Segments
from app.kernel.models import (User, UserIdentity, UserIPAddress)


class TestRoot(ndb.BaseModel):
      _KIND = 'TestRoot'
      name = ndb.StringProperty()
      sequence = ndb.IntegerProperty()
      
class TestChild(ndb.BaseModel):
      _KIND = 'TestChild'
      childname = ndb.StringProperty()
      
      
class Tests(Segments):
    
     def segment_test4(self):
         
         import time
         
         if self.request.get('put'):
            u = TestRoot(name='test', sequence=1)
            u.put()
            
            self.response.write(u)
            self.response.write('<br />Factory key: ' + u.key.urlsafe() + '<br /><br />')
         else:
             u = ndb.Key(urlsafe=self.request.get('k')).get()
             
         
         self.ss = 0.0 
         
         @ndb.transactional
         def trans(u):
             t = time.time()
             b = TestChild(parent=u.key, childname='foobar')
             self.response.write('Writing this entity to %s' % u.key.urlsafe())
             b.put()
             ssa = time.time() - t
             self.ss += ssa
             self.response.write('<br />Wrote it, got id() %s (%s s)<br />' % (b.key.id(), ssa))
             
         for i in range(0, int(self.request.get('iterations', 5))):
             trans(u)
             
         self.response.write('<br />Total time taken to complete %s' % self.ss)
    
     def segment_test(self):
         self.response.write(User.current())
    
     def segment_test5(self):
         if self.request.get('k'):
            u = ndb.Key(urlsafe=self.request.get('k')).get()
            u.identities.append(UserIdentity(identity='baaz', email='email2@gmail.com'))
         else:
             u = User(state=1, identities=[UserIdentity(identity='baaz', email='email@gmail.com')])
             u.put()
             
         self.response.write(u.identities)
         self.response.write(u.key.urlsafe())
 
 
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
             if user.is_logged:
                self.response.write('Already logged in %s' % user.key.urlsafe()) 
                save_in_session = False
                record_login_event = False
             else:
                user = False
          
             try:
                 data = getattr(self, '_login_%s_get_creds' % provider)(self.session[keyx].access_token)
                 self.response.write(data)
             except (AssertionError, TypeError), e:
                 del self.session[keyx]
             except Exception, e:
                 logger(e, 'exception')
                 del self.session[keyx]
             else:
                 # build virtual composite key
                 the_id = '%s-%s' % (data.get('id'), provider_id)   
                 email = data.get('email')
                 
                 user = User.query(User.identities.identity==the_id).get()
                 user_is_new = False
                 if not user:
                    user_is_new = True
                    
                 ip = self.request.remote_addr
            
                 @ndb.transactional
                 def run_save(user, user_is_new, ip, the_id, email):
                     
                     if user_is_new:
                         user = User(state=User.default_state())
                         user.emails = [email]
                         user.identities = [UserIdentity(identity=the_id, email=email)]
                         user.put()
                         # register new action for newly `put` user
                         user.new_state(None, 'register')
                     else:
                         do_put = False
                         if email not in user.emails:
                            do_put = True 
                            user.emails.append(email)
                         add = True  
                         for i in user.identities:
                             if i.identity == the_id:
                                add = False
                                if i.email != email:
                                   user.identities.remove(i)
                                   i.email = email
                                   user.identities.append(i)
                         if add:
                            do_put = True
                            user.identities.append(UserIdentity(identity=the_id, email=email, primary=False))
                     
                         if do_put:   
                            user.put()
                      
                     if record_login_event:
                        ip = UserIPAddress(parent=user.key, ip_address=ip).put()
                
                     if record_login_event:   
                        # record login action if needed
                        user.new_state(None, 'login', log=[user, ip])
                     return user
                      
                 user = run_save(user, user_is_new, ip, the_id, email)
                 if save_in_session:
                     self.session[settings.USER_SESSION_KEY] = user.key
                     User.set_current_user(user)
                 self.response.write('Successfully logged in, %s' % user.key.urlsafe())
                 return
             finally:
                 pass
 
          if error:
             self.response.write('You rejected access to your account.')
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
              self._template[p] = v.step1_get_authorize_url()
          return self.render('user/authorize.html')