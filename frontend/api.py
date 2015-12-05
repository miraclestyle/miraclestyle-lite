# -*- coding: utf-8 -*-
'''
Created on Sep 23, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json

from google.appengine.api import urlfetch

import settings


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
  kwds['url'] = settings.API_ENDPOINT
  return post(**kwds)


def model_meta():
  return post(url=settings.API_MODEL_META)
