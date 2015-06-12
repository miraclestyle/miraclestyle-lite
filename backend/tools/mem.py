# -*- coding: utf-8 -*-
'''
Created on Oct 8, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from webapp2_extras import local
from google.appengine.api import memcache

# Local memory for the app instance. storage must be released upon request completion.
mem_storage = local.Local()

'''
Wrapper for google memcache library, combined with in-memory cache (per-request and expiration after request execution)

'''

__all__ = ['mem_get', 'mem_set', 'mem_delete_multi', 'mem_set_multi', 'mem_temp_get', 'mem_temp_set', 'mem_storage', 
           'mem_temp_delete', 'mem_replace_multi', 'mem_tempcached', 'mem_add_multi', 'mem_forget_dead_hosts', 'mem_memcached',
           'mem_set_servers', 'mem_debuglog', 'mem_tmp_exists', 'mem_decr', 'mem_offset_multi', 'mem_disconnect_all', 
           'mem_replace', 'mem_incr', 'mem_flush_all', 'mem_delete', 'mem_add', 'mem_get_multi']


def mem_get(k, d=None, callback=None, **kwargs):
  '''
  k = identifier for cache,
  d = what not to expect,
  callback = expensive callable to execute and set its value into the memory, otherwise it will return 'd'.

  '''
  force = kwargs.pop('force', None)
  setkwargs = kwargs.pop('set', {})
  # If specified force=True, it will avoid in-memory check.
  if not force:
    tmp = mem_temp_get(k, d)
  else:
    tmp = d
  if tmp != d:
    return tmp
  else:
    tmp = memcache.get(k, **kwargs)
    if tmp is None:
      if callback:
        v = callback()
        mem_set(k, v, **setkwargs)
        return v
      return d
    mem_temp_set(k, tmp)
    return tmp


def mem_set(k, v, expire=0, **kwargs):
  mem_temp_set(k, v)
  memcache.set(k, v, expire, **kwargs)


def mem_delete(k):
  mem_temp_delete(k)
  memcache.delete(k)


def mem_temp_get(k, d=None):
  return getattr(mem_storage, k, d)


def mem_tmp_exists(k):
  return hasattr(mem_storage, k)


def mem_temp_set(k, v):
  setattr(mem_storage, k, v)


def mem_temp_delete(k):
  try:
    del mem_storage[k]
  except:
    pass


def mem_memcached(func, k=None, d=None):
  '''Decorator
  Usage:
  @memcached(k='heavy_processing_key')
  def heavy_processing():
  ...

  '''
  if k is None:
    k = func.__name__

  def dec(*args, **kwargs):
    v = mem_get(k, d)
    if v == d:
      v = func()
      mem_set(k, v)
      return v

  return dec


def mem_tempcached(func, k=None, d=None):
  '''Does temporary caching of the provided function.
  Temporary caching is the one that is done inside threads using webapp2_extras.local

  '''
  if k is None:
    k = func.__name__

  def dec(*args, **kwargs):
    v = mem_temp_get(k, d)
    if v == d:
      v = func()
      mem_temp_set(k, v)
      return v
  return dec


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
