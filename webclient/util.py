# -*- coding: utf-8 -*-
'''
Created on Oct 8, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import imp
import os
import json
import datetime

from google.appengine.api import datastore_types
from app import orm, settings
from webclient import webclient_settings

JINJA_FILTERS = {}
JINJA_GLOBALS = {}

def register_filter(name, funct):
  
    global JINJA_FILTERS
    
    JINJA_FILTERS[name] = funct
    
def register_global(name, value):
  
    global JINJA_GLOBALS
    
    JINJA_GLOBALS[name] = value
        
def to_json(s, **kwargs):
    defaults = {'indent': 2, 'check_circular': False, 'cls': JSONEncoderHTML}
    defaults.update(kwargs)
    return json.dumps(s, **defaults)
  
def static_dir(file_path):
    return '/webclient/static/%s' % file_path
            
register_filter('to_json', to_json)
register_global('static_dir', static_dir)
register_global('webclient_settings', webclient_settings)

class JSONEncoderHTML(json.JSONEncoder):
    """An encoder that produces JSON safe to embed in HTML.

    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.
    
    Also its `default` function will properly format data that is usually not serialized by json standard.
    """
    
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
        chunks = super(JSONEncoderHTML, self).iterencode(o, _one_shot)
        for chunk in chunks:
            chunk = chunk.replace('&', '\\u0026')
            chunk = chunk.replace('<', '\\u003c')
            chunk = chunk.replace('>', '\\u003e')
            yield chunk
            

MODULE_EXTENSIONS = ('.py',)

def package_contents(package_name):
    file, pathname, description = imp.find_module(package_name)
    if file:
        raise ImportError('Not a package: %r', package_name)
    # Use a set because some may be both source and compiled.
    return set([os.path.splitext(module)[0]
        for module in os.listdir(pathname)
        if module.endswith(MODULE_EXTENSIONS)])