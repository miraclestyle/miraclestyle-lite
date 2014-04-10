# -*- coding: utf-8 -*-
'''
Created on Oct 8, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from webapp2_extras import local
from google.appengine.api import memcache

# Local memory for the app instance. _local must be released upon request completion.
_local = local.Local()

"""
Wrapper for google memcache library, combined with in-memory cache (per-request and expiration after request execution)

"""

def set(k, v, expire=0, **kwargs):
  temp_memory_set(k, v)
  memcache.set(k, v, expire, **kwargs)

def get(k, d=None, callback=None, **kwargs):
  """'k' = identifier for cache,
  'd' = what not to expect,
  'callback' = expensive callable to execute and set its value into the memory, otherwise it will return 'd'.
  
  """
  force = kwargs.pop('force', None)
  setkwargs = kwargs.pop('set', {})
  # If specified force=True, it will avoid in-memory check.
  if not force:
    tmp = temp_memory_get(k, d)
  else:
    tmp = d
  
  if tmp != d:
    return tmp
  else:
    tmp = memcache.get(k, **kwargs)
    if tmp == None:
      if callback:
        v = callback()
        set(k, v, **setkwargs)
        return v
      return d
    temp_memory_set(k, tmp)
    return tmp

def delete(k):
  memcache.delete(k)
  temp_memory_delete(k)

def tempcached(func, k=None, d=None):
  """Does temporary caching of the provided function.
  Temporary caching is the one that is done inside threads using webapp2_extras.local
  
  """
  if k == None:
    k = func.__name__
  
  def dec(*args, **kwargs):
    v = temp_memory_get(k, d)
    if v == d:
      v = func()
      temp_memory_set(k, v)
      return v
  
  return dec

def memcached(func, k=None, d=None):
  """Decorator
  Usage:
  @memcached(k='heavy_processing_key')
  def heavy_processing():
  ...
  
  """
  if k == None:
    k = func.__name__
  
  def dec(*args, **kwargs):
    v = get(k, d)
    if v == d:
      v = func()
      set(k, v)
      return v
  
  return dec

def temp_memory_get(k, d=None):
  return getattr(_local, k, d)

def temp_memory_set(k, v):
  setattr(_local, k, v)

def temp_memory_delete(k):
  try:
    del _local[k]
  except:
    pass

# Comply with memcache from google app engine. These methods will be possibly overriden in favor of above methods.
set_servers = memcache.set_servers
disconnect_all = memcache.disconnect_all
forget_dead_hosts = memcache.forget_dead_hosts
debuglog = memcache.debuglog
get_multi = memcache.get_multi
set_multi = memcache.set_multi
add = memcache.add
add_multi = memcache.add_multi
replace = memcache.replace
replace_multi = memcache.replace_multi
delete_multi = memcache.delete_multi
incr = memcache.incr
decr = memcache.decr
flush_all = memcache.flush_all
offset_multi = memcache.offset_multi
