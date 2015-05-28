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

    def respond_seo(self, *args, **kwargs):
        data = self.api_endpoint(payload={'action_id': 'public_search', 'action_model': '31'})
        self.render('seo/home/view.html', {'catalogs': data['entities']})

class Sitemap(base.SeoOrAngular):

    def respond_seo(self, *args, **kwargs):
        self.render('seo/home/sitemap.html')

settings.ROUTES.extend(((r'/', HomeView, 'home'), (r'/sitemap', Sitemap, 'sitemap')))
