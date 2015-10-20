# -*- coding: utf-8 -*-
'''
Created on May 28, 2015

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import urllib

import api
from handler import base


class HomeView(base.SeoOrAngular):

  def respond(self, *args, **kwargs):
    if self.request.get('toggle_seo'):
        if 'seo' in self.request.cookies:
            self.response.delete_cookie('seo')
        else:
            self.response.set_cookie('seo', '1', max_age=360)
    return super(HomeView, self).respond(*args, **kwargs)

  def respond_seo(self, *args, **kwargs):
    data = self.api_endpoint(payload={'action_id': 'public_search', 'action_model': '31'})
    tpl = {'catalogs': data['entities'], 'logo': '%s/client/dist/static/logo_240.png' % self.template['base_url']}
    self.render('seo/home/view.html', tpl)

settings.ROUTES.extend(((r'/', HomeView, 'home'),))
