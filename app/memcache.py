# -*- coding: utf-8 -*-
'''
Created on Jul 22, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import webapp2
import logging
 
from google.appengine.api import memcache

from app import settings

class smart_cache:
    """
    Smart cache combines in-memory webapp2._local and google memcache to maximize performance as well some goddies
    """
  
    @staticmethod
    def get(k, d=None, callback=None, **kwargs):
        
        """
        `k` = identifier for cache
        `d` = what not to expect
        `callback` = expensive callable to execute and set its value into the memory, otherwise it will return `d`
        """
        force = kwargs.get('force', None)
        # if specified force=True, it will avoid in-memory check
        if not force:
           tmp = get_temp_memory(k, d)
        else:
           tmp = d
           
        if tmp != d:
           return tmp
        else:
           tmp = memcache.get(k)
           if settings.DO_LOGS:
              logging.info('cache get %s, got: %s' % (k, tmp))
           if tmp == None:
              if callback:
                 v = callback()
                 smart_cache.set(k, v)
                 return v
              return d
          
           set_temp_memory(k, tmp)
           return tmp        
    
    @staticmethod
    def set(k, v, expire=0):
         logging.info('cache set %s' % k)
         set_temp_memory(k, v)
         memcache.set(k, v, expire)        
    
    @staticmethod
    def delete(k):
        memcache.delete(k)
        try:
            del webapp2.local[k]
        except:
            pass   
     
def get_temp_memory(k, d=None):
    return getattr(webapp2._local, k, d)

def set_temp_memory(k, v):
    setattr(webapp2._local, k, v)