# -*- coding: utf-8 -*-
'''
Created on Feb 26, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import urllib

from handler import base

# update this config to map paths
# so far we just mapped paths, but we will need logic for some of them, like catalog/<key> and seller/<key>
settings.ROUTES.extend(((r'/', base.AngularBlank),
                       (r'/collections', base.AngularBlank),
                       (r'/buy/orders', base.AngularBlank),
                       (r'/buy/carts', base.AngularBlank),
                       (r'/seller/<key>', base.AngularBlank),
                       (r'/sell/catalogs', base.AngularBlank),
                       (r'/sell/orders', base.AngularBlank),
                       (r'/sell/carts', base.AngularBlank),
                       (r'/login/status', base.AngularBlank),
                       (r'/admin/list/<kind>/<filter>', base.AngularBlank)))

# due development server bug, proxy the endpoint api to the real module
if settings.DEVELOPMENT_SERVER:
  
  from google.appengine.api import urlfetch
  
  class BackendProxy(base.RequestHandler):
    
    autoload_current_account = False
    autoload_model_meta = False
    
    def respond(self, *args, **kwargs):
      full_path = self.request.url.replace('/api/', '/api/proxy/')
      if self.request.method == 'POST':
        method = urlfetch.POST
      else:
        method = urlfetch.GET
      data = self.request.body
      if not data:
        data = self.request.params
      kwargs = {'payload': data, 'deadline': 60, 'method': method, 'url': full_path, 'headers': self.request.headers}
      result = urlfetch.fetch(**kwargs)
      self.response.write(result.content)
      
  settings.ROUTES.append((r'/api/<:.*>', BackendProxy))