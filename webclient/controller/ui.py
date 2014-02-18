# -*- coding: utf-8 -*-
'''
Created on Feb 5, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient import handler

class Home(handler.Angular):
  
  def respond(self):
      return {'hello' : 'world'}
      
      
handler.register(('/', Home))



