# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import json
import webapp2

from jinja2 import FileSystemLoader

from webapp2_extras import sessions, jinja2

from app import settings
from app.util import import_module, logger
 
from webclient import webclient_settings
from webclient.util import JSONEncoderHTML, Jinja

_WSGI_CONFIG = None
 
def wsgi_config(as_tuple=False):
    
    global _WSGI_CONFIG
    
    if _WSGI_CONFIG:
       if not as_tuple:
          return _WSGI_CONFIG
       return tuple(_WSGI_CONFIG.items())
 
    ROUTES = []
   
    TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)
      
    for a in webclient_settings.ACTIVE_CONTROLLERS:
        module_manifest = import_module('webclient.controllers.%s' % a)
        if module_manifest:
            routes = getattr(module_manifest, 'ROUTES', None)
            if routes:
               ROUTES += routes
                
    JINJA_FILTERS = Jinja.filters
    JINJA_GLOBALS = Jinja.globals         
    # It won't change, so convert it to a tuple to save memory.           
    ROUTES = tuple(ROUTES)       
    JINJA_GLOBALS.update({'uri_for' : webapp2.uri_for, 'ROUTES' : ROUTES, 'settings' : settings, 'webclient_settings' : webclient_settings})
    TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_DIRS)
    
    logger('Webapp2 started, compiling stuff')
    
    JINJA_CONFIG = {}
    JINJA_CONFIG.update(webclient_settings.WEBAPP2_EXTRAS)
    JINJA_CONFIG['webapp2_extras.jinja2'] = {
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
     
    
    _WSGI_CONFIG = dict(JINJA_CONFIG=JINJA_CONFIG,
                        ROUTES=ROUTES,
                        JINJA_GLOBALS=JINJA_GLOBALS,
                        JINJA_FILTERS=JINJA_FILTERS,
                        TEMPLATE_DIRS=TEMPLATE_DIRS,
                        TEMPLATE_LOADER=TEMPLATE_LOADER
                       )
    if not as_tuple:
       return _WSGI_CONFIG
    else:
       return tuple(_WSGI_CONFIG.items())
 

class Handler(webapp2.RequestHandler):
    
    """
    General-purpose handler that comes with:
    self.session for session access
    self.template to send variables to render template
    and other hooks like `after`, `before` etc.
    
    """
    
    _USE_SESSION = True
    
    template = {'base' : 'index.html'}
 
     
    def send_json(self, data):
        ent = 'application/json;charset=utf-8'
        if self.response.headers.get('Content-Type') != ent:
           self.response.headers['Content-Type'] = ent
        self.response.write(json.dumps(data, cls=JSONEncoderHTML))
     
    def is_post(self):
        """
        Checks if current request is post method
        """
        return self.request.method == 'POST'
    
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
    
    def before_before(self):
        """
        This function fires even before the session init
        """
        pass
    
    def after_after(self):
        """
        This function fires after all executions are done
        """
        pass
    
    def before(self):
        """
        This function is fired just before the handler, usefull for setting variables
        """
        pass
    
    def after(self):
        """
        This function is fired just after the handler is executed
        """
        pass
    
    def get(self, *args, **kwargs):
        self.respond(*args, **kwargs)
        
    def post(self, *args, **kwargs):
        self.respond(*args, **kwargs)
        
    def respond(self, *args, **kwargs):
        self.abort(404)
        self.response.write('<h1>404 Not found</h1>')
 
    def dispatch(self):
        
        self.before_before()
  
        if self._USE_SESSION:
            # Get a session store for this request.
            # request=self.request
            self.session_store = sessions.get_store()
            
        self.before()

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
            
            self.after()
            
        finally:
            # Save all sessions.
            if self._USE_SESSION:
               self.session_store.save_sessions(self.response)
            self.after_after()

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(backend=webclient_settings.SESSION_STORAGE)
     
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
      
      data = {}
      
      def dispatch(self):  
          self.data = {}
          super(Angular, self).dispatch()
           
      def angular_redirect(self, *args, **kwargs):
          self.data['redirect'] = self.uri_for(*args, **kwargs)
     
      def after(self):
          if self.request.headers.get('X-Requested-With', '').lower() ==  'xmlhttprequest':
             if not self.data:
                self.data = {}
                if self.response.status == 200:
                   self.response.status = 204
             self.send_json(self.data)
             return
         
          self.render('angular/index.html', {'initdata' : self.data})
          
          
class AngularSegments(Segments, Angular):
      pass
