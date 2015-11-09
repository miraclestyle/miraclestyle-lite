# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import json
import sys
import codecs
import shutil
import subprocess

# META
SITE_META_TITLE = 'Miraclestyle.com'
SITE_META_DESCRIPTION = 'Description'
SITE_META_KEYWORDS = 'miraclestyle,thing'
SITE_META_TWITTER_USERNAME = 'miraclestyle'
DEBUG_HOST_NAMES = ['localhost:9982', 'universal-trail-608.appspot.com']
HOST_NAME = os.environ.get('DEFAULT_VERSION_HOSTNAME', os.environ.get('HTTP_HOST'))
DEBUG = False
if HOST_NAME in DEBUG_HOST_NAMES:
  DEBUG = True

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(ROOT_DIR, 'client')
CLIENT_COMPONENTS_DIR = os.path.join(CLIENT_DIR, 'src')

DEVELOPMENT_SERVER = os.getenv('SERVER_SOFTWARE', '').startswith('Development')

ACTIVE_HANDLERS = ('misc', 'seller', 'catalog', 'home', 'builder')

HOST_URL = None
if HOST_URL is None:
  def __discover_host_url():
    http = 'http://'
    if os.environ.get('HTTPS') == 'on':
      http = 'https://'
    return '%s%s' % (http, HOST_NAME)
  HOST_URL = __discover_host_url()

# api path configs
API_ENDPOINT = HOST_URL + '/api/endpoint'
API_MODEL_META = HOST_URL + '/api/model_meta'

ROUTES = []
JINJA_GLOBALS = {}
JINJA_FILTERS = {}

TEMPLATE_CACHE = 0
WEBAPP2_EXTRAS = {}


def env(dev, production=None):
  if not production:
    production = dev
  if DEBUG:
    return dev
  else:
    return production

# Angular only configurations for user interface
ANGULAR_VENDOR_JS = (
    env('vendor/modernizr/modernizr.js'),
    env('vendor/jquery/dist/jquery.js', 'vendor/jquery/dist/jquery.min.js'),
    env('vendor/jquery-ui/ui/core.js', 'vendor/jquery-ui/ui/minified/core.min.js'),
    env('vendor/jquery-ui/ui/widget.js', 'vendor/jquery-ui/ui/minified/widget.min.js'),
    env('vendor/jquery-ui/ui/mouse.js', 'vendor/jquery-ui/ui/minified/mouse.min.js'),
    env('vendor/jquery-ui/ui/position.js', 'vendor/jquery-ui/ui/minified/position.min.js'),
    env('vendor/jquery-ui/ui/sortable.js', 'vendor/jquery-ui/ui/minified/sortable.min.js'),
    env('vendor/jquery-ui/ui/draggable.js', 'vendor/jquery-ui/ui/minified/draggable.min.js'),
    env('vendor/jquery-ui/ui/droppable.js', 'vendor/jquery-ui/ui/minified/droppable.min.js'),
    env('vendor/showdown/src/showdown.js', 'vendor/showdown/compressed/Showdown.min.js'),
    env('vendor/jquery.scrollTo/jquery.scrollTo.js', 'vendor/jquery.scrollTo/jquery.scrollTo.min.js'),
    env('vendor/jquery-ui-touch-punch/jquery.ui.touch-punch.js', 'vendor/jquery-ui-touch-punch/jquery.ui.touch-punch.min.js'),
    env('vendor/jquery-cookie/jquery.cookie.js'),
    env('vendor/underscore/underscore.js', 'vendor/underscore/underscore-min.js'),
    env('vendor/underscore.string/lib/underscore.string.js', 'vendor/underscore.string/dist/underscore.string.min.js'),
    env('vendor/angular/angular.js', 'vendor/angular/angular.min.js'),
    env('vendor/angular-ui-sortable/sortable.js', 'vendor/angular-ui-sortable/sortable.min.js'),
    env('vendor/angular-ui-utils/ui-utils.js', 'vendor/angular-ui-utils/ui-utils.min.js'),
    env('vendor/angular-sanitize/angular-sanitize.js', 'vendor/angular-sanitize/angular-sanitize.min.js'),
    env('vendor/angular-ui-router/release/angular-ui-router.js', 'vendor/angular-ui-router/release/angular-ui-router.min.js'),
    env('vendor/angular-cookie/angular-cookie.js', 'vendor/angular-cookie/angular-cookie.min.js'),
    env('vendor/angular-animate/angular-animate.js', 'vendor/angular-animate/angular-animate.min.js'),
    env('vendor/angular-aria/angular-aria.js', 'vendor/angular-aria/angular-aria.min.js'),
    env('vendor/angular-messages/angular-messages.js', 'vendor/angular-messages/angular-messages.min.js'),
    env('vendor/angular-dragdrop/src/angular-dragdrop.js', 'vendor/angular-dragdrop/src/angular-dragdrop.min.js'),
    env('vendor/momentjs/moment.js', 'vendor/momentjs/min/moment.min.js'),
    env('vendor/humanize-duration/humanize-duration.js'),
    env('vendor/angular-timer/dist/angular-timer.js', 'vendor/angular-timer/dist/angular-timer.min.js'),
    env('vendor/angular-google-chart/ng-google-chart.js'),
    env('vendor/angular-markdown-directive/markdown.js')
)
ANGULAR_VENDOR_CSS = ()
ANGULAR_TEMPLATE_FILES = []
ANGULAR_STATIC_FILES = []
ANGULAR_CSS_FILES = []
ANGULAR_CSS_PATHS = []
ANGULAR_JAVASCRIPT_FILES = []
ANGULAR_JAVASCRIPT_PATHS = []
ANGULAR_ACTIVE_COMPONENTS = [
    'core/kernel/boot',
    'core/kernel',
    'core/backdrop',
    'core/config',
    'core/button',
    'core/card',
    'core/checkbox',
    'core/content',
    'core/util',
    'core/input',
    'core/radioButton',
    'core/sidenav',
    'core/simpledialog',
    'core/list',
    'core/swipe',
    'core/textField',
    'core/snackbar',
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
    'core/spinner',
    'account',
    'buyer',
    'catalog',
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
      elif f.endswith('.css') and not dirname.endswith('static') and iscomponent:
        ANGULAR_CSS_PATHS.append(path)
        ANGULAR_CSS_FILES.append(abs_path)
      elif f.endswith('.html') and dirname.endswith('template') or '/template/' in str(dirname):
        ANGULAR_TEMPLATE_FILES.append(abs_path)


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
      _copytree(s, d, symlinks, ignore)
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
  node = os.path.join(ROOT_DIR, '.node', 'raw')
  paths = {}
  buff = {}

  def out(t):
    if inform:
      print t

  def read(f, m='r'):
    return codecs.open(f, m, 'utf-8')

  for p in ['app.js', 'seo.css', 'style.css', 'templates.js']:
    paths[p] = os.path.join(node, p)
    buff[p] = u''
  paths['static'] = os.path.join(dist, 'static')
  if js_and_css:
    with read(os.path.join(CLIENT_DIR, 'seo', 'seo.css')) as f:
      buff['seo.css'] = f.read()
    for t, b in [('JAVASCRIPT', 'app.js'), ('CSS', 'style.css')]:
      for files in globals().get('ANGULAR_%s_FILES' % t):
        with read(files) as f:
          buff[b] += f.read()
    if write:
      for b, w in buff.iteritems():
        if w:
          out('Writing %s' % paths[b])
          with read(paths[b], 'w') as f:
            f.write(w)
  if templates:
    out('Caching templates...')
    cached_templates = []
    for tpl in ANGULAR_TEMPLATE_FILES:
      with read(tpl) as f:
        d = tpl.replace('/template/', '/')[_client_components_dir_length:]
        #out('Caching template %s' % d)
        cached_templates.append('    $templateCache.put(%s, %s);' % (json.dumps(d), json.dumps(f.read())))
    buff['templates.js'] = """angular.module('app').run(ng(function ($templateCache) {\n%s\n}));""" % "\n".join(cached_templates)
    out('Cached %s templates' % len(cached_templates))
  if write:
    with read(paths['templates.js'], 'w') as f:
      #out('Writing cache %s' % paths['templates.js'])
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
    cmd = ['gulp']
    if len(sys.argv) > 1:
      cmd.extend(sys.argv[:][1:])
    proc = subprocess.Popen(cmd, cwd=node)
    while proc.wait():
      exit()
  return buff

if __name__ == '__main__':
  build(write=True)
