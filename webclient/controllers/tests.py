# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular
 
class Tests(Angular):
    
      def respond(self):
          pass
       
register(('/tests', Tests))