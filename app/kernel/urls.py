# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.routes import register

ROUTES = register('app.kernel.controller',
     (r'/', 'Home'),
)