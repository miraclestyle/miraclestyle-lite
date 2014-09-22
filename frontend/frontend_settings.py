# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
ACTIVE_CONTROLLERS = ('home', 'account', 'catalog', 'tests', 'ui')

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