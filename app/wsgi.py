# -*- coding: utf-8 -*-

'''
Created on Oct 15, 2012

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module wsgi.py

'''
import logging
import webapp2
 
from app.core import import_module
from app import settings
 
ROUTES = []
  
for a in settings.APPLICATIONS_INSTALLED:
    module_urls = import_module('%s.%s' % (a, 'urls'))
    patts = None
    if module_urls:
        patts = getattr(module_urls, 'ROUTES')
        if patts:
           ROUTES += patts
            
           
# It won't change, so convert it to a tuple to save memory.           
ROUTES = tuple(ROUTES)

logging.info('Webapp2 started')

config = {}
config.update(settings.WEBAPP2_EXTRAS)

app = webapp2.WSGIApplication(ROUTES, debug=settings.DEBUG, config=config)