# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import datetime

from app import orm, settings  # @todo settings has to GET OUT OF HERE!!!
from app.tools.base import *
from app.util import *


class ProductCategoryUpdateWrite(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    # this code builds leaf categories for selection with complete names, 3.8k of them
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    update_file_path = self.cfg.get('file', None)
    if not update_file_path:
      raise orm.TerminateAction()
    Category = context.models['17']
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
      if i == 100 and not settings.DEVELOPMENT_SERVER:
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
    # this has to exist because it carries a lot of logic with it
    # so we cant bluntly use Set()
    # it also calls .process() after it copies over the image to be used for copy process
    catalog_images = context._catalog._images.value
    catalog_cover = context._catalog.cover.value
    if catalog_images and len(catalog_images):
      if catalog_cover:
        if catalog_cover.gs_object_name[:-6] != catalog_images[0].gs_object_name:
          context._catalog.cover = catalog_images[0]
          context._catalog.cover.process()
      else:
        context._catalog.cover = catalog_images[0]
        context._catalog.cover.process()
    elif catalog_cover:
      context._catalog.cover = None
      


class CatalogCronPublish(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    limit = self.cfg.get('page', 10)
    Catalog = context.models['35']
    catalogs = []
    if context.domain.state == 'active':
      catalogs = Catalog.query(Catalog.state == 'locked',
                               Catalog.publish_date <= datetime.datetime.now(),
                               namespace=context.namespace).fetch(limit=limit)
    for catalog in catalogs:
      if catalog._is_eligible:
        data = {'action_id': 'publish',
                'action_model': '35',
                'message': 'Published by Cron.',
                'key': catalog.key.urlsafe()}
        context._callbacks.append(('callback', data))


class CatalogCronDiscontinue(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    limit = self.cfg.get('page', 10)
    Catalog = context.models['35']
    if context.domain.state == 'active':
      catalogs = Catalog.query(Catalog.state == 'published',
                               Catalog.discontinue_date <= datetime.datetime.now(),
                               namespace=context.namespace).fetch(limit=limit)
    else:
      catalogs = Catalog.query(Catalog.state == 'published',
                               namespace=context.namespace).fetch(limit=limit)
    for catalog in catalogs:
      data = {'action_id': 'discontinue',
              'action_model': '35',
              'message': 'Expired',
              'key': catalog.key.urlsafe()}
      context._callbacks.append(('callback', data))


class CatalogCronDelete(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    limit = self.cfg.get('page', 10)
    catalog_unpublished_life = self.cfg.get('unpublished_life', 180)
    catalog_discontinued_life = self.cfg.get('discontinued_life', 7)
    Catalog = context.models['35']
    catalogs = []
    locked_catalogs = []
    if context.domain.state != 'active':
      locked_catalogs = Catalog.query(Catalog.state == 'locked',
                                      namespace=context.namespace).fetch(limit=limit)
    unpublished_catalogs = Catalog.query(Catalog.state == 'unpublished',
                                         Catalog.created < (datetime.datetime.now() - datetime.timedelta(days=catalog_unpublished_life)),
                                         namespace=context.namespace).fetch(limit=limit)
    discontinued_catalogs = Catalog.query(Catalog.state == 'discontinued',
                                          Catalog.updated < (datetime.datetime.now() - datetime.timedelta(days=catalog_discontinued_life)),
                                          namespace=context.namespace).fetch(limit=limit)
    catalogs.extend(locked_catalogs)
    catalogs.extend(unpublished_catalogs)
    catalogs.extend(discontinued_catalogs)
    for catalog in catalogs:
      data = {'action_id': 'delete',
              'action_model': '35',
              'key': catalog.key.urlsafe()}
      context._callbacks.append(('callback', data))


# @todo To be rewriten once we finish search integration with orm.
class CatalogSearchDocumentWrite(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    documents = []
    index_name = self.cfg.get('index', None)
    max_doc = self.cfg.get('max_doc', 200)
    catalog_fields = {'created': 'created', 'updated': 'updated', 'name': 'name',
                      'publish_date': 'publish_date', 'discontinue_date': 'discontinue_date',
                      'state': 'state', 'cover': 'cover.serving_url', 'cover_width': 'cover.width',
                      'cover_height': 'cover.height', 'seller_name': 'namespace_entity.name',
                      'seller_logo': 'namespace_entity.logo.serving_url',
                      'seller_logo_width': 'namespace_entity.logo.width',
                      'seller_logo_height': 'namespace_entity.logo.height'}  # name='seller_feedback', value=context._catalog.namespace_entity.feedback
    product_fields = {'catalog_name': 'parent_entity.name', 'seller_name': 'namespace_entity.name',
                      'seller_logo': 'namespace_entity.logo.serving_url',
                      'seller_logo_width': 'namespace_entity.logo.width',
                      'seller_logo_height': 'namespace_entity.logo.height',
                      'product_category': 'product_category._urlsafe',
                      'product_category_parent_record': '_product_category.parent_record._urlsafe',
                      'product_category_name': '_product_category.name',
                      'product_category_complete_name': '_product_category.complete_name',
                      'name': 'name', 'description': 'description', 'code': 'code'}
    catalog_images = get_catalog_images(context.models['36'], context._catalog.key)
    templates = get_catalog_products(context.models['38'], context.models['39'],
                                     catalog_images=catalog_images, include_instances=False, include_categories=True)
    write_index = True
    if not len(templates):
      # write_index = False  @todo We shall not allow indexing of catalogs without products attached!
      pass
    for template in templates:
      if template._product_category.state != 'indexable':
        write_index = False
        break
    results = None
    if write_index:
      documents.extend([context._catalog.get_search_document()])
      documents.extend([product.get_search_document() for product in context._catalog._products])
      results = document_write(documents, index_name=index_name, documents_per_index=max_doc)


# @todo To be rewriten once we finish search integration with orm.
class CatalogSearchDocumentDelete(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entities = []
    index_name = self.cfg.get('index', None)
    max_doc = self.cfg.get('max_doc', 200)
    entities.append(context._catalog)
    catalog_images = get_catalog_images(context.models['36'], context._catalog.key)
    templates = get_catalog_products(context.models['38'], context.models['39'],
                                     catalog_images=catalog_images, include_instances=False)
    entities.extend(templates)
    results = document_delete(entities, index_name=index_name, documents_per_index=max_doc)


class CatalogSearch(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    index_name = self.cfg.get('index', None)
    search_arguments = context.input.get('search')
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
