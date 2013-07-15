# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.core import RequestHandler
from app.template import render_template
from app.kernel.models import User
 
class Home(RequestHandler):
      def get(self):
          
          users = User.all()
          
          session = self.session.get('user')
  
          self.response.write(render_template('kernel/test.html', {'users' : users, 'sess' : session}))