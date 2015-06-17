# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import os
import webapp2
import codecs
import re
import api
from webapp2_extras import jinja2
from google.appengine.api import urlfetch

from jinja2 import evalcontextfilter, Markup, escape

import settings
import api


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
  return '%s/client/%s' % (settings.HOST_URL, file_path)


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
    self.template['base_url'] = self.request.host_url
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
    if data is None:
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
    if (self.request.headers.get('X-Requested-With', '').lower() == 'xmlhttprequest'):
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


class SeoOrAngular(AngularBlank):

  out = None

  @property
  def is_seo(self):
    agent = self.request.headers.get('User-Agent')
    if agent:
      return re.search('(bot|crawl|slurp|spider|facebook|twitter|pinterest|linkedin)', agent) or self.request.cookies.get('seo') == '1'
    return False

  def respond_angular(self, *args, **kwargs):
    return super(SeoOrAngular, self).respond(*args, **kwargs)

  def respond(self, *args, **kwargs):
    if not self.is_seo:
      return self.respond_angular(*args, **kwargs)
    else:
      return self.respond_seo(*args, **kwargs)

  def respond_seo(self, *args, **kargs):
    self.abort(404)

  def api_endpoint(self, *args, **kwargs):
    response = api.endpoint(*args, **kwargs)
    if 'errors' in response:
      self.abort(503, response['errors'])
    return response

  def after(self):
    if not self.is_seo:
      super(SeoOrAngular, self).after()


settings.JINJA_GLOBALS.update({'uri_for': webapp2.uri_for, 'ROUTES': settings.ROUTES, 'settings': settings})
settings.JINJA_FILTERS.update({'json': lambda x: json.dumps(x, indent=2)})

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@evalcontextfilter
def nl2br(eval_ctx, value):
  result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n')
                        for p in _paragraph_re.split(escape(value)))
  if eval_ctx.autoescape:
    result = Markup(result)
  return result


@evalcontextfilter
def keywords(eval_ctx, value):
  return ','.join(unicode(value).lower().split(' '))

settings.JINJA_FILTERS['nl2br'] = nl2br
settings.JINJA_FILTERS['keywords'] = keywords
