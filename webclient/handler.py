# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import json
import webapp2
import importlib
import datetime
  
from jinja2 import FileSystemLoader
from webapp2 import Route
from webapp2_extras import jinja2

from app import orm, settings, util, mem

from webclient import webclient_settings
 
 
JINJA_FILTERS = {}
JINJA_GLOBALS = {}
__ROUTES = []
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
        
        
def to_json(s, **kwargs):
  '''
    Converter of complex values into json
  '''
  defaults = {'indent': 2, 'check_circular': False, 'cls': JSONEncoderCommunicator}
  defaults.update(kwargs)
  return json.dumps(s, **defaults)
  
  
def _static_dir(file_path):
  return '/webclient/static/%s' % file_path
            
            
register_filter('to_json', to_json)
register_global({'static_dir': _static_dir, 
                 'webclient_settings': webclient_settings})


class JSONEncoderCommunicator(json.JSONEncoder):
    '''An encoder that produces JSON safe to embed in HTML.

    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.
    
    Also its `default` function will properly format data that is usually not serialized by json standard.
    '''
    
    def default(self, o):
      if isinstance(o, datetime.datetime):
         return o.strftime(settings.DATETIME_FORMAT)
      if isinstance(o, orm.Key):
         return o.urlsafe()
      if hasattr(o, 'get_output'):
        try:
          return o.get_output()
        except TypeError as e:
          pass
      if hasattr(o, 'get_meta'):
        try:
         return o.get_meta()
        except TypeError:
         pass
      try:
        out = str(o)
        return out
      except TypeError:
        pass
      return json.JSONEncoder.default(self, o)
  
    def iterencode(self, o, _one_shot=False):
      chunks = super(JSONEncoderCommunicator, self).iterencode(o, _one_shot)
      for chunk in chunks:
        chunk = chunk.replace('&', '\\u0026')
        chunk = chunk.replace('<', '\\u003c')
        chunk = chunk.replace('>', '\\u003e')
        yield chunk

      
def get_routes():
  global __ROUTES
  return __ROUTES        
 
 
def register(*args):
  global __ROUTES
  prefix = None
  for arg in args:
    if isinstance(arg, basestring):
       prefix = arg
       continue
    if isinstance(arg, (list, tuple)):
        if prefix:
          if isinstance(arg, tuple):
             arg = list(arg)
          try:
             arg[1] = '%s.%s' % (prefix, arg[1])
          except KeyError:
             pass
        arg = Route(*arg)
    if isinstance(arg, dict):
      if prefix:
         arg['handler'] = '%s.%s' % (prefix, arg['handler'])
      arg = Route(**arg)
    if not isinstance(arg, Route):
       raise InvalidRouteError
    __ROUTES.append(arg)
  return __ROUTES

 
def get_wsgi_config():
    
  ''' Config function. Prepares all variables and routes for webapp2 WSGI constructor '''
  
  global __WSGI_CONFIG
  
  if __WSGI_CONFIG is not None:
    return __WSGI_CONFIG
  
  TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'template'),)
    
  for a in webclient_settings.ACTIVE_CONTROLLERS:
      importlib.import_module('webclient.controller.%s' % a)
    
  # It won't change, so convert it to a tuple to save memory.   
  ROUTES = tuple(get_routes())
  
  JINJA_GLOBALS.update({'uri_for' : webapp2.uri_for, 'ROUTES' : ROUTES, 'settings' : settings, 'webclient_settings' : webclient_settings})
  TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_DIRS)
  
  util.log('Webapp2 started, compiling stuff')
  
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
  return __WSGI_CONFIG
   
   
class Base(webapp2.RequestHandler):
  
  ''' General-purpose handler from which all other handlers must derrive from. '''
  
  autoload_current_user = True
  
  def __init__(self, *args, **kwargs):
    super(Base, self).__init__(*args, **kwargs)
    self.data = {}
    self.template = {}
  
  def get_input(self):
    special = '__body__'
    try:
      dicts = json.loads(self.request.body)
    except:
      special_data = self.request.get(special)
      if special_data:
        dicts = json.loads(special_data)
      else:
        dicts = {}
    newparams = {}
    for param_key in self.request.params.keys():
      if param_key == special:
        continue
      value = self.request.params.getall(param_key)
      if len(value) == 1:
         value = value[0]
      if param_key in dicts:
        dictval = dicts.get(param_key)
        if isinstance(dictval, list):
          if isinstance(value, list):
            dictval.extend(value)
          else:
            dictval.append(value)
          continue
      newparams[param_key] = value
    dicts.update(newparams)
    return dicts
   
  def send_json(self, data):
    """ sends `data` to json format, accepts anything json compatible """
    ent = 'application/json;charset=utf-8'
    if self.response.headers.get('Content-Type') != ent:
       self.response.headers['Content-Type'] = ent
    self.response.write(to_json(data))
  
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
    from app.models.auth import User
    self.template['current_user'] = User.current_user()
   
  def after(self):
    """
    This function is fired just after the handler is executed
    """
    pass
 
  def get(self, *args, **kwargs):
    return self.respond(*args, **kwargs)
       
  def post(self, *args, **kwargs):
    return self.respond(*args, **kwargs)
       
  def respond(self, *args, **kwargs):
    self.abort(404)
    self.response.write('<h1>404 Not found</h1>')
  
  @orm.toplevel
  def dispatch(self):
    csrf = None
    csrf_cookie_value = self.request.cookies.get(webclient_settings.COOKIE_CSRF_KEY)
    if self.autoload_current_user:
      from app.models.auth import User
      User.set_current_user_from_auth_code(self.request.cookies.get(webclient_settings.COOKIE_USER_KEY))
      current_user = User.current_user()
      current_user.set_taskqueue(self.request.headers.get('X-AppEngine-QueueName', None) != None) # https://developers.google.com/appengine/docs/python/taskqueue/overview-push#Python_Task_request_headers
      current_user.set_cron(self.request.headers.get('X-Appengine-Cron', None) != None) # https://developers.google.com/appengine/docs/python/config/cron#Python_app_yaml_Securing_URLs_for_cron
      csrf = current_user._csrf
    if not csrf_cookie_value:
     if csrf == None:
       csrf = util.random_chars(32)
     self.response.set_cookie(webclient_settings.COOKIE_CSRF_KEY, csrf)
    try:
      self.before()
      super(Base, self).dispatch()
      self.after()
    finally:
      # support our memcache wrapper lib temporary variables, and release them upon request complete
      mem._local.__release_local__()
         
         
class Blank(Base):
  
  def respond(self, *args, **kwargs):
    pass
  
  
class Angular(Base):
    
  # angular handles data differently, `respond` method can return value and that value will be force-set into self.data
  def get(self, *args, **kwargs):
    data = self.respond(*args, **kwargs)
    if data:
       self.data = data
    
  def post(self, *args, **kwargs):
    data = self.respond(*args, **kwargs)
    if data:
       self.data = data
  
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
 
 
class AngularBlank(Angular):
  
  def respond(self, *args, **kwargs):
    pass
  
  