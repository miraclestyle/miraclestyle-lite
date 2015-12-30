# -*- coding: utf-8 -*-
'''
Created on Sep 23, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import webapp2
import settings

from google.appengine.api import urlfetch

def api_endpoint():
  request = webapp2.get_request()
  return settings.get_host_url(request.host) + '/api/endpoint'

def api_model_meta():
  request = webapp2.get_request()
  return settings.get_host_url(request.host) + '/api/model_meta'


def get(**kwds):
  kwds['method'] = urlfetch.GET
  return _exec(**kwds)


def post(**kwds):
  kwds['method'] = urlfetch.POST
  if 'payload' in kwds:
    kwds['payload']['_csrf'] = '_____skipcsrf_____'
    kwds['payload'] = json.dumps(kwds['payload'])
  if 'headers' not in kwds:
    kwds['headers'] = {}
  kwds['headers']['Content-Type'] = 'application/json;utf=8;'
  return _exec(**kwds)


def _exec(**kwds):
  if 'deadline' not in kwds:
    kwds['deadline'] = 60
  response = urlfetch.fetch(**kwds)
  return json.loads(response.content)


def endpoint(**kwds):
  kwds['url'] = api_endpoint()
  return post(**kwds)


def model_meta():
  return post(url=api_model_meta())
