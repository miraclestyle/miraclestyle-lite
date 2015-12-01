# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json
import urlparse
import urllib

from google.appengine.api import urlfetch


__all__ = ['OAuth2ResourceError', 'OAuth2Client']


'''Simple generic client OAUTH2 client class for retrieving access tokens.'''


class OAuth2ResourceError(Exception):
  pass


def _build_url(base, additional_params=None):
  '''Construct an URL from the base, containing all parameters in
  the query portion of the base plus any additional parameters.
  'base' parameter: Base URL.
  'base' type: String.
  'additional_params' parameter: Additional query parameters to include.
  'additional_params' type: Dictionary.
  return type: String.

  '''
  url = urlparse.urlparse(base)
  query_params = {}
  query_params.update(urlparse.parse_qsl(url.query, True))
  if additional_params is not None:
    query_params.update(additional_params)
    for key, value in additional_params.iteritems():
      if value is None:
        query_params.pop(key)
  return urlparse.urlunparse((url.scheme, url.netloc,
                              url.path, url.params,
                              urllib.urlencode(query_params),
                              url.fragment))


class OAuth2Client(object):

  def __init__(self, client_id, client_secret, redirect_uri, authorization_uri, token_uri, access_token=None, **kwds):
    '''Constructor for OAuth 2.0 Client.
    'client_id' parameter: Client ID.
    'client_id' type: String.
    'client_secret' parameter: Client secret.
    'client_secret' type: String.
    'redirect_uri' parameter: Client redirect URI: handle provider response.
    'redirect_uri' type: String.
    'authorization_uri' parameter: Provider authorization URI.
    'authorization_uri' type: String
    'token_uri' parameter: Provider token URI.
    'token_uri' type: String.

    '''
    self.client_id = client_id
    self.client_secret = client_secret
    self.redirect_uri = redirect_uri
    self.authorization_uri = authorization_uri
    self.token_uri = token_uri
    self.access_token = access_token
    self.scope = kwds.get('scope')

  def resource_request(self, method=None, url=None, data=None, status=None):
    '''Uses google urlfetch library for performing http requests to external resources.
    This method will return None if the response status code is not equal 'status'.
    Default value for 'status' is 200.

    '''
    if method is None:
      method = 'GET'
    if data is None:
      data = {}
    if status is None:
      status = 200
    method = getattr(urlfetch, method.upper())
    url = _build_url(url, {'access_token': self.access_token})
    try:
      if data is not None:
        data = urllib.urlencode(data)
      response = urlfetch.fetch(url=url, payload=data, deadline=60, method=method)
      if response.status_code == status:
        return json.loads(response.content)
      else:
        raise OAuth2ResourceError(getattr(response, 'content', None))
    except (TypeError, OAuth2ResourceError):
      return None

  @property
  def default_response_type(self):
    return 'code'

  @property
  def default_grant_type(self):
    return 'authorization_code'

  def http_post(self, url, data=None):
    '''POST to URL and get result as a response object.
    'url' parameter: URL to POST.
    'url' type: String.
    'data' paramter: Data to send in the form body.
    'data' type: String.
    return type: requests.Response.

    '''
    if not url.startswith('https://'):
      raise ValueError('Protocol must be HTTPS, invalid URL: %s' % url)
    data = urllib.urlencode(data)
    response = urlfetch.fetch(url=url, payload=data, method=urlfetch.POST, deadline=60, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if response and response.status_code == 200:
      try:
        return json.loads(response.content)
      except ValueError as e:
        return dict(urlparse.parse_qsl(response.content))
    return None

  def get_authorization_code_uri(self, **params):
    '''Construct a full URL that can be used to obtain an authorization
    code from the provider authorization_uri. Use this URI in a client
    frame to cause the provider to generate an authorization code.
    return type: String.

    '''
    if 'response_type' not in params:
      params['response_type'] = self.default_response_type
    params.update({'client_id': self.client_id,
                   'scope': self.scope,
                   'redirect_uri': self.redirect_uri})
    return _build_url(self.authorization_uri, params)

  def get_token(self, code, **params):
    '''Get an access token from the provider token URI.
    'code' parameter: Authorization code.
    'code' type: String.
    return: Dictionary containing access token, refresh token, etc.
    return type: Dictionary.

    '''
    params['code'] = code
    if 'grant_type' not in params:
      params['grant_type'] = self.default_grant_type
    params.update({'client_id': self.client_id,
                   'client_secret': self.client_secret,
                   'redirect_uri': self.redirect_uri})
    response = self.http_post(self.token_uri, params)
    if response:
      self.access_token = response['access_token']
    return response
