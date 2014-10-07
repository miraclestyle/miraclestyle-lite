# -*- coding: utf-8 -*-
'''
Created on Oct 7, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import os

from handler import base

class BuildAngularIndexHTML(base.Angular):
  
  def after(self):
    pass
  
  def respond(self):
    self.response.headers['Content-Type'] = 'text/plain;charset=utf8'
    self.render(self.base_template)
    
settings.ROUTES.append((r'/build/angular/index.html', BuildAngularIndexHTML))