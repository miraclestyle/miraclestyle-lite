# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

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

# ('Alias', 'Full path to the template in the app'), something to read https://cloud.google.com/appengine/docs/python/config/appconfig#application_readable
ANGULAR_TEMPLATES = (
  # core
  ('core/form/builder.html',),
  ('core/misc/alert.html',),
  ('core/misc/errors.html',),
  ('core/misc/confirm.html',),
  ('core/misc/content_view_body.html',),
  ('core/misc/content_view_footer.html',),
  ('core/misc/load_more_button.html',),
  ('core/misc/search_form.html',),
  ('core/misc/icon.html',),
  ('core/misc/history.html',),
  ('core/misc/history_view_body.html',),

  ('core/action/dropdown.html',),
  ('core/action/dropdown_list.html',),
  ('core/action/toolbar.html',),
  ('core/select/input.html',),
  ('core/select/underscore/choices.html',),
  ('core/list/button.html',),
  ('core/underscore/form/select.html',),
  ('core/underscore/form/select_async.html',),
  ('core/underscore/form/structured.html',),
  ('core/underscore/form/boolean.html',),
  ('core/underscore/form/datetime.html',),
  ('core/underscore/form/text.html',),
  ('core/underscore/form/image.html',),
  ('core/underscore/form/string.html',),
  ('core/underscore/form/plugins.html',),
  ('core/underscore/form/manage_plugin.html',),
  ('core/underscore/form/manage_structured.html',),
  
  ('core/form/manage_entity.html',),
  ('core/form/manage_entity_default_body.html',),
      
  ('template/accordion/accordion_group.html',
   'lib/angular-bootstrap/accordion/accordion_group.html'),
  ('template/accordion/accordion.html',
   'lib/angular-bootstrap/accordion/accordion.html'),
  ('template/modal/backdrop.html',
   'lib/angular-bootstrap/modal/backdrop.html'),
  ('template/modal/window.html',
   'lib/angular-bootstrap/modal/window.html'),
  ('lib/md-date-time/popup.html',),
  ('lib/md-date-time/md-date-time.html',),
  
  # account
  ('account/manage_body.html',),
  ('account/manage_actions.html',),
  ('account/administer.html',),
  
  # seller
  ('seller/carrier_line_rule_display.html',),
  ('seller/address_rule_location_display.html',),
  ('seller/default_line_display.html',),
  ('seller/view_body.html',),
  ('seller/view_footer.html',),
  
  # buyer
  ('buyer/address_display.html',),
  ('buyer/carts.html',),

  # colleciton
  ('collection/manage_body.html',),

  # admin area
  ('admin/list.html',),
  ('admin/list_display/default.html',),
  ('admin/list_display/31.html',), # display directive template for catalog
  ('admin/list_display/11.html',), # display directive template for account
  ('admin/list_display/34.html',), # display directive template for order

  # catalog
  ('catalog/quick_info.html',),
  ('catalog/manage_actions.html',),
  ('catalog/administer.html',),
  ('catalog/products.html',),
  ('catalog/view.html',),
  ('catalog/product/manage_footer.html',),
  ('catalog/product/view.html',),
  ('catalog/product/variant_choices.html',),
  ('catalog/list.html',),
  ('catalog/underscore/form/image.html',),
  ('catalog/product/product_instance_display.html',),

  # order
  ('order/view.html',),
  ('order/list.html',),

  # other
  ('home/index.html',),
  ('home/main_menu_item.html',),
)