# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import os

''' Settings file for backend module '''

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'  # This formating is used for input and output.

DEVELOPMENT_SERVER = os.getenv('SERVER_SOFTWARE', '').startswith('Development')
DEBUG = True
DO_LOGS = True

NOTIFY_EMAIL = 'notify-noreply@miraclestyle.com'  # Password: xZa9hv8nbWyzk67boq4Q0

# Task queue settings.
OUTLET_TEMPLATES_PER_TASK = 10
RECIPIENTS_PER_TASK = 50

# Cron settings.
DOMAINS_PER_CRON = 10
SETUP_ELAPSED_TIME = 15

# User settings.
ROOT_ADMINS = ('edis.sehalic@gmail.com', 'elvinkosova@gmail.com')

# Record settings.
RECORDS_PAGE = 10
SEARCH_PAGE = 10

# Blob cloud storage settings.
BUCKET_PATH = 'x-arcanum-801.appspot.com'

# Catalog settings.
CATALOG_PAGE = 10
CATALOG_UNPUBLISHED_LIFE = 1  # @todo This will be something like 7 days
CATALOG_DISCONTINUED_LIFE = 1  # @todo This will be something like 120-180 days
CATALOG_INDEX = 'catalogs'
CATALOG_DOCUMENTS_PER_INDEX = 200

# How many days does user have to leave feedback
FEEDBACK_ALLOWED_DAYS = 7

HOST_URL = None
if DEVELOPMENT_SERVER:
  HOST_URL = 'http://128.65.105.64:9982'
  HOST_URL = 'http://localhost:9982'

if HOST_URL is None:
  def __discover_host_url():
    http = 'http://'
    if os.environ.get('HTTPS') == 'on':
      http = 'https://'
    return '%s%s' % (http, os.environ.get('DEFAULT_VERSION_HOSTNAME', os.environ.get('HTTP_HOST')))
  HOST_URL = __discover_host_url()

ETC_DATA_DIR = os.path.join(ROOT_DIR, 'etc', 'data')

UOM_DATA_FILE = os.path.join(ETC_DATA_DIR, 'uom.xml')
LOCATION_DATA_FILE = os.path.join(ETC_DATA_DIR, 'location.xml')
CURRENCY_DATA_FILE = os.path.join(ETC_DATA_DIR, 'currency.xml')
ORDER_ACCOUNT_CHART_DATA_FILE = os.path.join(ETC_DATA_DIR, 'order_account_chart.xml')
PRODUCT_CATEGORY_DATA_FILE = os.path.join(ETC_DATA_DIR, 'taxonomy.txt')


BLOBKEYMANAGER_KEY = '_BLOBKEYMANAGER'

# OAuth credentials, goes in format <PROVIDER>_OAUTH<VERSION>
GOOGLE_OAUTH2 = {
   'client_id'    : '659759206787-v5nj4qd1k6trkv6kttkc9rt92ojkcvtu.apps.googleusercontent.com',
   'client_secret': 'NiPPgts3FGMcICryDRn05X3x',
   'scope'        : " ".join(['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email']),
   'authorization_uri'     : 'https://accounts.google.com/o/oauth2/auth',
   'token_uri'    : 'https://accounts.google.com/o/oauth2/token',
   'redirect_uri' : '%s/api/account/login/google' % HOST_URL,
   'type' : 1,
   'accountinfo' : 'https://www.googleapis.com/oauth2/v1/userinfo',
}

FACEBOOK_OAUTH2 = {
   'client_id'    : '125702284258635',
   'client_secret': 'f5bcbcfa1bec6166bedb703d69911d43',
   'scope'        : ",".join(['email']),
   'authorization_uri'     : 'https://www.facebook.com/dialog/oauth',
   'token_uri'    : 'https://graph.facebook.com/oauth/access_token',
   'redirect_uri' : '%s/api/account/login/facebook' % HOST_URL,
   'type' : 2,
   'accountinfo' : 'https://graph.facebook.com/me',
}

LOGIN_METHODS = {
    'google': {'oauth2': GOOGLE_OAUTH2},
    'facebook': {'oauth2': FACEBOOK_OAUTH2},
}

PAYPAL_WEBSCR_SANDBOX = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
PAYPAL_WEBSCR = 'https://www.paypal.com/cgi-bin/webscr'
PAYPAL_SANDBOX = True