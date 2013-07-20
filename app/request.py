# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import webapp2
import time

from webapp2_extras.i18n import _
from webapp2_extras import sessions, i18n, jinja2

from app import settings
 
class Handler(webapp2.RequestHandler):
    
    _USE_SESSION = True
    _LOAD_TRANSLATIONS = True
    
    _common = {'base' : 'index.html'}
    
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
        self._common.update(data)
        return self.render_response(tpl, **self._common)
    
    def before_before(self):
        pass
    
    def after_after(self):
        pass
    
    def before(self):
        pass
    
    def after(self):
        pass
    
    def get(self, *args, **kwargs):
        self.respond(*args, **kwargs)
        
    def post(self, *args, **kwargs):
        self.respond(*args, **kwargs)
        
    def respond(self, *args, **kwargs):
        self.abort(404)
        self.response.write(_('Not found'))
 
    def dispatch(self):
        
        self.before_before()

        if self._LOAD_TRANSLATIONS:
            i18n.get_i18n().set_locale('en_US')
      
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
        return self.session_store.get_session(backend=settings.SESSION_STORAGE)
    
    
class Segments(Handler):
  
      def respond(self, *args, **kwargs):
          segment = kwargs.pop('segment')
          f = 'segment_%s' % segment
          if hasattr(self, f):
             return getattr(self, f)(*args, **kwargs)