# -*- coding: utf-8 -*-

'''
Created on Oct 15, 2012

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module wsgi.py

'''
import webapp2

from app import settings
from webclient.utils import boot
  
load = boot()
app = webapp2.WSGIApplication(load['ROUTES'], debug=settings.DEBUG, config=load['JINJA_CONFIG'])