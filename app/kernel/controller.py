# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.request import Handler
from app.template import render_template
from app.kernel.models import User
 
class Home(Handler):
      def get(self):
          
          users = User.all()
          
          session = self.session.get('user')
  
          self.response.write(render_template('kernel/test.html', {'users' : users, 'sess' : session}))