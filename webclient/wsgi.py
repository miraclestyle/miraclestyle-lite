# -*- coding: utf-8 -*-

'''
Created on Oct 15, 2012

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module wsgi.py

'''
import webapp2

from app import settings

from webclient.handler import wsgi_config
  
cfg = wsgi_config()
app = webapp2.WSGIApplication(cfg['ROUTES'], debug=settings.DEBUG, config=cfg['JINJA_CONFIG'])