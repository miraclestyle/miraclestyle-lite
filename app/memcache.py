# -*- coding: utf-8 -*-
'''
Created on Jul 22, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import webapp2

from google.appengine.api import memcache

from app.core import logger

__all__ = ['set', 'get', 'delete', 'tempcached', 'memcached', 'get_temp_memory', 'set_temp_memory', 'delete_temp_memory']

def set(k, v, expire=0, **kwargs):
         logger('cache set %s' % k)
         set_temp_memory(k, v)
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
           tmp = get_temp_memory(k, d)
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
          
           set_temp_memory(k, tmp)
           return tmp  

def delete(k):
        memcache.delete(k)
        delete_temp_memory(k)
        
def tempcached(func, k=None, d=None):
        if k == None:
           k = func.__name__
           
        def dec(*args, **kwargs):
            v = get_temp_memory(k, d)
            if v == d:
               v = func() 
               set_temp_memory(k, v)
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
         
def get_temp_memory(k, d=None):
    return getattr(webapp2._local, k, d)

def set_temp_memory(k, v):
    setattr(webapp2._local, k, v)
    
def delete_temp_memory(k):
    try:
      del webapp2._local[k]
    except:
      pass   