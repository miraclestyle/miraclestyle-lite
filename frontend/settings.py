# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import json
import codecs
import shutil
from glob import glob

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(ROOT_DIR, 'client')
CLIENT_COMPONENTS_DIR = os.path.join(CLIENT_DIR, 'src')

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
ANGULAR_VENDOR_JS = (
  'vendor/modernizr/modernizr.js',
  'vendor/jquery/dist/jquery.js',
  'vendor/jquery-ui/ui/core.js',
  'vendor/jquery-ui/ui/widget.js',
  'vendor/jquery-ui/ui/mouse.js',
  'vendor/jquery-ui/ui/position.js',
  'vendor/jquery-ui/ui/sortable.js',
  'vendor/jquery-ui/ui/draggable.js',
  'vendor/jquery-ui/ui/droppable.js',
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
  'vendor/momentjs/min/moment.min.js',
  'vendor/humanize-duration/humanize-duration.js',
  'vendor/angular-timer/dist/angular-timer.js',
  'vendor/angular-google-chart/ng-google-chart.js'
)
ANGULAR_VENDOR_CSS = ('vendor/material-design-iconic-font/css/material-design-iconic-font.min.css',)
ANGULAR_TEMPLATE_FILES = []
ANGULAR_STATIC_FILES = []
ANGULAR_CSS_FILES = []
ANGULAR_CSS_PATHS = []
ANGULAR_JAVASCRIPT_FILES = []
ANGULAR_JAVASCRIPT_PATHS = []
ANGULAR_ACTIVE_COMPONENTS = [
    'core/kernel/boot',
    'core/kernel',
    'core/config',
    'core/backdrop',
    'core/button',
    'core/card',
    'core/checkbox',
    'core/content',
    'core/util',
    'core/input',
    'core/progressCircular',
    'core/progressLinear',
    'core/radioButton',
    'core/sidenav',
    'core/simpledialog',
    'core/list',
    'core/swipe',
    'core/switch',
    'core/textField', 
    'core/toolbar',
    'core/action', 
    'core/cache', 
    'core/datetime', 
    'core/fields', 
    'core/grid',
    'core/misc', 
    'core/modal', 
    'core/models', 
    'core/record', 
    'core/select', 
    'core/slider', 
    'core/social', 
    'core/upload',
    'core/responsive', 
    'account',
    'buyer', 
    'catalog', 
    'collection',
    'home', 
    'location', 
    'order', 
    'seller',
    'admin',
    'core/kernel/init'
]

ANGULAR_JAVASCRIPT_PATHS.extend(ANGULAR_VENDOR_JS)
ANGULAR_CSS_PATHS.extend(ANGULAR_VENDOR_CSS)

_client_dir_length = len(CLIENT_DIR) + 1
_client_components_dir_length = len(CLIENT_COMPONENTS_DIR) + 1
for component in ANGULAR_ACTIVE_COMPONENTS:
  for dirname, dirnames, filenames in os.walk(os.path.join(CLIENT_COMPONENTS_DIR, component)):
    for f in filenames:
      if f.startswith('.'):
        continue
      abs_path = os.path.join(dirname, f)
      path = abs_path[_client_dir_length:]
      iscomponent = dirname.endswith(component)
      if f.endswith('.js') and not dirname.endswith('static') and iscomponent:
        ANGULAR_JAVASCRIPT_PATHS.append(path)
        ANGULAR_JAVASCRIPT_FILES.append(abs_path)
      elif f.endswith('.css') and not dirname.endswith('static') and iscomponent \
           and not f.endswith('-default-theme.css'):
        ANGULAR_CSS_PATHS.append(path)
        ANGULAR_CSS_FILES.append(abs_path)
      elif f.endswith('.html') and dirname.endswith('template') or '/template/' in str(dirname):
        ANGULAR_TEMPLATE_FILES.append(abs_path)

if not DEBUG:
  ANGULAR_CSS_FILES = ['dist/style.css']
  ANGULAR_JAVASCRIPT_FILES = ['dist/app.js', 'dist/templates.js']

def get_component_dirs():
  for dirname, dirnames, filenames in os.walk(CLIENT_COMPONENTS_DIR):
      for d in dirnames:
        if d != 'template':
          ANGULAR_ACTIVE_COMPONENTS.append(os.path.join(dirname, d)[_client_components_dir_length:])
  return json.dumps(ANGULAR_ACTIVE_COMPONENTS, indent=4)

def _copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(src).st_mtime - os.stat(dst).st_mtime > 1:
                shutil.copy2(s, d)

def _empty_dir(d):
  for root, dirs, files in os.walk(d):
    for f in files:
      os.unlink(os.path.join(root, f))
    for d in dirs:
      shutil.rmtree(os.path.join(root, d))

def build(templates=True, statics=True, js_and_css=True, write=False, inform=True):
  dist = os.path.join(CLIENT_DIR, 'dist')
  paths = {}
  buff = {}

  def out(t):
    if inform:
      print t
  def read(f, m='r'):
    return codecs.open(f, m, 'utf-8')

  for p in ['app.js', 'style.css', 'static', 'templates.js']:
      paths[p] = os.path.join(dist, p)
      buff[p] = u''
  if js_and_css:
    for t, b in [('JAVASCRIPT', 'app.js'), ('CSS', 'style.css')]:
        for files in globals().get('ANGULAR_%s_FILES' % t):
            with read(files) as f:
                buff[b] += f.read()
    if write:
      for b, w in buff.iteritems():
          if w:
            out('Writing %s' % paths[b])
            with read(paths[b], 'w') as f:
                f.write(w)  # @todo minify
  if templates:
    cached_templates = []
    for tpl in ANGULAR_TEMPLATE_FILES:
      with read(tpl) as f:
        d = tpl.replace('/template/', '/')[_client_components_dir_length:]
        out('Caching template %s' % d)
        cached_templates.append('    $templateCache.put(%s, %s);' % (json.dumps(d), json.dumps(f.read())))
    buff['templates.js'] = """angular.module('app').run(function ($templateCache) {\n%s\n});""" % "\n".join(cached_templates)
  if write:
    with read(paths['templates.js'], 'w') as f:
      out('Writing cache %s' % paths['templates.js'])
      f.write(buff['templates.js'])

  if statics and write:
    out('Empty static dir %s' % paths['static'])
    _empty_dir(paths['static'])
    for c in ANGULAR_ACTIVE_COMPONENTS:
      try:
        static_folder = os.path.join(CLIENT_COMPONENTS_DIR, c, 'static')
        _copytree(static_folder, paths['static'])
      except Exception as e:
        pass
    out('Write static dir %s' % paths['static'])
  return buff

if __name__ == '__main__':
  build(write=True)