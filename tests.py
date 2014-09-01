# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import time
import urllib2

while True:
  time.sleep(0.2)
  urllib2.urlopen('http://localhost:9982/Tests/Test1?pp=foo6')