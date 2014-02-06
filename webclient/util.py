# -*- coding: utf-8 -*-
'''
Created on Oct 8, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import imp
import os
import json

from app import ndb

JINJA_FILTERS = {}
JINJA_GLOBALS = {}

def register_filter(name, funct):
  
    global JINJA_FILTERS
    
    JINJA_FILTERS[name] = funct
    
def register_global(name, value):
  
    global JINJA_GLOBALS
    
    JINJA_GLOBALS[name] = value
        
def to_json(s):
    return json.dumps(s, indent=2, cls=JSONEncoderHTML)
            
register_filter('to_json', to_json)
 
class JSONEncoderHTML(json.JSONEncoder):
    """An encoder that produces JSON safe to embed in HTML.

    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.
    """
    
    def default(self, o):
        
        if isinstance(o, ndb.Key):
           return o.urlsafe()
        
        if hasattr(o, '__todict__'):
           return o.__todict__()
        else:
           if hasattr(o, '__str__'):
              return o.__str__()
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