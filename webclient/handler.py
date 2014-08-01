# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import json
import webapp2
import importlib
  
from jinja2 import FileSystemLoader
from webapp2_extras import jinja2

from app import orm, settings, util, mem

from webclient import webclient_settings
from webclient.util import JSONEncoderHTML, JINJA_GLOBALS, JINJA_FILTERS

from webapp2 import Route

__ROUTES = []

class InvalidRouteError(Exception):
      pass
  
  
class AngularRoute(Route):
    
  """
  Angular compatible route
  """
  
  angular_path = None
  angular_controller = None
  angular_template = None
  angular_config = {}
  
  def _angular_make_path(self, p):
    p = p.replace('<', ':')
    p = p.replace('>', '')
    return p
  
  def _angular_make_controller(self, c):
    if not isinstance(c, basestring):
        c = c.__name__
    li = c.split('.')
    li_last = li[-1]
    del li[-1]
    co = [k.title() for k in li]
    co.append(li_last)
    return u"".join(co)
    
  def __init__(self, template, handler=None, name=None, angular_template=False, angular_config={}, build_only=False):
    """Initializes this route."""
    super(AngularRoute, self).__init__(template, handler, name, build_only)
    
    self.angular_config = angular_config
    self.angular_path = self._angular_make_path(template)
    self.angular_controller = self._angular_make_controller(handler)
    self.angular_template = angular_template
        
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
        arg = AngularRoute(*arg)
    if isinstance(arg, dict):
        if prefix:
           arg['handler'] = '%s.%s' % (prefix, arg['handler'])
        arg = AngularRoute(**arg)
    if not isinstance(arg, AngularRoute):
       raise InvalidRouteError
    __ROUTES.append(arg)
  return __ROUTES

 
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
  if not as_tuple:
     return __WSGI_CONFIG
  else:
     return tuple(__WSGI_CONFIG.items())
   
class Base(webapp2.RequestHandler):
  
  """
  General-purpose handler that comes with:
  self.template to send variables to render template
  and other hooks like `after`, `before` etc.
  
  """
  LOAD_CURRENT_USER = True
  
  def __init__(self, *args, **kwargs):
    super(Base, self).__init__(*args, **kwargs)
    self.data = {}
    self.template = {}
  
  def get_input(self):
    special = '__body__'
    try:
      dicts = json.loads(self.request.body)
    except:
      if self.request.get(special):
        dicts = json.loads(self.request.get(special))
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
  
  def initialize(self, request, response):
    super(Base, self).initialize(request, response)
      
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
    pass
   
  def after(self):
    """
    This function is fired just after the handler is executed
    """
    pass
  
  @orm.toplevel
  def get(self, *args, **kwargs):
    return self.respond(*args, **kwargs)
      
  @orm.toplevel    
  def post(self, *args, **kwargs):
    return self.respond(*args, **kwargs)
       
  def respond(self, *args, **kwargs):
    self.abort(404)
    self.response.write('<h1>404 Not found</h1>')
  
  def dispatch(self):
    csrf = None
    csrf_cookie_value = self.request.cookies.get(webclient_settings.COOKIE_CSRF_KEY)
    if self.LOAD_CURRENT_USER:
      from app.models import auth
      auth.User.login_from_authorization_code(self.request.cookies.get(webclient_settings.COOKIE_USER_KEY))
      current_user = auth.User.current_user()
      current_user.set_taskqueue(self.request.headers.get('X-AppEngine-QueueName', None) != None) # https://developers.google.com/appengine/docs/python/taskqueue/overview-push#Python_Task_request_headers
      current_user.set_cron(self.request.headers.get('X-Appengine-Cron', None) != None) # https://developers.google.com/appengine/docs/python/config/cron#Python_app_yaml_Securing_URLs_for_cron
      csrf = current_user._csrf
      self.template['current_user'] = current_user
    if not csrf_cookie_value:
     if csrf == None:
       csrf = util.random_chars(32)
     self.response.set_cookie(webclient_settings.COOKIE_CSRF_KEY, csrf)
    try:
      self.before()
      # Dispatch the request.
      super(Base, self).dispatch()
      self.after()
    finally:
      # support our memcache wrapper lib temporary variables, and release them upon request complete
      mem._local.__release_local__()
         
         
class Blank(Base):
  
  def respond(self, *args, **kwargs):
    pass
     
     
class Segments(Base):
  """
   Segments handler behaves in the way that you can construct multi-function "view"
  """
  def respond(self, *args, **kwargs):
    segment = kwargs.pop('segment')
    f = 'segment_%s' % segment
    if hasattr(self, f):
       return getattr(self, f)(*args, **kwargs)
         
         
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
          
          
class AngularSegments(Segments, Angular):
  pass


class AngularBlank(Angular):
  
  def respond(self, *args, **kwargs):
    pass
  