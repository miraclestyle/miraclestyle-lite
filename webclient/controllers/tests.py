# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.domain import acl

from webclient.route import register
from webclient.handler import Angular

import sys

class Tests(Angular):
    
      def respond(self):
          
          logs = list(sys.modules)
          
          self.data['model'] = logs
                
      
      

register(('/tests', Tests))