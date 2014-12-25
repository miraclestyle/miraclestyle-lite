# -*- coding: utf-8 -*-
'''
Created on Oct 7, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import os

from handler import base

class BuildAngularIndexHTML(base.Angular):

  '''
    Handler used to compile index html file for external use
  '''
  
  def after(self):
    pass
  
  def _static_dir(self, file_path):
    static_dir = '%s/' % settings.HOST_URL
    if self.request.get('static_dir') != None:
      static_dir = self.request.get('static_dir')
    return '%sclient/static/%s' % (static_dir, file_path)
    
  
  def respond(self):
    self.response.headers['Content-Type'] = 'text/plain;charset=utf8'
    self.render(self.base_template, {'static_dir': self._static_dir})
    
settings.ROUTES.append((r'/build/angular/index.html', BuildAngularIndexHTML))