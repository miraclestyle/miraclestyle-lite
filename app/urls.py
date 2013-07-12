# -*- coding: utf-8 -*-

'''
Created on July 8, 2013

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module app.urls.py

'''

from django.utils.importlib import import_module
from django.conf import settings

def urlpatterns_module_exists(module_name):
    try:
       module = import_module('%s.urls' % module_name)
    except ImportError:
        return False
    else:
        return module

urlpatterns = [] 

if len(settings.INSTALLED_APPS):
    for app in settings.INSTALLED_APPS:
        module = urlpatterns_module_exists(app)
        if module:
            patts = getattr(module, 'urlpatterns', None)
            if patts:
               urlpatterns += patts