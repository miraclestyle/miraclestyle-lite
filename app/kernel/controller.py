# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import random
 
from google.appengine.api import urlfetch
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError
 
from app import settings, ndb
from app.core import logger
from app.request import Segments
from app.kernel.models import (User, UserIdentity, UserEmail, UserIPAddress, ObjectLog, TestExpando, Role, RoleUser, CatalogImage)
 
class Tests(Segments):
    
      # unit testing segmenter
      
      def segment_test7(self):
          bar = CatalogImage(state=1, some_text='foobar')
          bar.put()
          self.response.write(bar)
      
      def segment_test6(self):
          self.response.write(User.current().has_permission(permission_name='view_published_catalog', _raise=True))
      
      def segment_test5(self):
          user = User.get_current_user()
          if user.is_logged:
             if self.request.get('make_roles'): 
                 newrole = Role(parent=user.key, name='Admin', permissions=['update_active_user', 'suspend_active_user', 'activate_suspended_user']).put()
                 RoleUser(parent=user.key, role=newrole, state=1).put()
                 user.aggregate_user_permissions()
                 user._self_clear_memcache()
             else:
                 self.response.write(user.has_permission(user, 'update'))
                 
          else:
               self.response.write(user.has_permission(user, 'update'))
    
      def segment_test4(self):
          user = User.get_current_user()
          if user.is_logged:
             self.response.write('Hello, %s' % user.primary_email)
             for l in user.logs:
                 self.response.write([l.key.id(), l.get_log])
                 
             if self.request.get('make'):
                pass
                 
             if self.request.get('check'):
                user.has_permission(user, 'update', _raise=True)
    
      def segment_test3(self):
          if self.request.get('k'):
             t = ndb.Key(urlsafe=str(self.request.get('k'))).get()
             
             if self.request.get('put'):
                 del t.baaz
                 t.put()
             self.response.write(t)
             return
             
          a = TestExpando(foobar=2, baaz=4, faas=3)
          a.put()
          
          self.response.write([a, a.key.urlsafe()])
    
      def segment_test2(self):
          
          if self.request.get('cr'):
              u = User(state=1)
              u.put()
              
              self.response.write('user key: %s<br />' % u.key.urlsafe())
              
              ue = UserEmail(parent=u.key, email='test%s@example.com' % str(random.random()).replace('.', '_'))
              ue.put()
              
              oblog = ObjectLog(parent=ue.key, agent=u.key, action=1, state=1)
              
              oblog.put()
          else:
              #oblog = ndb.Key(ObjectLog, str(self.request.get('k'))).get()
              #oblog = ObjectLog.get(self.request.get('k'))
              if self.request.get('cstate'):
                 u = ndb.Key(urlsafe=str(self.request.get('uk'))) 
                 """ue = UserEmail(parent=u, email='test%s@example.com' % str(random.random()).replace('.', '_'))
                 ue.put() 
                 oblog = ObjectLog(parent=ue.key, agent=u, action=2, state=2)
                 oblog.put()"""
                 oblog = ObjectLog(parent=u, agent=u, action=2, state=2)
                 oblog.put()
                 
              lista = ObjectLog.query(ancestor=ndb.Key(urlsafe=str(self.request.get('uk')))).fetch()
              for a in lista:
                  self.response.write(a)
                  self.response.write('<br /><br />')
              return
              oblog = ndb.Key(urlsafe=str(self.request.get('k')))
              pa = oblog.parent()
              self.response.write(pa.get())
              while pa:
                  pa = pa.parent()
                  if not pa:
                     break
            
                  self.response.write(pa.get())
                  self.response.write('<br /><br />')
                  
          
          self.response.write('object log: %s<br />' % oblog.key.urlsafe())
    
      def segment_test(self):
 
          user = User.get_current_user()
  
          if self.request.get('a'):
             user.logout()
             user.new_state(None, 'logout', log=[user])
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
                 relate = None
                 relate2 = None
                 # build virtual composite key
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
                         user = User(state=User.default_state())
                         user.put()
                         
                         # register new action for newly `put` user
                         user.new_state(None, 'register')

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
                        ip = UserIPAddress(parent=user.key, ip_address=self.request.remote_addr).put()
                
                     if record_login_event:   
                        # record login action if needed
                        user.new_state(None, 'login', log=[user, ip])
                     
                     return user
                      
                 user = run_save(user, user_is_new, relate, relate2)
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
              self._common[p] = v.step1_get_authorize_url()
           
          return self.render('user/authorize.html', self._common)