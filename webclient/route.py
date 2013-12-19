# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webapp2 import Route

__ROUTES = []

class InvalidRouteError(Exception):
      pass
  
class AngularRoute(Route):
    
    """
    Angular compatible route
    """
    
    angular_path = None
    angular_controller = None
    angular_template = None
    angular_config = {}
    
    def _angular_make_path(self, p):
        p = p.replace('<', ':')
        p = p.replace('>', '')
        return p
    
    def _angular_make_controller(self, c):
        if not isinstance(c, basestring):
            c = c.__name__
        li = c.split('.')
        li_last = li[-1]
        del li[-1]
        
        co = [k.title() for k in li]
        co.append(li_last)
        
        return u"".join(co)
      
    def __init__(self, template, handler=None, name=None, angular_template=False, angular_config={}, build_only=False):
        """Initializes this route."""
        super(AngularRoute, self).__init__(template, handler, name, build_only)
        
        self.angular_config = angular_config
        self.angular_path = self._angular_make_path(template)
        self.angular_controller = self._angular_make_controller(handler)
        self.angular_template = angular_template
        
def get_routes():
  
    global __ROUTES
    
    return __ROUTES        

def register(*args):
  
    global __ROUTES
 
    prefix = None
  
    for arg in args:
        if isinstance(arg, basestring):
           prefix = arg
           continue
       
        if isinstance(arg, (list, tuple)):
            if prefix:
                if isinstance(arg, tuple):
                   arg = list(arg)
                try:
                   arg[1] = '%s.%s' % (prefix, arg[1])
                except KeyError:
                   pass
            arg = AngularRoute(*arg)
        if isinstance(arg, dict):
            if prefix:
               arg['handler'] = '%s.%s' % (prefix, arg['handler'])
            arg = AngularRoute(**arg)
            
        if not isinstance(arg, AngularRoute):
           raise InvalidRouteError
    
        __ROUTES.append(arg)
    return __ROUTES