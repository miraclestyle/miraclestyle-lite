# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webapp2 import Route

class InvalidRoute(Exception):
      pass

def register(prefix=None, *args):
    routes = []
    for arg in args:
        if isinstance(arg, (list, tuple)):
            if prefix:
                if isinstance(arg, tuple):
                   arg = list(arg)
                try:
                   arg[1] = '%s.%s' % (prefix, arg[1])
                except KeyError:
                   pass
            arg = Route(*arg)
        if isinstance(arg, dict):
            if prefix:
               arg['handler'] = '%s.%s' % (prefix, arg['handler'])
            arg = Route(**arg)
            
        if not isinstance(arg, Route):
           raise InvalidRoute
            
        routes.append(arg)
    return routes