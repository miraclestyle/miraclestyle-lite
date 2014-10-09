# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

DEVELOPMENT_SERVER = os.getenv('SERVER_SOFTWARE', '').startswith('Development')

ACTIVE_HANDLERS = ('mapping', 'builder')


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

# Angular only configurations for user interface
ANGULAR_JS_PATHS = (
  'libraries/jquery/dist/jquery.js',
  'libraries/jquery-ui/jquery-ui.js',
  'libraries/underscore/underscore.js',
  'libraries/angular/angular.js',
  'libraries/angular-ui-sortable/sortable.js',
  'libraries/angular-ui-utils/ui-utils.js',
  'libraries/angular-sanitize/angular-sanitize.js',
  'libraries/angular-bootstrap/ui-bootstrap.js',
  'libraries/angular-bootstrap/ui-bootstrap-tpls.js',
  'libraries/angular-ui-router/release/angular-ui-router.js',
  'libraries/angular-messages/angular-messages.js',
  'libraries/angular-cookie/angular-cookie.js',
  'libraries/angular-touch/angular-touch.js',
  'libraries/angular-cache/dist/angular-cache.js',
  'libraries/angular-ui-select/dist/select.js',
  'libraries/angular-bootstrap-datetimepicker/src/js/datetimepicker.js'
)

ANGULAR_CSS_PATHS = ('fonts/sawasdee/stylesheet.css', 
                     'libraries/angular-ui-select/dist/select.css',
                     'libraries/angular-ui-select/dist/select2.css',
                     'libraries/angular-bootstrap-datetimepicker/src/css/datetimepicker.css',
                     'css/style.css')

ANGULAR_ACTIVE_COMPONENTS = ('home', 'account', 'tests')

# ('Alias', 'Full path to the template in the app')
ANGULAR_TEMPLATES = (
  # core
  ('home/index.html',),
  ('tests/html.html',),
  ('form/builder.html',),
  ('underscore/form/string.html',),
  ('underscore/form/select.html',),
  ('underscore/form/select_async.html',),
  # angular ui
  ('template/datetimepicker/datetimepicker.html',
   'libraries/angular-bootstrap/datetimepicker/datetimepicker.html'),
  ('template/accordion/accordion-group.html',
   'libraries/angular-bootstrap/accordion/accordion-group.html'),
  ('template/accordion/accordion.html',
   'libraries/angular-bootstrap/accordion/accordion.html'),
  ('template/datepicker/datepicker.html',
   'libraries/angular-bootstrap/datepicker/datepicker.html'),
  ('template/datepicker/day.html',
   'libraries/angular-bootstrap/datepicker/day.html'),
  ('template/datepicker/month.html',
   'libraries/angular-bootstrap/datepicker/month.html'),
  ('template/datepicker/popup.html',
   'libraries/angular-bootstrap/datepicker/popup.html'),
  ('template/datepicker/year.html',
   'libraries/angular-bootstrap/datepicker/year.html'),
  ('template/modal/backdrop.html',
   'libraries/angular-bootstrap/modal/backdrop.html'),
  ('template/modal/window.html',
   'libraries/angular-bootstrap/modal/window.html'),
  ('template/popover/popover.html',
   'libraries/angular-bootstrap/popover/popover.html'),
  ('template/progressbar/progress.html',
   'libraries/angular-bootstrap/progressbar/progress.html'),
  ('template/progressbar/progressbar.html',
   'libraries/angular-bootstrap/progressbar/progressbar.html'),
  ('template/timepicker/timepicker.html',
   'libraries/angular-bootstrap/timepicker/timepicker.html'),
  ('template/tooltip/tooltip-html-unsafe-popup.html',
   'libraries/angular-bootstrap/tooltip/tooltip-html-unsafe-popup.html'
   ),
  ('template/tooltip/tooltip-popup.html',
   'libraries/angular-bootstrap/tooltip/tooltip-popup.html'),
  # select2
  ('bootstrap/choices.tpl.html',
   'libraries/angular-ui-select/bootstrap/choices.tpl.html'),
  ('bootstrap/match-multiple.tpl.html',
   'libraries/angular-ui-select/bootstrap/match-multiple.tpl.html'),
  ('bootstrap/match.tpl.html',
   'libraries/angular-ui-select/bootstrap/match.tpl.html'),
  ('bootstrap/select-multiple.tpl.html',
   'libraries/angular-ui-select/bootstrap/select-multiple.tpl.html'),
  ('bootstrap/select.tpl.html',
   'libraries/angular-ui-select/bootstrap/select.tpl.html'),
  ('select2/choices.tpl.html',
   'libraries/angular-ui-select/select2/choices.tpl.html'),
  ('select2/match-multiple.tpl.html',
   'libraries/angular-ui-select/select2/match-multiple.tpl.html'),
  ('select2/match.tpl.html',
   'libraries/angular-ui-select/select2/match.tpl.html'),
  ('select2/select-multiple.tpl.html',
   'libraries/angular-ui-select/select2/select-multiple.tpl.html'),
  ('select2/select.tpl.html',
   'libraries/angular-ui-select/select2/select.tpl.html'),
  ('selectize/choices.tpl.html',
   'libraries/angular-ui-select/selectize/choices.tpl.html'),
  ('selectize/match.tpl.html',
   'libraries/angular-ui-select/selectize/match.tpl.html'),
  ('selectize/select.tpl.html',
   'libraries/angular-ui-select/selectize/select.tpl.html'),
)