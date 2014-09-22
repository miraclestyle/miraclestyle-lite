# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import webapp2
from webapp2_extras import jinja2

from backend import http
from frontend import frontend_settings

def _static_dir(file_path):
  return '/frontend/static/%s' % file_path
 

frontend_settings.JINJA_FILTERS['to_json'] = http.json_output
frontend_settings.JINJA_GLOBALS.update({'static_dir': _static_dir, 
                                        'frontend_settings': frontend_settings})

class Handler(http.BaseRequestHandler):
  
  '''General-purpose handler from which all other frontend handlers must derrive from.'''
 
  def __init__(self, *args, **kwargs):
    super(Handler, self).__init__(*args, **kwargs)
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
 
         
class Blank(Handler):
  
  '''Blank response base class'''
  
  def respond(self, *args, **kwargs):
    pass
  
  
class Angular(Handler):
  
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