# -*- coding: utf-8 -*-
'''
Created on May 28, 2015

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import urllib
from google.appengine.ext import ndb

from handler import base


class CatalogView(base.SeoOrAngular):

    def respond_seo(self, *args, **kwargs):
        data = {'action_id': 'read', 'action_model': '31', 'key': kwargs.get('key'), 'read_arguments': {
            '_images': {'config': {'limit': -1}}, '_seller': {}}}
        data = self.api_endpoint(payload=data)
        self.render('seo/catalog/view.html', {'catalog': data['entity']})


class CatalogProductView(base.SeoOrAngular):

    def respond_seo(self, *args, **kwargs):
        catalog_key = [list(ndb.Key(urlsafe=kwargs.get('key')).flat())]
        catalog_image_key = [[]]
        catalog_image_key[0].extend(catalog_key[0])
        catalog_image_key[0].extend(['30', int(kwargs.get('image_id'))])
        catalog_image_pricetag_key = [[]]
        catalog_image_pricetag_key[0].extend(catalog_key[0])
        catalog_image_pricetag_key[0].extend(['29', kwargs.get('pricetag_id')])
        data = {'action_id': 'read', 'action_model': '31', 'key': catalog_key,
                'read_arguments': {'_images': {'config': {'keys': [catalog_image_key]}, 'pricetags': {'_product': {'_category': {}}, 'config': {'keys': [catalog_image_pricetag_key]}}}, '_seller': {'_currency': {}}}}
        data = self.api_endpoint(payload=data)
        tpl = {'catalog': data['entity'],  'product': data['entity']['_images'][0]['pricetags'][0]['_product']}
        tpl.update(kwargs)
        self.render('seo/catalog/product/view.html', tpl)


class CatalogEmbed(base.SeoOrAngular):

    def respond_seo(self, *args, **kwargs):
        return CatalogView.respond_seo(self, *args, **kwargs)


class CatalogProductEmbed(base.SeoOrAngular):

    def respond_seo(self, *args, **kwargs):
        return CatalogProductView.respond_seo(self, *args, **kwargs)

settings.ROUTES.extend(((r'/catalog/<key>', CatalogView, 'catalog.view'),
                        (r'/catalog/<key>/product/<image_id>/<pricetag_id>',
                         CatalogProductView, 'catalog.product.view'),
                        (r'/embed/catalog/<key>',
                         CatalogEmbed, 'embed.catalog'),
                        (r'/embed/catalog/product/<key>', CatalogProductEmbed, 'embed.catalog.product')))
