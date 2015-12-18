# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import os

'''Settings file for backend module'''

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST_NAME = os.environ.get('DEFAULT_VERSION_HOSTNAME', os.environ.get('HTTP_HOST'))

DEFAULT_HOST_SETTINGS = {
  'DEBUG': True,
  'FORCE_SSL': False,
  'LAG': False,
  'BUCKET_PATH': 'themiraclestyle-testing-site.appspot.com',
  'PAYPAL_WEBSCR': 'https://www.sandbox.paypal.com/cgi-bin/webscr'
}
HOSTS_SPECIFIC_SETTINGS = {
  'localhost:9982': {
    'FORCE_SSL': False
  },
  'themiraclestyle-testing-site.appspot.com': {
    'FORCE_SSL': True
  },
  'miraclestyle.com': {
    'DEBUG': False,
    'FORCE_SSL': True,
    'BUCKET_PATH': 'themiraclestyle.appspot.com',
    'PAYPAL_WEBSCR': 'https://www.paypal.com/cgi-bin/webscr'
  }
}

HOST_SPECIFIC_SETTINGS = HOSTS_SPECIFIC_SETTINGS.get(HOST_NAME, DEFAULT_HOST_SETTINGS)
for k, v in DEFAULT_HOST_SETTINGS.items():
  if k not in HOST_SPECIFIC_SETTINGS:
    HOST_SPECIFIC_SETTINGS[k] = v

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'  # This formating is used for input and output.
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
# Notify
NOTIFY_EMAIL = 'Miraclestyle <notify-noreply@miraclestyle.com>'  # Password: xZa9hv8nbWyzk67boq4Q0

# User settings.
ROOT_ADMINS = ('elvin@miraclestyle.com', 'edis@miraclestyle.com')

SEARCH_PAGE = 10

CATALOG_UNPUBLISHED_LIFE = 1  # @note This will be something like 7 days
CATALOG_DISCONTINUED_LIFE = 1  # @note This will be something like 120-180 days
CATALOG_INDEX = 'catalogs'
CATALOG_DOCUMENTS_PER_INDEX = 200

ORDER_CART_LIFE = 1  # @note This will be something like 15 days
ORDER_UNPAID_LIFE = 1  # @note This will be something like 30 days

MAX_MESSAGE_SIZE = 1024

def get_host_url():
  http = 'http://'
  if os.environ.get('HTTPS') == 'on' or FORCE_SSL:
    http = 'https://'
  return '%s%s' % (http, HOST_NAME)

HOST_URL = None
if HOST_URL is None:
  HOST_URL = get_host_url()

# Configuration files
ETC_DATA_DIR = os.path.join(ROOT_DIR, 'etc', 'data')

UOM_DATA_FILE = os.path.join(ETC_DATA_DIR, 'uom.xml')
LOCATION_DATA_FILE = os.path.join(ETC_DATA_DIR, 'location.xml')
CURRENCY_DATA_FILE = os.path.join(ETC_DATA_DIR, 'currency.xml')
PRODUCT_CATEGORY_DATA_FILE = os.path.join(ETC_DATA_DIR, 'taxonomy.txt')

# BLOB Handling
BLOBKEYMANAGER_KEY = '_BLOBKEYMANAGER'
# Cloud storage path settings.
BUCKET_PATH = HOST_SPECIFIC_SETTINGS['BUCKET_PATH']
OAUTH2_REDIRECT_URI = HOST_SPECIFIC_SETTINGS.get('OAUTH2_REDIRECT_URI', HOST_URL)

# OAuth credentials, goes in format <PROVIDER>_OAUTH<VERSION>
GOOGLE_OAUTH2 = {
    'client_id': '262487344336-vkpvegjrp7q3isfr73vod7q9m0piu9gd.apps.googleusercontent.com',
    'client_secret': 'AtUlgzsKycfOueKYUrX6CYIn',
    'scope': " ".join(['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email']),
    'authorization_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://accounts.google.com/o/oauth2/token',
    'redirect_uri': '%s/api/account/login/1' % OAUTH2_REDIRECT_URI,
    'type': '1',
    'account_info': 'https://www.googleapis.com/oauth2/v1/userinfo',
}

FACEBOOK_OAUTH2 = {
    'client_id': '114231673409',
    'client_secret': '7a467a6d24ba35343d09ce672faf98c2',
    'scope': ",".join(['email']),
    'authorization_uri': 'https://www.facebook.com/dialog/oauth',
    'token_uri': 'https://graph.facebook.com/oauth/access_token',
    'redirect_uri': '%s/api/account/login/2' % OAUTH2_REDIRECT_URI,
    'type': '2',
    'account_info': 'https://graph.facebook.com/v2.5/me?fields=id,email',
}

LINKEDIN_OAUTH2 = {
    'client_id': '77xclva9s9qsex',
    'client_secret': 'cYHLJehkmDGm1j9n',
    'scope': ",".join(['r_basicprofile', 'r_emailaddress']),
    'authorization_uri': 'https://www.linkedin.com/uas/oauth2/authorization',
    'token_uri': 'https://www.linkedin.com/uas/oauth2/accessToken',
    'redirect_uri': '%s/api/account/login/3' % OAUTH2_REDIRECT_URI,
    'type': '3',
    'account_info': 'https://api.linkedin.com/v1/people/~:(firstName,lastName,id,email-address)?format=json',
    'header': True
}

LOGIN_METHODS = [GOOGLE_OAUTH2, FACEBOOK_OAUTH2, LINKEDIN_OAUTH2]

# Payment Methods
AVAILABLE_PAYMENT_METHODS = ('paypal',)

# PAYPAL
PAYPAL_WEBSCR = HOST_SPECIFIC_SETTINGS['PAYPAL_WEBSCR']
# HTTP client related configs
CSRF_SALT = '21482499fsd9i348124982ufs89j9f2qofi4knsgye8w9djqwiodnjenj'
CSRF_TOKEN_KEY = 'csrf_token'
COOKIE_SECRET = '3184ur9gejgirtgrkg493itkopgdfaklfnsgjkfgnei'
COOKIE_AUTH_KEY = 'auth'
