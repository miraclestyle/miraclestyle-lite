# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os

DEVELOPMENT_SERVER = os.getenv('SERVER_SOFTWARE', '').startswith('Development')

ACTIVE_HANDLERS = ('mapping',)


def __discover_host():
  http = 'http://'
  if os.environ.get('HTTPS') == 'on':
    http = 'https://'
  return '%s%s' % (http, os.environ.get('DEFAULT_VERSION_HOSTNAME', os.environ.get('HTTP_HOST')))
 
HOST = __discover_host()

# api path configs
API_ENDPOINT = HOST + '/api/endpoint'
API_MODEL_META = HOST + '/api/model_meta'

ROUTES = []
JINJA_GLOBALS = {}
JINJA_FILTERS = {}

DEBUG = True
TEMPLATE_CACHE = 0
WEBAPP2_EXTRAS = {}

# Configurations for user interface
JS_PATHS = [
  'libraries/jquery/dist/jquery.js',
  'libraries/jquery-ui/jquery-ui.js',
  'libraries/underscore/underscore.js',
  'libraries/angular/angular.js',
  'libraries/angular-ui-sortable/sortable.js',
  'libraries/angular-ui-utils/ui-utils.js',
  'libraries/angular-bootstrap/ui-bootstrap.js',
  'libraries/angular-bootstrap/ui-bootstrap-tpls.js',
  'libraries/angular-ui-router/release/angular-ui-router.js',
  'libraries/angular-messages/angular-messages.js',
  'libraries/angular-cookie/angular-cookie.js',
  'libraries/angular-touch/angular-touch.js',
  'libraries/angular-cache/dist/angular-cache.min.js',
  'libraries/angular-ui-select/dist/select.js'
]

CSS_PATHS = ['libraries/angular-ui-select/select.css', 'css/style.css']

ANGULAR_ACTIVE_COMPONENTS = ['account']