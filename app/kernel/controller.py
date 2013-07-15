# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.request import Handler
from app.template import render_template
from app.kernel.models import User
from webapp2_extras.i18n import _

from app.kernel.forms import LoginForm
 
class Home(Handler):
    
      def post(self):
          self.get()
 
      def get(self):
          
          users = User.all()
          
          session = self.session.get('user')
          
          loginform = LoginForm()
          
          if self.request.method == 'POST':
              loginform = LoginForm(self.request.POST)
              loginform.validate()
   
          self.response.write(render_template('kernel/test.html', {'users' : users, 'form' : loginform, 'title' : _('A cool way to die hard'), 'sess' : session}))