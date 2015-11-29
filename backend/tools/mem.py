# -*- coding: utf-8 -*-
'''
Created on Oct 8, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import webapp2
from webapp2_extras import local
from google.appengine.api import memcache

class LocalStorage(object):
  pass

'''Wrapper for google memcache library, combined with in-memory cache (per-request and expiration after request execution)'''

__all__ = ['mem_get', 'mem_set', 'mem_delete_multi', 'mem_set_multi', 'mem_temp_get', 'mem_temp_set',
           'mem_temp_delete', 'mem_replace_multi', 'mem_add_multi', 'mem_forget_dead_hosts', 'mem_set_servers',
           'mem_debuglog', 'mem_temp_exists', 'mem_decr', 'mem_offset_multi', 'mem_disconnect_all',
           'mem_replace', 'mem_incr', 'mem_flush_all', 'mem_delete', 'mem_add', 'mem_get_multi', 'mem_rpc_get', 'mem_rpc_set', 'mem_rpc_delete']


def mem_get(key, default=None, callback=None, **kwargs):
  '''
  key = identifier for cache,
  default = what not to expect,
  callback = expensive callable to execute and set its value into the memory, otherwise it will return 'd'.

  '''
  force = kwargs.pop('force', None)
  set_kwargs = kwargs.pop('set', {})
  # If specified force=True, it will avoid in-memory check.
  if not force:
    tmp = mem_temp_get(key, default)
  else:
    tmp = default
  if tmp != default:
    return tmp
  else:
    tmp = memcache.get(key, **kwargs)
    if tmp is None:
      if callback:
        value = callback()
        mem_set(key, value, **set_kwargs)
        return value
      return default
    mem_temp_set(key, tmp)
    return tmp


def mem_set(key, value, expire=0, **kwargs):
  mem_temp_set(key, value)
  memcache.set(key, value, expire, **kwargs)


def mem_delete(key):
  mem_temp_delete(key)
  memcache.delete(key)


def get_storage():
  request = webapp2.get_request()
  if not hasattr(request, 'localstorage'):
    storage = LocalStorage()
    setattr(request, 'localstorage', storage)
  else:
    storage = getattr(request, 'localstorage')
  return storage


def mem_temp_get(key, default=None):
  return getattr(get_storage(), key, default)


def mem_temp_exists(key):
  return hasattr(get_storage(), key)


def mem_temp_set(key, value):
  setattr(get_storage(), key, value)


def mem_temp_delete(key):
  try:
    del get_storage()[key]
  except:
    pass


# Comply with memcache from google app engine. These methods will be possibly overriden in favor of above methods.
mem_set_servers = memcache.set_servers
mem_disconnect_all = memcache.disconnect_all
mem_forget_dead_hosts = memcache.forget_dead_hosts
mem_debuglog = memcache.debuglog
mem_get_multi = memcache.get_multi
mem_set_multi = memcache.set_multi
mem_add = memcache.add
mem_add_multi = memcache.add_multi
mem_replace = memcache.replace
mem_replace_multi = memcache.replace_multi
mem_delete_multi = memcache.delete_multi
mem_incr = memcache.incr
mem_decr = memcache.decr
mem_offset_multi = memcache.offset_multi
mem_flush_all = memcache.flush_all
mem_rpc_get = memcache.get
mem_rpc_set = memcache.set
mem_rpc_delete = memcache.delete