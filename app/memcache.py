# -*- coding: utf-8 -*-
'''
Created on Jul 22, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import webapp2

from google.appengine.api import memcache

from app.core import logger
"""
 Wrapper for google memcache library, combined with in-memory cache (per-request and expiration after request execution)

"""
__all__ = ['set', 'get', 'delete', 'tempcached', 'memcached', 'temp_memory_get', 'temp_memory_set', 'temp_memory_delete']

def set(k, v, expire=0, **kwargs):
         logger('cache set %s' % k)
         temp_memory_set(k, v)
         memcache.set(k, v, expire, **kwargs)
         
def get(k, d=None, callback=None, **kwargs):
        
        """
        `k` = identifier for cache
        `d` = what not to expect
        `callback` = expensive callable to execute and set its value into the memory, otherwise it will return `d`
        """
        force = kwargs.pop('force', None)
        setkwargs = kwargs.pop('set', {})
        # if specified force=True, it will avoid in-memory check
        if not force:
           tmp = temp_memory_get(k, d)
        else:
           tmp = d
           
        if tmp != d:
           return tmp
        else:
           tmp = memcache.get(k, **kwargs)
           logger('cache get %s, got: %s' % (k, tmp))
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
        """
        Decorator
        usage:
        
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
    return getattr(webapp2._local, k, d)

def temp_memory_set(k, v):
    setattr(webapp2._local, k, v)
    
def temp_memory_delete(k):
    try:
      del webapp2._local[k]
    except:
      pass   

# comply with memcache from google app engine, these methods will possibly overriden in favor of above methods  
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
flush_all = memcache.get_stats
offset_multi = memcache.offset_multi