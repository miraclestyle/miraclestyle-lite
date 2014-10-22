# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import os
import webapp2
import codecs
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
  return '%s/client/static/%s' % (settings.HOST, file_path)

def _angular_include_template(path):
  return codecs.open(os.path.join(settings.ROOT_DIR, 'templates/angular/parts', path), 'r', 'utf-8').read()
 
settings.JINJA_GLOBALS.update({'static_dir': _static_dir, 
                               'settings': settings,
                               'len': len,
                               'angular_include_template': _angular_include_template})

settings.JINJA_FILTERS.update({'to_json': to_json, 'static_dir': _static_dir})

class RequestHandler(webapp2.RequestHandler):
  '''General-purpose handler from which all other frontend handlers must derrive from.'''
 
  def __init__(self, *args, **kwargs):
    super(RequestHandler, self).__init__(*args, **kwargs)
    self.data = {}
    self.template = {}
  
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
      
  def dispatch(self):
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