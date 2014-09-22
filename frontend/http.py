# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import webapp2
import importlib

from jinja2 import FileSystemLoader
 
from backend import settings
from frontend import frontend_settings

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'template'),)
TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_DIRS)  
 
frontend_settings.JINJA_GLOBALS.update({'uri_for' : webapp2.uri_for, 'ROUTES' : frontend_settings.ROUTES, 'settings' : settings, 'frontend_settings' : frontend_settings})

for a in frontend_settings.ACTIVE_CONTROLLERS:
  importlib.import_module('frontend.handler.%s' % a)
    
frontend_settings.ROUTES[:] = map(lambda args: webapp2.Route(*args), frontend_settings.ROUTES)
   
wsgi_config = {}
wsgi_config['webapp2_extras.jinja2'] = {
               'template_path': 'templates',
               'globals' : frontend_settings.JINJA_GLOBALS,
               'filters' : frontend_settings.JINJA_FILTERS,
               'environment_args': {
                 'extensions': ['jinja2.ext.autoescape', 'jinja2.ext.loopcontrols'],
                 'autoescape' : True, 
                 'loader' : TEMPLATE_LOADER,
                 'cache_size' : frontend_settings.TEMPLATE_CACHE
       }
}
app = webapp2.WSGIApplication(frontend_settings.ROUTES, debug=frontend_settings.DEBUG, config=wsgi_config)