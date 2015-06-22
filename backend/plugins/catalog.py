# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import hashlib
import datetime
import copy
import collections

from google.appengine.api import search

import orm
import tools


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
    structure = collections.OrderedDict()
    for i, item in enumerate(data):
      if i == 100: # all instances now only import 100 items
        break
      full_path = item.split(sep)
      current_structure = structure
      for path in full_path:
        if path not in current_structure:
          current_structure[path] = collections.OrderedDict([('path', full_path)])
        current_structure = current_structure[path]

    def parse_structure(structure):
      current_structure = structure
      next_args = []
      while True:
        if not current_structure:
          try:
            current_structure = next_args.pop()
            continue
          except IndexError as e:
            break
        for key, value in current_structure:
          if not hasattr(value, 'iteritems'):
            continue
          current = value.get('path')
          current_total = len(current)-1
          parent = current[:-1]
          new_cat = {}
          new_cat['id'] = hashlib.md5(''.join(current)).hexdigest()
          if parent:
            new_cat['parent_record'] = Category.build_key(hashlib.md5(''.join(parent)).hexdigest())
          new_cat['name'] = ' / '.join(current)
          new_cat['state'] = ['indexable']
          if len(value) < 2:
            new_cat['state'].append('visible') # leafs
          new_cat = Category(**new_cat)
          new_cat._use_rule_engine = False
          new_cat._use_record_engine = False
          write_data.append(new_cat)
          if len(value) > 1:
            # roots
            next_args.append(value.iteritems())
        current_structure = None
    parse_structure(structure.iteritems())
    tools.log.debug('Writing %s categories' % len(write_data))
    for ent in write_data:
      ent.write()


class CatalogProcessCoverSet(orm.BaseModel):
  
  def run(self, context):
    catalog_image = None
    catalog_images = context._catalog._images.value
    if catalog_images and len(catalog_images) < 2:
      CatalogImage = context.models['30']
      catalog_images = CatalogImage.query(ancestor=context._catalog.key).order(-CatalogImage.sequence).fetch(1)
      # use query only when user is not uploading new images
    catalog_cover = context._catalog.cover.value
    if catalog_images:
      for catalog_image in catalog_images:
        if catalog_image._state == 'deleted':
          catalog_image = None
        else:
          break
    if catalog_image:
      if catalog_cover:
        if catalog_cover.gs_object_name[:-6] != catalog_image.gs_object_name:
          context._catalog.cover = copy.deepcopy(catalog_image)
          context._catalog.cover.value.sequence = 0
          context._catalog.cover.process()
      else:
        context._catalog.cover = copy.deepcopy(catalog_image)
        context._catalog.cover.value.sequence = 0
        context._catalog.cover.process()
    elif catalog_cover:
      catalog_cover._state = 'deleted'


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
    context._catalog.parent_entity.read() # read seller in-memory
    catalog_fields = {'parent_entity.name': orm.SuperStringProperty(search_document_field_name='seller_name'),
                      'parent_entity.key._root': orm.SuperKeyProperty(kind='23', search_document_field_name='seller_account_key'),
                      'parent_entity.logo.value.serving_url': orm.SuperStringProperty(search_document_field_name='seller_logo'),
                      'cover.value.serving_url': orm.SuperStringProperty(search_document_field_name='cover'),
                      'cover.value.proportion': orm.SuperStringProperty(search_document_field_name='cover_proportion')}  # name='seller_feedback', value=context._catalog.namespace_entity.feedback
    product_fields = {'key_parent._parent.entity.name': orm.SuperStringProperty(search_document_field_name='catalog_name'),
                      'key_parent._parent._parent.entity.name': orm.SuperStringProperty(search_document_field_name='seller_name'),
                      'key_parent._parent._parent.entity.logo.value.serving_url': orm.SuperStringProperty(search_document_field_name='seller_logo'),
                      '_category.value.parent_record': orm.SuperKeyProperty(kind='24', search_document_field_name='category_parent_record'),
                      '_category.value.name': orm.SuperStringProperty(search_document_field_name='category_name'),
                      '_category.value.complete_name': orm.SuperTextProperty(search_document_field_name='category_complete_name')}
    context._catalog._images.read({'config': {'search': {'options': {'limit': 0}}}, 'pricetags': {'_product': {'_category': {}}}})
    products = []
    for image in context._catalog._images.value:
      products.extend([pricetag._product.value for pricetag in image.pricetags.value])
    context._catalog._images = [] # dismember images from put queue to avoid too many rpcs
    write_index = True
    if not len(products):
      write_index = False # catalogs with no products are not allowed to be indexed
    for product in products:
      if 'indexable' not in product._category.value.state:
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
    index_name = self.cfg.get('index', None)
    entities = []
    entities.append(context._catalog.key_urlsafe)
    context._catalog._images.read({'config': {'search': {'options': {'limit': 0}}}, 'pricetags': {'_product': {}}})
    product_keys = []
    for image in context._catalog._images.value:
      product_keys.extend([pricetag._product.value.key_urlsafe for pricetag in image.pricetags.value])
    context._catalog._images = []
    entities.extend(product_keys)
    context._catalog._delete_custom_indexes = {}
    context._catalog._delete_custom_indexes[index_name] = entities

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
      overide_arguments[key] = tools.get_attr(context, value)
    tools.override_dict(search_arguments, overide_arguments)
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

class CatalogProcessPricetags(orm.BaseModel):
 
  def run(self, context):
    pricetags = {}
    catalog_images = context._catalog._images.value
    if catalog_images:
      for catalog_image in catalog_images:
        if catalog_image.pricetags.value:
          for pricetag in catalog_image.pricetags.value:
            pricetag_key = pricetag.key.urlsafe()
            if pricetag_key not in pricetags:
              pricetags[pricetag_key] = []
            pricetags[pricetag_key].append(pricetag)
      for pricetag_key, pricetag_set in pricetags.iteritems():
        if len(pricetag_set) > 1:
          for pricetag in pricetag_set:
            if pricetag._state == 'deleted':
              pricetag._state = 'removed'

class CatalogPricetagSetDuplicatedPosition(orm.BaseModel):

  def run(self, context):
    pricetags = context._catalog._images.value[0].pricetags.value
    if pricetags:
      for pricetag in pricetags:
        if pricetag._state == 'duplicated':
          pricetag.position_left += 20
          pricetag.position_top += 20
