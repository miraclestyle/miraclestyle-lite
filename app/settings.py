# -*- coding: utf-8 -*-

'''
Created on Jul 8, 2013

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module app.settings.py

'''

import os

DEBUG = os.getenv('SERVER_SOFTWARE', '').startswith('Development')

TEMPLATE_CACHE = 3600

if DEBUG:
   TEMPLATE_CACHE = 0

APPLICATIONS_INSTALLED = (
     'app.kernel',
)

WEBAPP2_EXTRAS = {
    'webapp2_extras.sessions' : {
        'secret_key': 'd212k19f0k09sdkf009kfewwdw',
    },
    'webapp2_extras.i18n' : {
    'translations_path': os.path.join(os.path.abspath(__file__), 'locale'),
    }
}

