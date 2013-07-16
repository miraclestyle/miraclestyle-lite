# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import settings
from app.request import Segments
from app.kernel.models import User
from webapp2_extras.i18n import _

from oauth2client.client import OAuth2WebServerFlow
 
class Login(Segments):
    
      providers = ['facebook', 'google']
      
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
             self.response.write(self.session[keyx].access_token)
             return
          
          if error:
             self.response.write(_('You rejected access to your account.'))
          elif code:
             creds = flow.step2_exchange(code)
             self.session[keyx] = creds
          else:
            return self.redirect(flow.step1_get_authorize_url())
           
      def segment_authorize(self, provider=''):
          for p, v in self.get_flows.items():
              self._common[p] = v.step1_get_authorize_url()
           
          return self.render('user/authorize.html', self._common)