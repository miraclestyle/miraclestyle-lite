# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import cgi
import json
import time
import webapp2
import importlib
import collections
  
from jinja2 import FileSystemLoader
from webapp2_extras import jinja2

from app import settings, util
from app.srv import blob
from app.memcache import _local
 
from webclient import webclient_settings
from webclient.util import JSONEncoderHTML, JINJA_GLOBALS, JINJA_FILTERS
from webclient.route import get_routes
 
__WSGI_CONFIG = None
 
def wsgi_config(as_tuple=False):
    
    """ Config function. Prepares all variables and routes for webapp2 WSGI startup """
    
    global __WSGI_CONFIG
 
    if __WSGI_CONFIG:
       if not as_tuple:
          return __WSGI_CONFIG
       return tuple(__WSGI_CONFIG.items())
  
    TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'template'),)
      
    for a in webclient_settings.ACTIVE_CONTROLLERS:
        importlib.import_module('webclient.controller.%s' % a)
      
    # It won't change, so convert it to a tuple to save memory.   
    ROUTES = tuple(get_routes())
   
    JINJA_GLOBALS.update({'uri_for' : webapp2.uri_for, 'ROUTES' : ROUTES, 'settings' : settings, 'webclient_settings' : webclient_settings})
    TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_DIRS)
    
    util.logger('Webapp2 started, compiling stuff')
    
    WSGI_CONFIG = {}
    WSGI_CONFIG.update(webclient_settings.WEBAPP2_EXTRAS)
    WSGI_CONFIG['webapp2_extras.jinja2'] = {
                 'template_path': 'templates',
                 'globals' : JINJA_GLOBALS,
                 'filters' : JINJA_FILTERS,
                 'environment_args': {
                   'extensions': ['jinja2.ext.autoescape', 'jinja2.ext.loopcontrols'],
                   'autoescape' : True, 
                   'loader' : TEMPLATE_LOADER,
                   'cache_size' : webclient_settings.TEMPLATE_CACHE
         }
    }
     
    
    __WSGI_CONFIG = dict(WSGI_CONFIG=WSGI_CONFIG,
                        ROUTES=ROUTES,
                        JINJA_GLOBALS=JINJA_GLOBALS,
                        JINJA_FILTERS=JINJA_FILTERS,
                        TEMPLATE_DIRS=TEMPLATE_DIRS,
                        TEMPLATE_LOADER=TEMPLATE_LOADER
                       )
    if not as_tuple:
       return __WSGI_CONFIG
    else:
       return tuple(__WSGI_CONFIG.items())
  
  
class Handler(webapp2.RequestHandler):
    
    """
    General-purpose handler that comes with:
    self.template to send variables to render template
    and other hooks like `after`, `before` etc.
    
    """
    
    LOAD_CURRENT_USER = True
 
    def __init__(self, *args, **kwargs):
      
        super(Handler, self).__init__(*args, **kwargs)
        
        self.data = {}
        self.template = {}
   
   
    def get_input(self):
        return collections.OrderedDict(self.request.params.items())
  
  
    def initialize(self, request, response):
        super(Handler, self).initialize(request, response)
 
        for key, value in self.request.params.items():
            if isinstance(value, cgi.FieldStorage):
              if 'blob-key' in value.type_options:
                  blob.Manager.field_storage_unused_blobs(value)

        
  
    def send_json(self, data):
        """ sends `data` to json format, accepts anything json compatible """
        ent = 'application/json;charset=utf-8'
        if self.response.headers.get('Content-Type') != ent:
           self.response.headers['Content-Type'] = ent
        self.response.write(json.dumps(data, indent=2, cls=JSONEncoderHTML))
 
 
    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)
    
    
    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv) 
  
  
    def render(self, tpl, data=None):
        if data == None:
           data = {}
        self.template.update(data)
        return self.render_response(tpl, **self.template)
    
    
    def before(self):
        """
        This function is fired just before the handler, usefull for setting variables
        """
        time.sleep(2) # emulate slowness
        pass
    
    
    def after(self):
        """
        This function is fired just after the handler is executed
        """
        time.sleep(1) # emulate slowness
        pass
    
    
    def get(self, *args, **kwargs):
        return self.respond(*args, **kwargs)
        
        
    def post(self, *args, **kwargs):
        return self.respond(*args, **kwargs)
        
        
    def respond(self, *args, **kwargs):
        self.abort(404)
        self.response.write('<h1>404 Not found</h1>')
 
 
    def dispatch(self):
      
        csrf = None
        csrf_cookie_value = self.request.cookies.get('XSRF-TOKEN')
        
        if self.LOAD_CURRENT_USER:
          
           from app.srv import auth
           
           auth.User.login_from_authorization_code(self.request.cookies.get('auth'))
           
           self.template['current_user'] = auth.User.current_user()
           
           csrf = self.template['current_user'].csrf
           
                          
        if not csrf_cookie_value or (csrf != None and csrf != csrf_cookie_value):
           if csrf == None:
              csrf = util.random_chars(32)
           self.response.set_cookie('XSRF-TOKEN', csrf)
            
        try:
            self.before()
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
            
            self.after()
        finally:
            
            # delete all blobs that did not got used in the application execution
            blob.Manager.delete_unused_blobs()
            
            # support the core's locals, and release them upon request complete
            _local.__release_local__()
         
 
     
class Segments(Handler):
      """
       Segments handler behaves in the way that you can construct multi-function "view"
      """
      def respond(self, *args, **kwargs):
          segment = kwargs.pop('segment')
          f = 'segment_%s' % segment
          if hasattr(self, f):
             return getattr(self, f)(*args, **kwargs)
         
         
class Angular(Handler):
    
     # angular handles data differently, `respond` method can return value and that value will be force-set into self.data
    
      def get(self, *args, **kwargs):
        data = self.respond(*args, **kwargs)
        if data:
           self.data['data'] = data
        
      def post(self, *args, **kwargs):
        data = self.respond(*args, **kwargs)
        if data:
           self.data['data'] = data
 
      def after(self):
          force_ajax = self.request.get('force_ajax')
          if (self.request.headers.get('X-Requested-With', '').lower() ==  'xmlhttprequest') or force_ajax:
             if not self.data:
                self.data = {}
                if self.response.status == 200:
                   self.response.status = 204
             self.send_json(self.data)
             return
          else:
            # always return the index.html rendering as init
            self.template['initdata'] = self.data
            self.render('angular/index.html')
          
          
class AngularSegments(Segments, Angular):
      pass
