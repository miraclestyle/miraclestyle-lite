# -*- coding: utf-8 -*-
'''
Created on May 28, 2015

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import urllib
from google.appengine.ext import ndb

from handler import base


class SellerView(base.SeoOrAngular):

  def respond_seo(self, *args, **kwargs):
    data = {'action_id': 'read', 'action_model': '23', 'account': kwargs.get('key'), 'read_arguments': {}}
    data = self.api_endpoint(payload=data)
    seller = data['entity']
    catalogs = {"action_model": "31",
                "action_id": "search",
                "search": {"ancestor": seller['key'],
                "filters": [{"field": "state", "operator": "IN", "value": ["published", "indexed"]}],
                "orders": [{"field": "published_date", "operator": "desc"}, {"field": "key", "operator": "desc"}],
                "options": {"start_cursor": None}}}
    catalogs = self.api_endpoint(payload=catalogs)
    tpl = {'seller': seller,
           'title': 'Seller %s' % seller['name'],
           'image': '%s=s360' % seller['logo']['serving_url'],
           'path': self.uri_for('seller.view', _full=True, key=seller['key']),
           'catalogs': catalogs['entities'],
           'updated': seller['updated']
           }
    self.render('seo/seller/view.html', tpl)


settings.ROUTES.extend(((r'/seller/<key>', SellerView, 'seller.view'),
                        (r'/embed/seller/<key>', SellerView, 'seller.embed.view'),))
