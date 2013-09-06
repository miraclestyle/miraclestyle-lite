# -*- coding: utf-8 -*-
'''
Created on Jul 12, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

import webapp2
import six
import os
import sys
import logging
import json
 
from jinja2 import FileSystemLoader

from app import settings

"""
 Systemic helper functions that are more python-related in their nature
"""

class JSONEncoderForHTML(json.JSONEncoder):
    """An encoder that produces JSON safe to embed in HTML.

    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.
    """
  
    def iterencode(self, o, _one_shot=False):
        chunks = super(JSONEncoderForHTML, self).iterencode(o, _one_shot)
        for chunk in chunks:
            chunk = chunk.replace('&', '\\u0026')
            chunk = chunk.replace('<', '\\u003c')
            chunk = chunk.replace('>', '\\u003e')
            yield chunk
 

def logger(msg, t=None):
    if t == None:
       t = 'info'
       
    if settings.DO_LOGS:
       getattr(logging, t)(msg)
 

def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in range(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                              "package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]

def module_exists(module_name):
    try:
       logger('Loading module: ' + module_name)
       module = import_module(module_name)
    except ImportError:
        return False
    else:
        return module
    

_BOOT_CONFIG = None
  
def boot(as_tuple=False):
    
    global _BOOT_CONFIG
    
    if _BOOT_CONFIG:
       if not as_tuple:
          return _BOOT_CONFIG
       return tuple(_BOOT_CONFIG.items())
    
     
    """
      Main boot, consists of loading urls.py from every installed application, and builds theme file paths
    """
    
    if not six.PY3:
        fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
      
    ROUTES = []
    JINJA_FILTERS = {}
    JINJA_GLOBALS = {}
    TEMPLATE_DIRS = []
      
    for a in settings.APPLICATIONS_INSTALLED:
        import_module('%s.%s' % (a, 'models')) # import all models for ndb mapper
        module_manifest = import_module('%s.%s' % (a, 'manifest'))
        if module_manifest:
            template_dir = os.path.join(os.path.dirname(module_manifest.__file__), 'templates')
            if os.path.isdir(template_dir):
               if not six.PY3:
                  template_dir = template_dir.decode(fs_encoding)
               TEMPLATE_DIRS.append(template_dir)
               
            routes = getattr(module_manifest, 'ROUTES', None)
            filters = getattr(module_manifest, 'JINJA_FILTERS', None)
            jinja_globals = getattr(module_manifest, 'JINJA_GLOBALS', None)
            
            if jinja_globals:
               for g in jinja_globals:
                   JINJA_GLOBALS[g[0]] = g[1]
            
            if filters:
               for f in filters:
                   if isinstance(f, dict):
                      JINJA_FILTERS[f['name']] = f['filter']
                   elif callable(f):
                      JINJA_FILTERS[f.__name__] = f
                   elif isinstance(f, tuple):
                      JINJA_FILTERS[f[0]] = f[1]
            
            if routes:
               ROUTES += routes
                
               
    # It won't change, so convert it to a tuple to save memory.           
    ROUTES = tuple(ROUTES)       
    TEMPLATE_DIRS = tuple(TEMPLATE_DIRS)
    JINJA_GLOBALS.update({'uri_for' : webapp2.uri_for, 'ROUTES' : ROUTES, 'settings' : settings})
    TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_DIRS)
    
    logger('Webapp2 started, compiling stuff')
    
    JINJA_CONFIG = {}
    JINJA_CONFIG.update(settings.WEBAPP2_EXTRAS)
    JINJA_CONFIG['webapp2_extras.jinja2'] = {
                 'template_path': 'templates',
                 'globals' : JINJA_GLOBALS,
                 'filters' : JINJA_FILTERS,
                 'environment_args': {
                   'extensions': ['jinja2.ext.i18n', 'jinja2.ext.autoescape', 'jinja2.ext.loopcontrols'],
                   'autoescape' : True, 
                   'loader' : TEMPLATE_LOADER,
                   'cache_size' : settings.TEMPLATE_CACHE
         }
    }
    
    _BOOT_CONFIG = dict(JINJA_CONFIG=JINJA_CONFIG,
                        ROUTES=ROUTES,
                        JINJA_GLOBALS=JINJA_GLOBALS,
                        JINJA_FILTERS=JINJA_FILTERS,
                        TEMPLATE_DIRS=TEMPLATE_DIRS,
                        TEMPLATE_LOADER=TEMPLATE_LOADER
                       )
    if not as_tuple:
       return _BOOT_CONFIG
    else:
       return tuple(_BOOT_CONFIG.items())