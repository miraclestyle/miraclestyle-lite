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
  return '%s%s' % (http, os.environ.get('HTTP_HOST'))
 
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

# ui based configurations
ANGULAR_MODULES = [
    'underscore',
    'router',
    'ngStorage',
    'ngUpload',
    'ngAnimate',
    'ngCookies',
    'ngSanitize',
    'ngTouch',
    'transition',
    'collapse',
    'accordion',
    'modal',
    'select2',
    'busy',
    'position',
    'datepicker',
    'sortable',
    'ngDragDrop',
    ]

ANGULAR_COMPONENTS = [
    'home',
    'account',
    'seller',
    'catalog',
    'buyer',
    'admin',
    ]

JQUERY_PLUGINS = ['select2/select2']