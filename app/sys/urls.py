# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

from django.conf.urls import patterns, url
 
 
urlpatterns = patterns('app.sys.views',
    url(r'^$', 'index', name="index"),
)
