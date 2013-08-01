# -*- coding: utf-8 -*-

'''
Created on Oct 15, 2012

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module wsgi.py

'''
import webapp2
import six
import os
import sys


from jinja2 import FileSystemLoader
 
from app.core import import_module, logger
from app import settings

if not six.PY3:
    fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
  
ROUTES = []
app_template_dirs = []
  
for a in settings.APPLICATIONS_INSTALLED:
    module_urls = import_module('%s.%s' % (a, 'urls'))
    module_models = import_module('%s.%s' % (a, 'models'))
    if module_urls:
        template_dir = os.path.join(os.path.dirname(module_urls.__file__), 'templates')
        if os.path.isdir(template_dir):
           if not six.PY3:
              template_dir = template_dir.decode(fs_encoding)
           app_template_dirs.append(template_dir)
        
        patts = None
        patts = getattr(module_urls, 'ROUTES')
        if patts:
           ROUTES += patts
            
           
# It won't change, so convert it to a tuple to save memory.           
ROUTES = tuple(ROUTES)       
app_template_dirs = tuple(app_template_dirs)   

logger('Webapp2 started')

config = {}
config.update(settings.WEBAPP2_EXTRAS)
config['webapp2_extras.jinja2'] = {
             'template_path': 'templates',
             'globals' : {'uri_for' : webapp2.uri_for, 'settings' : settings},
             'environment_args': { 
               'extensions': ['jinja2.ext.i18n'],
               'autoescape' : True, 
               'loader' : FileSystemLoader(app_template_dirs),
               'cache_size' : settings.TEMPLATE_CACHE
     }
}   
app = webapp2.WSGIApplication(ROUTES, debug=settings.DEBUG, config=config)