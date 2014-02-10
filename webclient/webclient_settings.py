# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
ACTIVE_CONTROLLERS = ('tests', 'auth', 'ui')

TEMPLATE_CACHE = 0

SESSION_USER_KEY = 'usr'

ANGULAR_MODULES = ['route', 'transition', 'tabs', 'collapse', 'accordion', 'modal', 'dropdown', 'select2',
                   'busy', 'checklist']
ANGULAR_COMPONENTS = ['home/home', 'srv/auth/login', 'srv/auth/account', 'opt/buyer/buyer']
JQUERY_PLUGINS = ['select2/select2']

WEBAPP2_EXTRAS = {
    'webapp2_extras.sessions' : {
        'secret_key': 'd212k19f0k09sdkf009kfewwdw',
        'backends' : {
            'webclient' : 'webclient.util.DatastoreSessionFactory'
         }
    },
}