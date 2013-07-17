# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import webapp2
from webapp2_extras import sessions, i18n

from app import settings
from app.template import render_template
 
class Handler(webapp2.RequestHandler):
    
    _USE_SESSION = True
    _LOAD_TRANSLATIONS = False
    
    _common = {}
  
    def render(self, tpl, data=None):
        return self.response.write(render_template(tpl, data))
    
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
        self.response.write('Not found')
 
    def dispatch(self):
        
        self.before()

        if self._LOAD_TRANSLATIONS:
            locale = 'en_US'
            i18n.get_i18n().set_locale(locale)
      
        if self._USE_SESSION:
            # Get a session store for this request.
            # request=self.request
            self.session_store = sessions.get_store()

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            if self._USE_SESSION:
               self.session_store.save_sessions(self.response)
            self.after()

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