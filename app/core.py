# -*- coding: utf-8 -*-
'''
Created on Jul 12, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import sys
import logging
import webapp2

from webapp2_extras import sessions
from webapp2_extras import i18n
 

def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in range(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                              "package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]

def module_exists(module_name):
    try:
       logging.info('Loading module: ' + module_name)
       module = import_module(module_name)
    except ImportError:
        return False
    else:
        return module

class RequestHandler(webapp2.RequestHandler):
    
    def dispatch(self):
        
        locale = 'en_US'
        i18n.get_i18n().set_locale(locale)
  
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(backend='memcache')
    
