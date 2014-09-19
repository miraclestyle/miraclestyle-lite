# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
ACTIVE_CONTROLLERS = ('api', 'account', 'catalog', 'task', 'ui', 'admin', 'cron', 'tests')

TEMPLATE_CACHE = 0

WEBAPP2_EXTRAS = {}
SESSION_USER_KEY = 'usr'
COOKIE_CSRF_KEY = 'XSRF-TOKEN'
COOKIE_USER_KEY = 'auth'

# ui based configurations
ANGULAR_MODULES = ['underscore',
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

ANGULAR_COMPONENTS = ['home',
                      'account',
                      'seller',
                      'catalog',
                      'buyer',
                      'admin',
                      ]

JQUERY_PLUGINS = [
                  'select2/select2',
                 ]