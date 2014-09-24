# -*- coding: utf-8 -*-
'''
Created on Feb 26, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import urllib

from handler import base
    
settings.ROUTES.extend(((r'/', base.AngularBlank),
                       (r'/sell/catalogs', base.AngularBlank),
                       (r'/login', base.AngularBlank),
                       (r'/login/<provider>', base.AngularBlank),
                       (r'/admin/search/<kind>/<filter>', base.AngularBlank)))

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
      kwargs = {'payload': data, 'method': method, 'url': full_path, 'headers': self.request.headers}
      result = urlfetch.fetch(**kwargs)
      self.response.write(result.content)
      
  settings.ROUTES.append((r'/api/<:.*>', BackendProxy))