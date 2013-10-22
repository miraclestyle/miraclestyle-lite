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

from app.memcache import _local
from app import settings, core
from app.util import import_module, logger
 
from webclient import webclient_settings
from webclient.util import JSONEncoderHTML, Jinja
from webclient.route import get_routes

_WSGI_CONFIG = None
 
def wsgi_config(as_tuple=False):
    
    """ Config function. Prepares all variables and routes for webapp2 WSGI startup """
    
    global _WSGI_CONFIG
    
    if _WSGI_CONFIG:
       if not as_tuple:
          return _WSGI_CONFIG
       return tuple(_WSGI_CONFIG.items())
  
    TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)
      
    for a in webclient_settings.ACTIVE_CONTROLLERS:
        import_module('webclient.controllers.%s' % a)
          
    JINJA_FILTERS = Jinja.filters
    JINJA_GLOBALS = Jinja.globals         
    # It won't change, so convert it to a tuple to save memory.   
    ROUTES = tuple(get_routes())
   
    JINJA_GLOBALS.update({'uri_for' : webapp2.uri_for, 'ROUTES' : ROUTES, 'settings' : settings, 'webclient_settings' : webclient_settings})
    TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_DIRS)
    
    logger('Webapp2 started, compiling stuff')
    
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
     
    
    _WSGI_CONFIG = dict(WSGI_CONFIG=WSGI_CONFIG,
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
    self.current_user to retrieve current user from session
    and other hooks like `after`, `before` etc.
    
    """
    
    USE_SESSION = True
 
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        
        self.data = {}
        self._current_user = None
        self.template = {'base' : 'index.html'}
      
    def for_guests(self, where=None):
        """ Does not allow logged in users """
        
        if where is None:
           where = 'index'
          
        if self.current_user is not None:
           self.redirect(self.uri_for(where))
      
    def ask_login(self):
        """ Does not allow guests """
        if self.current_user is None:
           self.redirect(self.uri_for('login'))
            
    def set_current_user(self, usr):
        """ Sets the specified user into session """
        self._current_user = usr
        self.session[webclient_settings.SESSION_USER_KEY] = usr.key
      
    @property
    def current_user(self):
        """ Retrieves the current user from the session, based on session data from the browser """
        k = webclient_settings.SESSION_USER_KEY
        uid = None
        if k in self.session and self._current_user is None:
           uid = self.session.get(k)
           # uid contains serialized ndb.Key of the user
        
        info = dict(key=uid, session_updated=getattr(self.session.container, 'session_updated', None),
                    session_id=getattr(self.session.container, 'sid', None))
        
        self._current_user = core.acl.User.current_user_read(**info)
        return self._current_user
 
            
    def send_json(self, data):
        """ sends `data` to json format, accepts anything json compatible """
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
  
        if self.USE_SESSION:
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
            if self.USE_SESSION:
               self.session_store.save_sessions(self.response)
            self.after_after()
            
            # support the core's locals, and release them upon request complete
            _local.__release_local__()
            
            

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(backend='webclient')
     
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
       
      def angular_redirect(self, *args, **kwargs):
          self.data['redirect'] = self.uri_for(*args, **kwargs)
     
      def after(self):
          if self.request.headers.get('X-Requested-With', '').lower() ==  'xmlhttprequest' or self.request.get('force_ajax'):
             if not self.data:
                self.data = {}
                if self.response.status == 200:
                   self.response.status = 204
             self.send_json(self.data)
             return
         
          self.render('angular/index.html', {'initdata' : self.data})
          
          
class AngularSegments(Segments, Angular):
      pass
