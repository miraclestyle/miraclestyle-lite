# -*- coding: utf-8 -*-

'''
Created on Jul 8, 2013

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module app.settings.py

'''

import os

# This is for key-based encryption we can change before we go into production
# - however changing this, automatically corrupts data (keys) and renders them unusable and undecryptable
SALT = u'salt'
# Separator for hashing, for example 
# Model.hash_create_key(key=value, key2=value2)
# with HASH_BINDER "-" would produce plaintext:
# {SALT}-value-value2
HASH_BINDER = u'-'

DEBUG = os.getenv('SERVER_SOFTWARE', '').startswith('Development')
# will still hold this as debug until full production
DEBUG = True
DO_LOGS = True

 
TEMPLATE_CACHE = 3600

if DEBUG:
   TEMPLATE_CACHE = 0

APPLICATIONS_INSTALLED = (
     'app.kernel',
)

SESSION_STORAGE = 'memcache'

USER_SESSION_KEY = 'user_key'
USER_AUTHENTICATED_KEYNAME = 'authenticated_user'
USER_ANONYMOUS_KEYNAME = 'anonymous_user'

# PERMISSIONS - these are installation permissions
USER_AUTHENTICATED_PERMISSIONS = (
    'create_active_store',
    'create_unpublished_catalog'
)
USER_ANONYMOUS_PERMISSIONS = (
    'view_published_catalog',
)

MAP_IDENTITIES = {
    'google' : 1,
    'facebook' : 2,
}

GOOGLE_OAUTH2 = {
   'client_id'    : '283384992095.apps.googleusercontent.com',
   'client_secret': '5MJ6bqGPbyD_bt2hYKFqShE2',              
   'scope'        : ['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email'],
   'auth_uri'     : 'https://accounts.google.com/o/oauth2/auth',
   'token_uri'    : 'https://accounts.google.com/o/oauth2/token',
   'redirect_uri' : False,

}

GOOGLE_OAUTH2_USERINFO = 'https://www.googleapis.com/oauth2/v1/userinfo'
 
FACEBOOK_OAUTH2 = {
   'client_id'    : '125702284258635',
   'client_secret': 'f5bcbcfa1bec6166bedb703d69911d43',              
   'scope'        : ['email'],
   'auth_uri'     : 'https://www.facebook.com/dialog/oauth',
   'token_uri'    : 'https://graph.facebook.com/oauth/access_token',
   'redirect_uri' : False,
}

FACEBOOK_OAUTH2_USERINFO = 'https://graph.facebook.com/me'
 

WEBAPP2_EXTRAS = {
    'webapp2_extras.sessions' : {
        'secret_key': 'd212k19f0k09sdkf009kfewwdw',
    },
    'webapp2_extras.i18n' : {
    'translations_path': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locale'),
    }
}

