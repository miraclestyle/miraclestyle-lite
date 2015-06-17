# -*- coding: utf-8 -*-
'''
Created on May 28, 2015

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import urllib

from handler import base


class SellerView(base.SeoOrAngular):

  def respond_seo(self, *args, **kwargs):
    self.render_response('seller/view.html')

settings.ROUTES.extend(((r'/seller/<key>', SellerView, 'seller.view'),))
