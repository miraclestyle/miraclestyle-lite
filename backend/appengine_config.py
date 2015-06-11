# -*- coding: utf-8 -*-
'''
Created on Jul 18, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

import cloudstorage


def webapp_add_wsgi_middleware(app):
  from google.appengine.ext.appstats import recording
  app = recording.appstats_wsgi_middleware(app)
  return app

cloudstorage.set_default_retry_params(cloudstorage.RetryParams(initial_delay=0.2, max_delay=5.0, backoff_factor=2,
                                                               max_retries=5, max_retry_period=60, urlfetch_timeout=30))
