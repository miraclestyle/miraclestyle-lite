# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
ACTIVE_CONTROLLERS = ('api', 'auth', 'task', 'ui', 'admin', 'domain', 'cron', 'tests')

TEMPLATE_CACHE = 0

SESSION_USER_KEY = 'usr'

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
                      'app',
                      'nav',
                      'rule',
                      'notify',
                      'catalog',
                      'buyer',
                      'transaction',
                      'admin',
                      ]

JQUERY_PLUGINS = [
                  'select2/select2',
                 ]


COOKIE_CSRF_KEY = 'XSRF-TOKEN'
COOKIE_USER_KEY = 'auth'

WEBAPP2_EXTRAS = {}