# -*- coding: utf-8 -*-
'''
Created on May 28, 2015

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import urllib
import json
import base64

from google.appengine.ext import ndb

from handler import base


class CatalogView(base.SeoOrAngular):

  def respond_seo(self, *args, **kwargs):
    data = {'action_id': 'read', 'action_model': '31', 'key': kwargs.get('key'), 'read_arguments': {
        '_images': {'config': {'limit': -1}}, '_seller': {}}}
    data = self.api_endpoint(payload=data)
    catalog = data['entity']
    tpl = {'catalog': catalog,
           'title': 'Catalog %s' % catalog['name'],
           'updated': catalog['updated'],
           'image': '%s=s360' % catalog['_images'][0]['serving_url'],
           'path': self.uri_for('catalog.view', _full=True, key=catalog['key'])
           }
    self.render('seo/catalog/view.html', tpl)


class CatalogProductView(base.SeoOrAngular):

  def respond_seo(self, *args, **kwargs):
    catalog_key = [list(ndb.Key(urlsafe=kwargs.get('key')).flat())]
    catalog_image_key = [[]]
    catalog_image_key[0].extend(catalog_key[0])
    catalog_image_key[0].extend(['30', int(kwargs.get('image_id'))])
    catalog_image_pricetag_key = [[]]
    catalog_image_pricetag_key[0].extend(catalog_key[0])
    catalog_image_pricetag_key[0].extend(['29', kwargs.get('pricetag_id')])

    data = {
        'action_id': 'read',
        'action_model': '31',
        'key': catalog_key,
        'read_arguments': {
            '_images': {
                'config': {
                    'keys': [catalog_image_key]
                },
                'pricetags': {
                    '_product': {
                        '_category': {}
                    },
                    'config': {
                        'keys': [catalog_image_pricetag_key]
                    }
                }
            },
            '_seller': {
                '_currency': {}
            }
        }
    }

    variant = kwargs.get('variant')
    raw_variant = variant
    as_variant = False
    if variant:
      variant = json.loads(base64.b64decode(variant.replace('-', '=')))
      if variant:
        as_variant = True
        variant_shell = []
        for v in variant:
          k, kv = v.iteritems().next()
          variant_shell.append('%s: %s' % (k, kv))
        data = {
            "action_model": "31",
            "action_id": "read",
            "key": catalog_key,
            "read_arguments": {
                '_seller': {
                    '_currency': {}
                },
                "_images": {
                    "config": {
                        "keys": [catalog_image_key]
                    },
                    "pricetags": {
                        "config": {
                            "keys": [catalog_image_pricetag_key]
                        },
                        "_product": {
                            "_category": {},
                            "_instances": {
                                "config": {
                                    "search": {
                                        "filters": [{
                                            "field": "variant_options",
                                            "operator": "ALL_IN",
                                            "value": variant_shell
                                        }]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    data = self.api_endpoint(payload=data)
    catalog = data['entity']
    product = catalog['_images'][0]['pricetags'][0]['_product']
    if as_variant and product['_instances']:
      for k, v in product['_instances'][0].items():
        if k in product and v:
          product[k] = v
    kwds = dict(pricetag_id=kwargs.get('pricetag_id'),
                _full=True,
                variant=raw_variant,
                image_id=kwargs.get('image_id'),
                key=catalog['key'])
    if not raw_variant:
      kwds.pop('variant')
    tpl = {'catalog': catalog,
           'product': product,
           'title': 'Product %s' % product['name'],
           'description': "\n".join([product['_category']['name'], product['description']]),
           'code': product['code'],
           'updated': product['updated'],
           'raw_variant' : raw_variant,
           'price': product['unit_price'],
           'category': product['_category']['name'],
           'currency': catalog['_seller']['_currency'],
           'path': self.uri_for('catalog.product.variant.view' if raw_variant else 'catalog.product.view', **kwds),
           'image': False}
    if len(product['images']):
      tpl['image'] = '%s=s600' % product['images'][0]['serving_url']
    tpl.update(kwargs)
    self.render('seo/catalog/product/view.html', tpl)


class CatalogEmbed(base.SeoOrAngular):

  def respond_seo(self, *args, **kwargs):
    return CatalogView.respond_seo(self, *args, **kwargs)


class CatalogProductEmbed(base.SeoOrAngular):

  def respond_seo(self, *args, **kwargs):
    return CatalogProductView.respond_seo(self, *args, **kwargs)

settings.ROUTES.extend(((r'/catalog/<key>', CatalogView, 'catalog.view'),
                        (r'/catalog/<key>/order/view', CatalogView, 'catalog.order'),
                        (r'/catalog/<key>/product/<image_id>/<pricetag_id>', CatalogProductView, 'catalog.product.view'),
                        (r'/catalog/<key>/product/<image_id>/<pricetag_id>/<variant>', CatalogProductView, 'catalog.product.variant.view'),
                        (r'/catalog/<key>/product-add-to-cart/<image_id>/<pricetag_id>/<variant>/<quantity>', CatalogProductView, 'catalog.product.add_to_cart'),
                        (r'/embed/catalog/<key>', CatalogView, 'embed.catalog'),
                        (r'/embed/catalog/<key>/order/view', CatalogView, 'embed.catalog.order'),
                        (r'/embed/catalog/<key>/product/<image_id>/<pricetag_id>', CatalogProductView, 'embed.catalog.product'),
                        (r'/embed/catalog/<key>/product/<image_id>/<pricetag_id>/<variant>', CatalogProductView, 'embed.catalog.product.variant'),
                        (r'/embed/catalog/<key>/product-add-to-cart/<image_id>/<pricetag_id>/<variant>/<quantity>', CatalogProductView, 'catalog.product.add_to_cart')))
