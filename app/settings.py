# -*- coding: utf-8 -*-

'''
Created on Jul 8, 2013

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module app.settings.py

'''

import os

DEBUG = os.getenv('SERVER_SOFTWARE', '').startswith('Development')

TEMPLATE_CACHE = 3600

if DEBUG:
   TEMPLATE_CACHE = 0

APPLICATIONS_INSTALLED = (
     'app.kernel',
)