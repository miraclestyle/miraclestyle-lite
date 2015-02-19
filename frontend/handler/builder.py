# -*- coding: utf-8 -*-
'''
Created on Oct 7, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import os
import codecs

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
    return '%sclient/static/%s' % (static_dir, file_path)
    
  
  def respond(self):
    self.response.headers['Content-Type'] = 'text/plain; charset=utf8'
    self.render(self.base_template, {'static_dir': self._static_dir})

class BuildAngularDist(base.Angular):

  def after(self):
    pass

  def respond(self):
    dist = os.path.join(settings.CLIENT_DIR, 'dist')
    paths = {}
    buff = {}
    for p in ['app.js', 'style.css', 'static', 'templates.js']:
      paths[p] = os.path.join(dist, p)
      buff[p] = u''
    for t, b in [('JAVASCRIPT', 'app.js'), ('CSS', 'style.css')]:
      for js in getattr(settings, 'ANGULAR_%s_PATHS' % t):
        with codecs.open(js, 'r', 'utf-8') as f:
          buff[b] += f.read()
    for b, w in buff.iteritems():
      with codecs.open(paths[b], 'w', 'utf-8') as f:
        f.write(w) # @todo minify
    

    
settings.ROUTES.append((r'/build/angular/dist', BuildAngularDist),
                       (r'/build/angular/index.html', BuildAngularIndexHTML))