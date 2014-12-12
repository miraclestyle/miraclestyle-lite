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
  'vendor/jquery/dist/jquery.js',
  'vendor/jquery-ui/jquery-ui.js',
  'vendor/jquery-ui-touch-punch/jquery.ui.touch-punch.min.js',
  'vendor/underscore/underscore.js',
  'vendor/underscore.string/lib/underscore.string.js',
  'vendor/angular/angular.js',
  'vendor/angular-ui-sortable/sortable.js',
  'vendor/angular-ui-utils/ui-utils.js',
  'vendor/angular-sanitize/angular-sanitize.js',
  'vendor/angular-bootstrap/ui-bootstrap.js',
  'vendor/angular-bootstrap/ui-bootstrap-tpls.js',
  'vendor/angular-ui-router/release/angular-ui-router.js',
  'vendor/angular-messages/angular-messages.js',
  'vendor/angular-cookie/angular-cookie.js',
  'vendor/angular-touch/angular-touch.js',
  'vendor/angular-dragdrop/src/angular-dragdrop.js',
  'vendor/jquery.kinetic/jquery.kinetic.js',
  'vendor/angular-elastic/elastic.js',
  'lib/angular-cache/dist/angular-cache.js',
  'vendor/angular-ui-select/dist/select.js',
  'lib/angular-ui-bootstrap-datetimepicker/datetimepicker.js',
  'lib/angular-ui-bootstrap-datetimepicker/datetimepicker-tpls-0.11.js',
  'lib/ngUpload/ng-upload.js'
)

ANGULAR_GLOBAL_JS_PATHS = ['shim', 'overrides', 'app', 'services', 'directives', 'filters', 'controllers', 'bootstrap']

ANGULAR_CSS_PATHS = ('fonts/sawasdee/stylesheet.css',
                     'js/lib/angular-ui-bootstrap-datetimepicker/datetimepicker.css',
                     'css/style.css')

class Structured():
  
  def __init__(self, segment, parts=None):
    self.segment = segment
  
  def __str__(self):
    return self.segment

ANGULAR_ACTIVE_COMPONENTS = [Structured('home'), Structured('account'), Structured('buyer'), Structured('seller'), Structured('catalog')]
ANGULAR_ACTIVE_COMPONENTS_ITER = enumerate(ANGULAR_ACTIVE_COMPONENTS)
ANGULAR_ACTIVE_COMPONENTS = []
for i, angular_component in ANGULAR_ACTIVE_COMPONENTS_ITER:
  if isinstance(angular_component, Structured):
    for entity in ('services', 'filters', 'directives', 'controllers'):
      ANGULAR_ACTIVE_COMPONENTS.append('%s/%s' % (angular_component, entity))
  else:
    ANGULAR_ACTIVE_COMPONENTS.append(angular_component)

# ('Alias', 'Full path to the template in the app')
ANGULAR_TEMPLATES = (
  # core
  ('home/index.html',),

  ('form/builder.html',),

  ('misc/form_wrapper.html',),
  ('misc/modal/alert.html',),
  ('misc/modal/errors.html',),
  ('misc/modal/confirm.html',),

  ('entity/modal/editor.html',),
  ('entity/modal/editor_default_body.html',),
  ('entity/modal/editor_default_footer.html',),
  
  ('account/modal/settings.html',),
  
  ('seller/directive/carrier_line_rule_display.html',),
  ('seller/directive/address_rule_location_display.html',),
  
  ('buyer/directive/buyer_address_display.html',),
  
  ('catalog/modal/manage_footer.html',),
  ('catalog/modal/administer.html',),
  ('catalog/modal/products.html',),
  ('catalog/modal/view.html',),
  ('catalog/product/modal/manage_footer.html',),
  ('catalog/product/modal/view.html',),
  ('catalog/product/modal/variant_choices.html',),
  ('catalog/list.html',),
  ('catalog/underscore/form/image.html',),
  ('catalog/product/directive/product_instance_display.html',),
  
  ('underscore/form/select.html',),
  ('underscore/form/select_async.html',),
  ('underscore/form/structured.html',),
  ('underscore/form/boolean.html',),
  ('underscore/form/datetime.html',),
  ('underscore/form/text.html',),
  ('underscore/form/image.html',),
  ('underscore/form/string.html',),
  ('underscore/form/plugins.html',),
  ('underscore/form/modal/plugins.html',),
  ('underscore/form/modal/structured.html',),
 
                     
  ('template/accordion/accordion-group.html',
   'lib/angular-bootstrap/accordion/accordion-group.html'),
  ('template/accordion/accordion.html',
   'lib/angular-bootstrap/accordion/accordion.html'),
  ('template/datepicker/datepicker.html',
   'lib/angular-bootstrap/datepicker/datepicker.html'),
  ('template/datepicker/day.html',
   'lib/angular-bootstrap/datepicker/day.html'),
  ('template/datepicker/month.html',
   'lib/angular-bootstrap/datepicker/month.html'),
  ('template/datepicker/popup.html',
   'lib/angular-bootstrap/datepicker/popup.html'),
  ('template/datepicker/year.html',
   'lib/angular-bootstrap/datepicker/year.html'),
  ('template/modal/backdrop.html',
   'lib/angular-bootstrap/modal/backdrop.html'),
  ('template/modal/window.html',
   'lib/angular-bootstrap/modal/window.html'),
  ('template/popover/popover.html',
   'lib/angular-bootstrap/popover/popover.html'),
  ('template/progressbar/progress.html',
   'lib/angular-bootstrap/progressbar/progress.html'),
  ('template/progressbar/progressbar.html',
   'lib/angular-bootstrap/progressbar/progressbar.html'),
  ('template/timepicker/timepicker.html',
   'lib/angular-bootstrap/timepicker/timepicker.html'),
  ('template/tooltip/tooltip-html-unsafe-popup.html',
   'lib/angular-bootstrap/tooltip/tooltip-html-unsafe-popup.html'
   ),
  ('template/tooltip/tooltip-popup.html',
   'lib/angular-bootstrap/tooltip/tooltip-popup.html'),
  # select2
  ('bootstrap/choices.tpl.html',
   'lib/angular-ui-select/bootstrap/choices.tpl.html'),
  ('bootstrap/match-multiple.tpl.html',
   'lib/angular-ui-select/bootstrap/match-multiple.tpl.html'),
  ('bootstrap/match.tpl.html',
   'lib/angular-ui-select/bootstrap/match.tpl.html'),
  ('bootstrap/select-multiple.tpl.html',
   'lib/angular-ui-select/bootstrap/select-multiple.tpl.html'),
  ('bootstrap/select.tpl.html',
   'lib/angular-ui-select/bootstrap/select.tpl.html'),
  ('select2/choices.tpl.html',
   'lib/angular-ui-select/select2/choices.tpl.html'),
  ('select2/match-multiple.tpl.html',
   'lib/angular-ui-select/select2/match-multiple.tpl.html'),
  ('select2/match.tpl.html',
   'lib/angular-ui-select/select2/match.tpl.html'),
  ('select2/select-multiple.tpl.html',
   'lib/angular-ui-select/select2/select-multiple.tpl.html'),
  ('select2/select.tpl.html',
   'lib/angular-ui-select/select2/select.tpl.html'),
  ('selectize/choices.tpl.html',
   'lib/angular-ui-select/selectize/choices.tpl.html'),
  ('selectize/match.tpl.html',
   'lib/angular-ui-select/selectize/match.tpl.html'),
  ('selectize/select.tpl.html',
   'lib/angular-ui-select/selectize/select.tpl.html'),
)