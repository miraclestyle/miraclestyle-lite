# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import webapp2
from webapp2_extras import jinja2

from google.appengine.api import urlfetch

import settings, api

class JSONEncoder(json.JSONEncoder):

  def iterencode(self, o, _one_shot=False):
    chunks = super(JSONEncoder, self).iterencode(o, _one_shot)
    for chunk in chunks:
      chunk = chunk.replace('&', '\\u0026')
      chunk = chunk.replace('<', '\\u003c')
      chunk = chunk.replace('>', '\\u003e')
      yield chunk
      
def to_json(s, **kwds):
  kwds['cls'] = JSONEncoder
  return json.dumps(s, **kwds)

def _static_dir(file_path):
  return '/frontend/static/%s' % file_path
 
settings.JINJA_GLOBALS.update({'static_dir': _static_dir, 
                               'settings': settings})

settings.JINJA_FILTERS.update({'to_json': to_json})

class RequestHandler(webapp2.RequestHandler):
  
  autoload_current_account = True
  autoload_model_meta = True
  
  '''General-purpose handler from which all other frontend handlers must derrive from.'''
 
  def __init__(self, *args, **kwargs):
    super(RequestHandler, self).__init__(*args, **kwargs)
    self.data = {}
    self.template = {}
    self.current_account = None
    self.current_model_meta = None
  
  def send_json(self, data):
    ''' sends `data` to be serialized in json format, and sets content type application/json utf8'''
    ent = 'application/json;charset=utf-8'
    if self.response.headers.get('Content-Type') != ent:
       self.response.headers['Content-Type'] = ent
    self.response.write(json.dumps(data))
  
  def before(self):
    '''
    This function is fired just before the handler logic is executed
    '''
    pass
  
  def after(self):
    '''
    This function is fired just after the handler is executed
    '''
    pass
  
  def get(self, *args, **kwargs):
    return self.respond(*args, **kwargs)
  
  def post(self, *args, **kwargs):
    return self.respond(*args, **kwargs)
  
  def respond(self, *args, **kwargs):
    self.abort(404)
    self.response.write('<h1>404 Not found</h1>')
    
  def autoloads(self):
    ''' Loads current user from backend '''
    if self.current_account is None and self.autoload_current_account:
      self.current_account = api.endpoint(payload={'action_id': 'current_account', 'action_model': '11'},
                                          headers=self.request.headers)
      self.template['current_account'] = self.current_account['entity']
      
    if self.current_model_meta is None and self.autoload_model_meta:
      self.current_model_meta = api.model_meta()
      self.template['current_model_meta'] = self.current_model_meta
      
  def dispatch(self):
    self.autoloads()
    try:
      self.before()
      super(RequestHandler, self).dispatch()
      self.after()
    finally:
      pass
  
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
 
         
class Blank(RequestHandler):
  
  '''Blank response base class'''
  
  def respond(self, *args, **kwargs):
    pass
  
  
class Angular(RequestHandler):
  
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