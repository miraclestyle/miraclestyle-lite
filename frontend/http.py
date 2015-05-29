# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import webapp2
import importlib
import settings
import json
import re

from jinja2 import Environment, evalcontextfilter, Markup, escape, FileSystemLoader


TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)
TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_DIRS)  
 
settings.JINJA_GLOBALS.update({'uri_for' : webapp2.uri_for, 'ROUTES' : settings.ROUTES, 'settings' : settings})
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