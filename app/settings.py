# -*- coding: utf-8 -*-

'''
Created on Jul 8, 2013

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module settings.py

'''
import os

""" APP settings file. """

APPDIR = os.path.dirname(os.path.abspath(__file__))

# This is for key-based encryption we can change before we go into production
# - however changing this, automatically corrupts data (keys) and renders them unusable and undecryptable
SALT = u'salt'
# Separator for hashing, for example 
# Model.hash_create_key(key=value, key2=value2)
# with HASH_BINDER "-" would produce plaintext:
# {SALT}-value-value2
HASH_BINDER = u'-'

REAL_DEBUG = os.getenv('SERVER_SOFTWARE', '').startswith('Development')
DEBUG = True # REAL_DEBUG override because we are under development either way
DO_LOGS = True

NOTIFY_EMAIL = 'edis.sehalic@gmail.com'
 
# user settings
USER_AUTHENTICATED_KEYNAME = 'authenticated_user'
USER_ANONYMOUS_KEYNAME = 'anonymous_user'
ROOT_ADMINS = ('edis.sehalic@gmail.com', 'elvinkosova@gmail.com')

COMPANY_LOGO_BUCKET = 'user_input/company_logo'
CATALOG_IMAGE_BUCKET = 'user_input/catalog_image'
PRODUCT_TEMPLATE_BUCKET = 'user_input/product_template_image'
PRODUCT_INSTANCE_BUCKET = 'user_input/product_instance_image'

# task queue
OUTLET_TEMPLATES_PER_TASK = 10
OUTLET_RECIPIENTS_PER_TASK = 50

# records
RECORDS_PAGE = 10
SEARCH_PAGE = 10
 
_http = 'http://'

if os.environ.get('HTTPS') == 'on':
  _http = 'https://'
   

HOST = '%s%s' % (_http, os.environ.get('HTTP_HOST'))

# OAuth credentials, goes in format <PROVIDER>_OAUTH<VERSION>
GOOGLE_OAUTH2 = {
   'client_id'    : '283384992095.apps.googleusercontent.com',
   'client_secret': '5MJ6bqGPbyD_bt2hYKFqShE2',              
   'scope'        : " ".join(['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email']),
   'authorization_uri'     : 'https://accounts.google.com/o/oauth2/auth',
   'token_uri'    : 'https://accounts.google.com/o/oauth2/token',
   'redirect_uri' : '%s/login/google' % HOST,
   'type' : 1,
   'userinfo' : 'https://www.googleapis.com/oauth2/v1/userinfo',
}
 
FACEBOOK_OAUTH2 = {
   'client_id'    : '125702284258635',
   'client_secret': 'f5bcbcfa1bec6166bedb703d69911d43',              
   'scope'        : ",".join(['email']),
   'authorization_uri'     : 'https://www.facebook.com/dialog/oauth',
   'token_uri'    : 'https://graph.facebook.com/oauth/access_token',
   'redirect_uri' : '%s/login/facebook' % HOST,
   'type' : 2,
   'userinfo' : 'https://graph.facebook.com/me',
}

LOGIN_METHODS = {
    'google': {'oauth2': GOOGLE_OAUTH2},
    'facebook': {'oauth2': FACEBOOK_OAUTH2},
}