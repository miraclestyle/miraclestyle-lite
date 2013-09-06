# -*- coding: utf-8 -*-
'''
Created on Sep 5, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.routes import register


ROUTES = register('app.tests.controller', 
           (r'/', 'AngularTests', 'angular_tests', 'angular/home.html'),       
           (r'/unittests/<segment>', 'RunTests'), 
           (r'/angular_test', 'AngularTests', 'angular_tests', 'angular/test.html'),
           (r'/segment_tests/<segment>', 'Tests', 'segment_tests'),
)