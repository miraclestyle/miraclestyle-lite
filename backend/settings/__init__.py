# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import os

'''Settings file for backend module'''

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST_NAME = os.environ.get('DEFAULT_VERSION_HOSTNAME', os.environ.get('HTTP_HOST'))

MIRACLESTYLE_SETTINGS = {
  'DEBUG': False,
  'FORCE_SSL': True,
  'CATALOG_UNPUBLISHED_LIFE': 15,
  'CATALOG_DISCONTINUED_LIFE': 15,
  'ORDER_CART_LIFE': 15,
  'ORDER_UNPAID_LIFE': 15,
  'ORDER_CRON_NOTIFY_TIMER': {'hours': 0, 'minutes': 10, 'seconds': 0},
  'BUCKET_PATH': 'themiraclestyle.appspot.com',
  'PAYPAL_WEBSCR': 'https://www.paypal.com/cgi-bin/webscr',
  'GOOGLE_OAUTH2': {
    'client_id': '794606722914-tue5sq5v7b459lq4rorvtm98m421pioj.apps.googleusercontent.com', 
    'client_secret': 'pvUWETG11c8mRh1IwN0qjYnm'
  }
}

DEFAULT_HOST_SETTINGS = {
  'DEBUG': True,
  'FORCE_SSL': False,
  'LAG': False,
  'CATALOG_UNPUBLISHED_LIFE': 1,
  'CATALOG_DISCONTINUED_LIFE': 1,
  'ORDER_CART_LIFE': 1,
  'ORDER_UNPAID_LIFE': 1,
  'ORDER_CRON_NOTIFY_TIMER': {'hours': 0, 'minutes': 0, 'seconds': 30},
  'BUCKET_PATH': 'themiraclestyle-testing-site.appspot.com',
  'PAYPAL_WEBSCR': 'https://www.sandbox.paypal.com/cgi-bin/webscr',
  'GOOGLE_OAUTH2': {
    'client_id': '262487344336-vkpvegjrp7q3isfr73vod7q9m0piu9gd.apps.googleusercontent.com', 
    'client_secret': 'AtUlgzsKycfOueKYUrX6CYIn'
  },
  'FACEBOOK_OAUTH2': {
    'client_id': '114231673409', 
    'client_secret': '7a467a6d24ba35343d09ce672faf98c2'
  },
  'LINKEDIN_OAUTH2': {
    'client_id': '77xclva9s9qsex', 
    'client_secret': 'cYHLJehkmDGm1j9n'
  }
}
HOSTS_SPECIFIC_SETTINGS = {
  'localhost:9982': {
    'FORCE_SSL': False,
    'LAG': False
  },
  'themiraclestyle-testing-site.appspot.com': {
    'FORCE_SSL': True
  },
  'themiraclestyle.appspot.com': MIRACLESTYLE_SETTINGS,
  'miraclestyle.com': MIRACLESTYLE_SETTINGS,
  'www.miraclestyle.com': MIRACLESTYLE_SETTINGS
}

HOST_SPECIFIC_SETTINGS = HOSTS_SPECIFIC_SETTINGS.get(HOST_NAME, DEFAULT_HOST_SETTINGS)
for k, v in DEFAULT_HOST_SETTINGS.items():
  if k not in HOST_SPECIFIC_SETTINGS:
    HOST_SPECIFIC_SETTINGS[k] = v

# Server side config
FORCE_SSL = HOST_SPECIFIC_SETTINGS['FORCE_SSL']
DEVELOPMENT_SERVER = os.getenv('SERVER_SOFTWARE', '').startswith('Development')
SILENCE_STDOUT = False
DO_LOGS = True  # logging on application level
PROFILE_SLOW_ACTIONS = True
PROFILING = False  # profiling of every function call using cProfile. Debug must be on
PROFILING_SORT = ('cumulative', )  # 'time'

DEBUG = HOST_SPECIFIC_SETTINGS['DEBUG']
LAG = HOST_SPECIFIC_SETTINGS['LAG']

CATALOG_UNPUBLISHED_LIFE = HOST_SPECIFIC_SETTINGS['CATALOG_UNPUBLISHED_LIFE']
CATALOG_DISCONTINUED_LIFE = HOST_SPECIFIC_SETTINGS['CATALOG_DISCONTINUED_LIFE']
ORDER_CART_LIFE = HOST_SPECIFIC_SETTINGS['ORDER_CART_LIFE']
ORDER_UNPAID_LIFE = HOST_SPECIFIC_SETTINGS['ORDER_UNPAID_LIFE']
ORDER_CRON_NOTIFY_TIMER = HOST_SPECIFIC_SETTINGS['ORDER_CRON_NOTIFY_TIMER']

PAYPAL_WEBSCR = HOST_SPECIFIC_SETTINGS['PAYPAL_WEBSCR']

def get_host_url(hostname):
  http = 'http://'
  if os.environ.get('HTTPS') == 'on' or FORCE_SSL:
    http = 'https://'
  return '%s%s' % (http, hostname)

# Cloud storage path settings.
BUCKET_PATH = HOST_SPECIFIC_SETTINGS['BUCKET_PATH']

# OAuth credentials, goes in format <PROVIDER>_OAUTH<VERSION>
GOOGLE_OAUTH2 = {
    'client_id': HOST_SPECIFIC_SETTINGS['GOOGLE_OAUTH2']['client_id'],
    'client_secret': HOST_SPECIFIC_SETTINGS['GOOGLE_OAUTH2']['client_secret'],
    'scope': " ".join(['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email']),
    'authorization_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://accounts.google.com/o/oauth2/token',
    'redirect_uri': '/api/account/login/1',
    'type': '1',
    'account_info': 'https://www.googleapis.com/oauth2/v1/userinfo',
}

FACEBOOK_OAUTH2 = {
    'client_id': HOST_SPECIFIC_SETTINGS['FACEBOOK_OAUTH2']['client_id'],
    'client_secret': HOST_SPECIFIC_SETTINGS['FACEBOOK_OAUTH2']['client_secret'],
    'scope': ",".join(['email']),
    'authorization_uri': 'https://www.facebook.com/dialog/oauth',
    'token_uri': 'https://graph.facebook.com/oauth/access_token',
    'redirect_uri': '/api/account/login/2',
    'type': '2',
    'account_info': 'https://graph.facebook.com/v2.5/me?fields=id,email',
}

LINKEDIN_OAUTH2 = {
    'client_id': HOST_SPECIFIC_SETTINGS['LINKEDIN_OAUTH2']['client_id'],
    'client_secret': HOST_SPECIFIC_SETTINGS['LINKEDIN_OAUTH2']['client_secret'],
    'scope': ",".join(['r_basicprofile', 'r_emailaddress']),
    'authorization_uri': 'https://www.linkedin.com/uas/oauth2/authorization',
    'token_uri': 'https://www.linkedin.com/uas/oauth2/accessToken',
    'redirect_uri': '/api/account/login/3',
    'type': '3',
    'account_info': 'https://api.linkedin.com/v1/people/~:(firstName,lastName,id,email-address)?format=json',
    'header': True
}

########## Global settings ##########
LOGIN_METHODS = [GOOGLE_OAUTH2, FACEBOOK_OAUTH2, LINKEDIN_OAUTH2]
NOTIFY_EMAIL = 'Miraclestyle <notify-noreply@miraclestyle.com>'
ROOT_ADMINS = ('elvin@miraclestyle.com', 'edis@miraclestyle.com')
SEARCH_PAGE = 10
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'  # This formating is used for input and output.
MAX_MESSAGE_SIZE = 1024
# Configuration files
ETC_DATA_DIR = os.path.join(ROOT_DIR, 'etc', 'data')
UOM_DATA_FILE = os.path.join(ETC_DATA_DIR, 'uom.xml')
LOCATION_DATA_FILE = os.path.join(ETC_DATA_DIR, 'location.xml')
CURRENCY_DATA_FILE = os.path.join(ETC_DATA_DIR, 'currency.xml')
PRODUCT_CATEGORY_DATA_FILE = os.path.join(ETC_DATA_DIR, 'taxonomy.txt')
# BLOB Handling
BLOBKEYMANAGER_KEY = '_BLOBKEYMANAGER'
# Payment Methods
AVAILABLE_PAYMENT_METHODS = ('stripe',) # only stripe is available atm
AES_KEY = '7XQg6j9ZHZByzckr0DzjXQPp4Oug3FXC' # 16, 24 or 32 bytes allowed
ENCRYPTION_PREFIX = 'encrypted'
# HTTP client related configs
CSRF_SALT = '21482499fsd9i348124982ufs89j9f2qofi4knsgye8w9djqwiodnjenj'
CSRF_TOKEN_KEY = 'csrf_token'
COOKIE_SECRET = '3184ur9gejgirtgrkg493itkopgdfaklfnsgjkfgnei'
COOKIE_AUTH_KEY = 'auth'
#####################################