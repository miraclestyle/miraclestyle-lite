# -*- coding: utf-8 -*-

'''
Created on Oct 15, 2012

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module wsgi.py

'''
import webapp2

from frontend import frontend_settings
from frontend.handler import get_wsgi_config
  
cfg = get_wsgi_config()
app = webapp2.WSGIApplication(cfg['ROUTES'], debug=frontend_settings.DEBUG, config=cfg['WSGI_CONFIG'])