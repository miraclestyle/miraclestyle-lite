# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
ACTIVE_CONTROLLERS = ('tests', 'auth', 'ui')

TEMPLATE_CACHE = 0

SESSION_USER_KEY = 'usr'

ANGULAR_MODULES = ['ui-router', 'ngStorage', 'transition', 'collapse', 'accordion', 'modal', 'select2',
                   'busy', 'checklist']
ANGULAR_COMPONENTS = ['home/home', 'srv/auth/account', 'srv/auth/app', 'opt/buyer/buyer']
JQUERY_PLUGINS = ['select2/select2']

WEBAPP2_EXTRAS = {}