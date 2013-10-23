# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular
 

class Tests(Angular):
    
      def respond(self):
 
          self.data['session'] = dir(self.session)
          self.data['tester'] = str(self.session.container.name)
          self.data['sid'] = str(self.session.container.sid)
       
register(('/tests', Tests))