# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
from glob import glob

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(ROOT_DIR, 'templates', 'angular', 'parts')

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
ANGULAR_JS_PATHS = (
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
  'vendor/angular-google-chart/ng-google-chart.js',
  'lib/md-date-time/md-date-time.js',
  'lib/angular-material/angular-material.js',
  'lib/angulike/angulike.js',
  'lib/angular-bootstrap/angular-bootstrap.js',
  'lib/angular-cache/angular-cache.js',
  'lib/ng-upload/ng-upload.js'
)

ANGULAR_GLOBAL_JS_PATHS = ['shim', 'overrides', 'app', 'bootstrap']

ANGULAR_CSS_PATHS = ('js/lib/angular-material/angular-material.css',
                     'js/lib/md-date-time/md-date-time.css',
                     'js/vendor/material-design-icons/sprites/css-sprite/sprite-action-grey600.css',
                     'js/vendor/material-design-icons/sprites/css-sprite/sprite-device-grey600.css',
                     'js/vendor/material-design-icons/sprites/css-sprite/sprite-navigation-grey600.css',
                     'css/style.css')

class Structured():
  
  def __init__(self, segment, parts=None):
    self.segment = segment
  
  def __str__(self):
    return self.segment

ANGULAR_ACTIVE_COMPONENTS = [Structured('core'), Structured('home'), Structured('account'),
                             Structured('buyer'), Structured('collection'), Structured('seller'), 
                             Structured('catalog'), Structured('order'), Structured('admin')]
ANGULAR_ACTIVE_COMPONENTS_ITER = enumerate(ANGULAR_ACTIVE_COMPONENTS)
ANGULAR_ACTIVE_COMPONENTS = []
for i, angular_component in ANGULAR_ACTIVE_COMPONENTS_ITER:
  if isinstance(angular_component, Structured):
    for entity in ('services', 'filters', 'directives', 'controllers'):
      ANGULAR_ACTIVE_COMPONENTS.append('%s/%s' % (angular_component, entity))
  else:
    ANGULAR_ACTIVE_COMPONENTS.append(angular_component)
ANGULAR_TEMPLATES = []
files = []
for dirname, dirnames, filenames in os.walk(TEMPLATES_DIR):
    for filename in filenames:
        files.append(os.path.join(dirname, filename))
for f in files:
  if not f.endswith('parts/index.html') and f.endswith('.html'):
    ANGULAR_TEMPLATES.append((f[len(TEMPLATES_DIR) + 1:],))
# ('Alias', 'Full path to the template in the app'), something to read https://cloud.google.com/appengine/docs/python/config/appconfig#application_readable