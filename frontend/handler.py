# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import webapp2
import importlib

from jinja2 import FileSystemLoader
from webapp2_extras import jinja2

from backend import settings, util, http
from frontend import frontend_settings

  
JINJA_FILTERS = {}
JINJA_GLOBALS = {}
__WSGI_CONFIG = None
 
 
class InvalidRouteError(Exception):
      pass


def register_filter(name, funct=None):
  global JINJA_FILTERS
  if isinstance(name, dict):
    JINJA_FILTERS.update(name)
  else:
    JINJA_FILTERS[name] = funct
    
    
def register_global(name, value=None):
  global JINJA_GLOBALS
  if isinstance(name, dict):
    JINJA_GLOBALS.update(name)
  else:
    JINJA_GLOBALS[name] = value
  
  
def _static_dir(file_path):
  return '/frontend/static/%s' % file_path
            
            
register_filter('to_json', http.json_output)
register_global({'static_dir': _static_dir, 
                 'frontend_settings': frontend_settings})
 
 
def get_wsgi_config():
    
  '''Config for wsgi instance. Prepares all variables and routes for webapp2 WSGI constructor'''
  
  global __WSGI_CONFIG
  
  if __WSGI_CONFIG is not None:
    return __WSGI_CONFIG
  
  TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'template'),)
    
  for a in frontend_settings.ACTIVE_CONTROLLERS:
      importlib.import_module('frontend.controller.%s' % a)
      
  frontend_settings.ROUTES[:] = map(lambda args: webapp2.Route(*args), frontend_settings.ROUTES)
  
  JINJA_GLOBALS.update({'uri_for' : webapp2.uri_for, 'ROUTES' : frontend_settings.ROUTES, 'settings' : settings, 'frontend_settings' : frontend_settings})
  TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_DIRS)
  
  util.log('Webapp2 started, compiling stuff')
  
  WSGI_CONFIG = {}
  WSGI_CONFIG.update(frontend_settings.WEBAPP2_EXTRAS)
  WSGI_CONFIG['webapp2_extras.jinja2'] = {
               'template_path': 'templates',
               'globals' : JINJA_GLOBALS,
               'filters' : JINJA_FILTERS,
               'environment_args': {
                 'extensions': ['jinja2.ext.autoescape', 'jinja2.ext.loopcontrols'],
                 'autoescape' : True, 
                 'loader' : TEMPLATE_LOADER,
                 'cache_size' : frontend_settings.TEMPLATE_CACHE
       }
  }
    
  __WSGI_CONFIG = dict(WSGI_CONFIG=WSGI_CONFIG,
                      ROUTES=frontend_settings.ROUTES,
                      JINJA_GLOBALS=JINJA_GLOBALS,
                      JINJA_FILTERS=JINJA_FILTERS,
                      TEMPLATE_DIRS=TEMPLATE_DIRS,
                      TEMPLATE_LOADER=TEMPLATE_LOADER
                     )
  return __WSGI_CONFIG
   
   
class Base(http.BaseRequestHandler):
  
  '''General-purpose handler from which all other frontend handlers must derrive from.'''
 
  def __init__(self, *args, **kwargs):
    super(Base, self).__init__(*args, **kwargs)
    self.data = {}
    self.template = {}
  
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
    self.template['current_account'] = self.current_account
 
         
class Blank(Base):
  
  '''Blank response base class'''
  
  def respond(self, *args, **kwargs):
    pass
  
  
class Angular(Base):
  
  '''Angular subclass of base handler'''  
  
  base_template = 'angular/index.html'
  
  def get(self, *args, **kwargs):
    data = self.respond(*args, **kwargs)
    if data:
       self.data = data
    
  def post(self, *args, **kwargs):
    data = self.respond(*args, **kwargs)
    if data:
       self.data = data
  
  def after(self):
    if (self.request.headers.get('X-Requested-With', '').lower() ==  'xmlhttprequest'):
       if not self.data:
          self.data = {}
          if self.response.status == 200:
             self.response.status = 204
       self.send_json(self.data)
       return
    else:
      # always return the index.html rendering as init
      self.render(self.base_template)
 
 
class AngularBlank(Angular):
  
  '''Same as Blank, but for angular'''
  
  def respond(self, *args, **kwargs):
    pass