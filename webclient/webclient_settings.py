# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
ACTIVE_CONTROLLERS = ('test', 'auth', 'task', 'ui', 'admin', 'domain')

TEMPLATE_CACHE = 0

SESSION_USER_KEY = 'usr'

ANGULAR_MODULES = ['router', 
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
                   'checklist',
                   'position',
                   'datepicker',
                  ]

ANGULAR_COMPONENTS = ['home',
                      'account',
                      'app',
                      'nav',
                      'rule',
                      'notify',
                      'catalog',
                      # this goes last
                      'admin',
                      ]

JQUERY_PLUGINS = ['select2/select2']

WEBAPP2_EXTRAS = {}