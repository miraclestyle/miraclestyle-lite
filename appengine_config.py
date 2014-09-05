# -*- coding: utf-8 -*-
'''
Created on Jul 18, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
def webapp_add_wsgi_middleware(app):
  from google.appengine.ext.appstats import recording
  app = recording.appstats_wsgi_middleware(app)
  return app