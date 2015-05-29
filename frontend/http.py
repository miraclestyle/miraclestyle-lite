# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import webapp2
import importlib
import settings
from jinja2 import FileSystemLoader


TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)
TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_DIRS)  


for a in settings.ACTIVE_HANDLERS:
  importlib.import_module('handler.%s' % a)
    
settings.ROUTES[:] = map(lambda args: webapp2.Route(*args), settings.ROUTES)
   
wsgi_config = {}
wsgi_config['webapp2_extras.jinja2'] = {
               'template_path': 'templates',
               'globals' : settings.JINJA_GLOBALS,
               'filters' : settings.JINJA_FILTERS,
               'environment_args': {
                 'extensions': ['jinja2.ext.autoescape', 'jinja2.ext.loopcontrols'],
                 'autoescape' : True, 
                 'loader' : TEMPLATE_LOADER,
                 'cache_size' : settings.TEMPLATE_CACHE
       }
}
app = webapp2.WSGIApplication(settings.ROUTES, debug=settings.DEBUG, config=wsgi_config)