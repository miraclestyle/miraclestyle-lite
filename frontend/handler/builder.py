# -*- coding: utf-8 -*-
'''
Created on Oct 7, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import os
import subprocess

from handler import base

class BuildAngularIndexHTML(base.Angular):

  '''
    Handler used to compile index html file for external use
  '''
  
  def after(self):
    pass
  
  def _static_dir(self, file_path):
    static_dir = '%s/' % settings.HOST_URL
    if self.request.get('static_dir') is not None:
      static_dir = self.request.get('static_dir')
    return '%sclient/%s' % (static_dir, file_path)
    
  
  def respond(self):
    self.response.headers['Content-Type'] = 'text/plain; charset=utf8'
    self.render(self.base_template, {'static_dir': self._static_dir})

class BuildAngularTemplates(base.Angular):

  def after(self):
    pass

  def respond(self):
    if settings.DEBUG:
      self.response.headers['Content-Type'] = 'application/x-javascript; charset=utf-8'
      gets = settings.build(templates=True, js_and_css=False, statics=False, write=False)
      self.response.write(gets['templates.js'])

settings.ROUTES.append((r'/build/angular/index.html', BuildAngularIndexHTML))
settings.ROUTES.append((r'/build/templates.js', BuildAngularTemplates))