# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime

from app import orm, util
from app.tools.base import *
from app.tools.manipulator import set_attr, get_attr, sort_by_list


# @todo We will figure out destiny of this plugin once we solve set operation issue!
class UpdateSet(orm.BaseModel):
  
  def run(self, context):
    context._catalog.name = context.input.get('name')
    context._catalog.discontinue_date = context.input.get('discontinue_date')
    context._catalog.publish_date = context.input.get('publish_date')
    pricetags = context.input.get('pricetags')
    sort_images = context.input.get('sort_images')
    entity_images, delete_images = sort_by_list(context._catalog._images, sort_images, 'image')
    context._delete_images = []
    for delete in delete_images:
      entity_images.remove(delete)
      context._delete_images.append(delete)
    context._catalog._images = entity_images
    if context._catalog._images:
      for i, image in enumerate(context._catalog._images):
        image.set_key(str(i), parent=context._catalog.key)
        image.pricetags = pricetags[i].pricetags
    context._catalog._images = []


class ProcessCoverSet(orm.BaseModel):
  
  def run(self, context):
    if len(context._catalog._images):
      if context._catalog.cover:
        if context._catalog.cover.gs_object_name[:-6] != context._catalog._images[0].gs_object_name:
          context._catalog.cover = context._catalog._images[0]
      else:
        context._catalog.cover = context._catalog._images[0]
    else:
      context._catalog.cover = None


class CronPublish(orm.BaseModel):
  
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


class CronDiscontinue(orm.BaseModel):
  
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


class CronDelete(orm.BaseModel):
  
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
class SearchWrite(orm.BaseModel):
  
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
      documents.extend(document_from_entity([context._catalog], catalog_fields))
      documents.extend(document_from_entity(templates, product_fields))
      results = document_write(documents, index_name=index_name, documents_per_index=max_doc)


# @todo To be rewriten once we finish search integration with orm.
class SearchDelete(orm.BaseModel):
  
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
