# -*- coding: utf-8 -*-
'''
Created on May 28, 2015

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import urllib

from handler import base


class CatalogView(base.SeoOrAngular):

    def respond_seo(self, *args, **kwargs):
        data = self.api_endpoint(payload={'action_id': 'read', 'action_model': '31', 'key': kwargs.get(
            'key'), 'read_arguments': {'_images': {'config': {'limit': -1}}, '_seller': {}}})
        self.render('seo/catalog/view.html', {'catalog': data['entity']})


class CatalogProductView(base.SeoOrAngular):
    pass


class CatalogEmbed(base.SeoOrAngular):
    pass


class CatalogProductEmbed(base.SeoOrAngular):
    pass

settings.ROUTES.extend(((r'/catalog/<key>', CatalogView, 'catalog.view'),
                        (r'/catalog/product/<key>',
                         CatalogProductView, 'catalog.product.view'),
                        (r'/embed/catalog/<key>',
                         CatalogEmbed, 'embed.catalog'),
                        (r'/embed/catalog/product/<key>', CatalogProductEmbed, 'embed.catalog.product')))
