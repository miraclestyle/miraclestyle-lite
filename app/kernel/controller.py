# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.core import RequestHandler
from app.template import render_template

class Home(RequestHandler):
      def get(self):
          self.response.write(render_template('sys/test.html'))