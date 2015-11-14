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

  def _static_dir(self, file_path, version=None):
    if version is not None:
      version = '?v=%s' % os.environ.get('CURRENT_VERSION_ID')
    else:
      version = ''
    static_dir = '%s/' % settings.HOST_URL
    if self.request.get('static_dir') is not None:
      static_dir = self.request.get('static_dir')
    return '%sclient/%s%s' % (static_dir, file_path, version)

  def respond(self):
    init = settings.DEBUG
    settings.DEBUG = False
    self.response.headers['Content-Type'] = 'text/plain; charset=utf8'
    self.render(self.base_template, {'static_dir': self._static_dir})
    settings.DEBUG = init


class BuildAngularDynamics(base.Angular):

  def after(self):
    pass

  def respond(self):
    if settings.DEBUG:
      self.response.headers['Content-Type'] = 'application/x-javascript; charset=utf-8'
      gets = settings.build(templates=True, js_and_css=False, statics=False, write=False)
      self.response.write(gets['templates.js'])

settings.ROUTES.append((r'/build/angular/index.html', BuildAngularIndexHTML))
settings.ROUTES.append((r'/build/dynamics.js', BuildAngularDynamics))
