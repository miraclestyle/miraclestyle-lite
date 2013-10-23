# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
ACTIVE_CONTROLLERS = ('tests', 'home', 'auth', 'admin')

TEMPLATE_CACHE = 0

SESSION_USER_KEY = 'usr'

WEBAPP2_EXTRAS = {
    'webapp2_extras.sessions' : {
        'secret_key': 'd212k19f0k09sdkf009kfewwdw',
        'backends' : {
            'webclient' : 'webclient.util.DatastoreSessionFactory'
         }
    },
}