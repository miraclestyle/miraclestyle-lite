# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import datetime
import copy

from google.appengine.api import search

from backend import orm
from backend.tools.base import *
from backend.util import *


class CatalogProductCategoryUpdateWrite(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    # This code builds leaf categories for selection with complete names, 3.8k of them.
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    update_file_path = self.cfg.get('file', None)
    production_environment = self.cfg.get('prod_env', False)
    if not update_file_path:
      raise orm.TerminateAction()
    Category = context.models['24']
    data = []
    with file(update_file_path) as f:
      for line in f:
        if not line.startswith('#'):
          data.append(line.replace('\n', ''))
    write_data = []
    sep = ' > '
    parent = None
    dig = 0
    for i, item in enumerate(data):
      if i == 100 and not production_environment:
        break
      new_cat = {}
      current = item.split(sep)
      try:
        next = data[i+1].split(sep)
      except IndexError as e:
        next = current
      if len(next) == len(current):
        current_total = len(current)-1
        last = current[current_total]
        parent = current[current_total-1]
        new_cat['id'] = hashlib.md5(last).hexdigest()
        new_cat['parent_record'] = Category.build_key(hashlib.md5(parent).hexdigest())
        new_cat['name'] = last
        new_cat['complete_name'] = ' / '.join(current[:current_total+1])
        new_cat['state'] = 'indexable'
        new_cat = Category(**new_cat)
        new_cat._use_rule_engine = False
        new_cat._use_record_engine = False
        write_data.append(new_cat)
    orm.put_multi(write_data)


class CatalogProcessCoverSet(orm.BaseModel):
  
  def run(self, context):
    # @todo before setting new cover we have to delete previous cover
    catalog_images = sorted(context._catalog._images.value, key=lambda x: x.sequence)
    catalog_cover = context._catalog.cover.value
    if catalog_images and len(catalog_images):
      if catalog_cover:
        if catalog_cover.gs_object_name[:-6] != catalog_images[0].gs_object_name:
          context._catalog.cover = copy.deepcopy(catalog_images[0])
          context._catalog.cover.value.sequence = 0
          context._catalog.cover.process()
      else:
        context._catalog.cover = copy.deepcopy(catalog_images[0])
        context._catalog.cover.value.sequence = 0
        context._catalog.cover.process()
    elif catalog_cover:
      context._catalog.cover._state = 'deleted'


# @todo Wee need all published catalogs here, no matter how many of them!
class CatalogDiscontinue(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    limit = self.cfg.get('page', 10)
    Catalog = context.models['31']
    account_key = context.input.get('account')
    account = account_key.get()
    if account is not None:
      catalogs = Catalog.query(Catalog.state == 'published', ancestor=account.key).fetch(limit=limit)
    for catalog in catalogs:
      data = {'action_id': 'discontinue',
              'action_model': '31',
              'message': 'Expired',
              'key': catalog.key.urlsafe()}
      context._callbacks.append(('callback', data))


class CatalogCronDiscontinue(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    limit = self.cfg.get('page', 10)
    Catalog = context.models['31']
    catalogs = Catalog.query(Catalog.state == 'published',
                             Catalog.discontinue_date <= datetime.datetime.now()).fetch(limit=limit)
    for catalog in catalogs:
      data = {'action_id': 'discontinue',
              'action_model': '31',
              'message': 'Expired',
              'key': catalog.key.urlsafe()}
      context._callbacks.append(('callback', data))


class CatalogCronDelete(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    limit = self.cfg.get('page', 10)
    catalog_unpublished_life = self.cfg.get('unpublished_life', 7)
    catalog_discontinued_life = self.cfg.get('discontinued_life', 180)
    Catalog = context.models['31']
    catalogs = []
    unpublished_catalogs = Catalog.query(Catalog.state == 'draft',
                                         Catalog.created < (datetime.datetime.now() - datetime.timedelta(days=catalog_unpublished_life))).fetch(limit=limit)
    discontinued_catalogs = Catalog.query(Catalog.state == 'discontinued',
                                          Catalog.updated < (datetime.datetime.now() - datetime.timedelta(days=catalog_discontinued_life))).fetch(limit=limit)
    catalogs.extend(unpublished_catalogs)
    catalogs.extend(discontinued_catalogs)
    for catalog in catalogs:
      data = {'action_id': 'delete',
              'action_model': '31',
              'key': catalog.key.urlsafe()}
      context._callbacks.append(('callback', data))


class CatalogSearchDocumentWrite(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    documents = []
    index_name = self.cfg.get('index', None)
    catalog_fields = {'root_entity.name': orm.SuperStringProperty(search_document_field_name='seller_name'),
                      'root_entity.logo.value.serving_url': orm.SuperStringProperty(search_document_field_name='seller_logo'),
                      'cover.value.serving_url': orm.SuperStringProperty(search_document_field_name='cover')}  # name='seller_feedback', value=context._catalog.namespace_entity.feedback
    product_fields = {'parent_entity.name': orm.SuperStringProperty(search_document_field_name='catalog_name'),
                      'root_entity.name': orm.SuperStringProperty(search_document_field_name='seller_name'),
                      'root_entity.logo.value.serving_url': orm.SuperStringProperty(search_document_field_name='seller_logo'),
                      '_product_category.value.parent_record': orm.SuperKeyProperty(kind='24', search_document_field_name='product_category_parent_record'),
                      '_product_category.value.name': orm.SuperStringProperty(search_document_field_name='product_category_name'),
                      '_product_category.value.complete_name': orm.SuperTextProperty(search_document_field_name='product_category_complete_name')}
    context._catalog._images.read({'config': {'cursor': -1}})
    product_keys = []
    for image in context._catalog._images.value:
      product_keys.extend([pricetag.product._urlsafe for pricetag in image.pricetags.value])
    context._catalog._products.read({'_product_category': {}, 'config': {'keys': product_keys}})
    products = context._catalog._products.value
    context._catalog._images = []
    write_index = True
    if not len(products):
      # write_index = False  @todo We shall not allow indexing of catalogs without products attached!
      pass
    for product in products:
      if product._product_category.value.state != 'indexable':
        write_index = False
        break
    results = None
    if write_index:
      documents.extend([context._catalog.get_search_document(catalog_fields)])
      documents.extend([product.get_search_document(product_fields) for product in products])
      context._catalog._write_custom_indexes = {}
      context._catalog._write_custom_indexes[index_name] = documents
    context._catalog._products = []


class CatalogSearchDocumentDelete(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entities = []
    index_name = self.cfg.get('index', None)
    entities.append(context._catalog.key)
    context._catalog._images.read({'config': {'cursor': -1}})
    product_keys = []
    for image in context._catalog._images.value:
      product_keys.extend([pricetag.product._urlsafe for pricetag in image.pricetags.value])
    context._catalog._products.read({'config': {'keys': product_keys}})
    products = context._catalog._products.value
    context._catalog._images = []
    entities.extend([product.key for product in products])
    context._catalog._delete_custom_indexes = {}
    context._catalog._delete_custom_indexes[index_name] = entities
    context._catalog._products = []


class CatalogSearch(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    index_name = self.cfg.get('index', None)
    static_arguments = self.cfg.get('s', {})
    dynamic_arguments = self.cfg.get('d', {})
    search_arguments = context.input.get('search')
    overide_arguments = {}
    overide_arguments.update(static_arguments)
    for key, value in dynamic_arguments.iteritems():
      overide_arguments[key] = get_attr(context, value)
    override_dict(search_arguments, overide_arguments)
    query = search_arguments['property'].build_search_query(search_arguments)
    index = search.Index(name=index_name)
    result = index.search(query)
    context._total_matches = result.number_found
    context._entities_count = len(result.results)
    context._entities = map(context.model.search_document_to_dict, result.results)
    more = False
    cursor = result.cursor
    if cursor is not None:
      cursor = cursor.web_safe_string
      more = True
    context._cursor = cursor
    context._more = more
