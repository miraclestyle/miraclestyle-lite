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
  
  class ResolveBackendProxy(base.RequestHandler):
    
    autoload_current_account = False
    autoload_model_meta = False
    
    def respond(self, *args, **kwargs):
      if self.request.method == 'POST':
        method = urlfetch.POST
      else:
        method = urlfetch.GET
      data = self.request.body
      if not data:
        data = self.request.params
      kwargs = {'payload': data, 'method': method, 'url': '%s%s' % (self.request.host_url, urllib.unquote_plus(self.request.get('__path'))), 'headers': self.request.headers}
      result = urlfetch.fetch(**kwargs)
      self.response.write(result.content)
  
  
  class BackendProxy(base.RequestHandler):
    
    autoload_current_account = False
    autoload_model_meta = False
    
    def respond(self, *args, **kwargs):
      full_path = '%s/resolve_proxy?__path=%s' % (self.request.host_url, urllib.quote_plus(self.request.path))
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
      
    
  settings.ROUTES.extend((('/resolve_proxy', ResolveBackendProxy),
                          ('/api/endpoint', BackendProxy),
                          ('/api/model_meta', BackendProxy),
                          ('/api/task/io_engine_run', BackendProxy),
                          ('/api/install', BackendProxy),
                          ('/api/login', BackendProxy, 'login'),
                          ('/api/login/<provider>', BackendProxy, 'login_provider'),
                          ('/api/logout', BackendProxy, 'logout')))