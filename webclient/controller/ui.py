# -*- coding: utf-8 -*-
'''
Created on Feb 5, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular

class Home(Angular):
  
  def respond(self):
      return {'hello' : 'world'}
      
      
register(('/', Home))



