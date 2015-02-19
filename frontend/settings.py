# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
from glob import glob

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(ROOT_DIR, 'client')
CLIENT_COMPONENTS_DIR = os.path.join(CLIENT_DIR, 'src', 'components')

DEVELOPMENT_SERVER = os.getenv('SERVER_SOFTWARE', '').startswith('Development')

ACTIVE_HANDLERS = ('mapping', 'builder')

HOST_URL = None
if DEVELOPMENT_SERVER:
  HOST_URL = 'http://128.65.105.64:9982'

if HOST_URL is None:
  def __discover_host_url():
    http = 'http://'
    if os.environ.get('HTTPS') == 'on':
      http = 'https://'
    return '%s%s' % (http, os.environ.get('DEFAULT_VERSION_HOSTNAME', os.environ.get('HTTP_HOST')))
  HOST_URL = __discover_host_url()

# api path configs
API_ENDPOINT = HOST_URL + '/api/endpoint'
API_MODEL_META = HOST_URL + '/api/model_meta'

ROUTES = []
JINJA_GLOBALS = {}
JINJA_FILTERS = {}

DEBUG = True
TEMPLATE_CACHE = 0
WEBAPP2_EXTRAS = {}

# Angular only configurations for user interface
ANGULAR_VENDOR = (
  'vendor/modernizr/modernizr.js',
  'vendor/jquery/dist/jquery.js',
  'vendor/jquery-ui/jquery-ui.js',
  'vendor/Steady.js/Steady.js',
  'vendor/jquery.scrollTo/jquery.scrollTo.js',
  'vendor/jquery-ui-touch-punch/jquery.ui.touch-punch.min.js',
  'vendor/jquery-cookie/jquery.cookie.js',
  'vendor/underscore/underscore.js',
  'vendor/underscore.string/lib/underscore.string.js',
  'vendor/angular/angular.js',
  'vendor/angular-ui-sortable/sortable.js',
  'vendor/angular-ui-utils/ui-utils.js',
  'vendor/angular-sanitize/angular-sanitize.js',
  'vendor/angular-ui-router/release/angular-ui-router.js',
  'vendor/angular-cookie/angular-cookie.js',
  'vendor/angular-animate/angular-animate.js',
  'vendor/angular-aria/angular-aria.js',
  'vendor/angular-messages/angular-messages.js',
  'vendor/angular-dragdrop/src/angular-dragdrop.js',
  'vendor/angular-timer/dist/angular-timer.js',
  'vendor/angular-google-chart/ng-google-chart.js'
)
ANGULAR_CSS_FILES = []
ANGULAR_CSS_PATHS = []
ANGULAR_JAVASCRIPT_FILES = []
ANGULAR_JAVASCRIPT_PATHS = []
ANGULAR_STATIC_PATHS = []
ANGULAR_ACTIVE_COMPONENTS = [
    "core/kernel/boot",
    "core/kernel",
    "core/material_design",
    "core/accordion", 
    "core/action", 
    "core/cache", 
    "core/datetime", 
    "core/fields", 
    "core/grid",
    "core/misc", 
    "core/modal", 
    "core/models", 
    "core/record", 
    "core/responsive", 
    "core/select", 
    "core/slider", 
    "core/social", 
    "core/upload",
    "account",
    "buyer", 
    "catalog", 
    "collection",
    "home", 
    "location", 
    "order", 
    "seller",
    "admin",
    "core/kernel/init"
]

_client_dir_length = len(CLIENT_DIR) + 1
_client_components_dir_length = len(CLIENT_COMPONENTS_DIR) + 1
for component in ANGULAR_ACTIVE_COMPONENTS:
  for dirname, dirnames, filenames in os.walk(os.path.join(CLIENT_COMPONENTS_DIR, component)):
    for f in filenames:
      abs_path = os.path.join(dirname, f)
      path = abs_path[_client_dir_length:]
      if f.endswith('.js'):
        ANGULAR_JAVASCRIPT_PATHS.append(abs_path)
        ANGULAR_JAVASCRIPT_FILES.append(path)
      elif f.endswith('.css'):
        ANGULAR_CSS_PATHS.append(abs_path)
        ANGULAR_CSS_FILES.append(path)
      else:
        ANGULAR_STATIC_PATHS.append(abs_path)

if not DEBUG:
  ANGULAR_CSS_FILES = ['dist/style.css']
  ANGULAR_JAVASCRIPT_FILES = ['dist/app.js', 'dist/templates.js']

def get_component_dirs():
  for dirname, dirnames, filenames in os.walk(CLIENT_COMPONENTS_DIR):
      for d in dirnames:
        if d != 'template':
          ANGULAR_ACTIVE_COMPONENTS.append(os.path.join(dirname, d)[_client_components_dir_length:])
  import json
  print json.dumps(ANGULAR_ACTIVE_COMPONENTS, indent=4)
# ('Alias', 'Full path to the template in the app'), something to read https://cloud.google.com/appengine/docs/python/config/appconfig#application_readable