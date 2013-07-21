# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.routes import register

ROUTES = register('app.kernel.controller',
     (r'/login/<segment>', 'Login', 'login'),
     (r'/login/<segment>/<provider>', 'Login', 'login'),
     (r'/tests', 'UnitTests', 'tests'),
     (r'/segment_tests/<segment>', 'Tests', 'segment_tests'),
)