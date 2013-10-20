# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.core.tests import SelfReference

from webclient.route import register
from webclient.handler import Angular

class Tests(Angular):
    
      def respond(self):
          fa = SelfReference()
          fa.name = 'foo'
          fa.put()
          
          fa2 = SelfReference()
          fa2.name = 'foobar'
          fa2.ref = fa.key
          fa2.put()
          
          self.data['fa'] = fa
          self.data['fa2'] = fa2
      
      
      

register(('/tests', Tests))