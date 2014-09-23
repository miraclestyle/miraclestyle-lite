# -*- coding: utf-8 -*-
'''
Created on Sep 22, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import webapp2
import settings
import importlib

for a in settings.HTTP_ACTIVE_HANDLERS:
  importlib.import_module('handler.%s' % a) # import every handler and register its routes and all configs

settings.HTTP_ROUTES[:] = map(lambda args: webapp2.Route(*args), settings.HTTP_ROUTES)

# expose app to app.yaml
app = webapp2.WSGIApplication(settings.HTTP_ROUTES, debug=settings.DEBUG)