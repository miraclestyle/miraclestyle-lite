# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import datetime
import copy
import collections

from google.appengine.api import search, datastore

import orm
import tools


class CatalogProductCategoryUpdateWrite(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    # This code builds leaf categories for selection with complete names, 3.8k of them.
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    update_file_path = self.cfg.get('file', None)
    debug_environment = self.cfg.get('debug_environment', False)
    if not update_file_path:
      raise orm.TerminateAction()
    Category = context.models['24']
    gets = datastore.Query('24', namespace=None, keys_only=True).Run()
    keys = list(gets)
    datastore.Delete(keys)
    categories = []
    put_entities = []
    structure = {}
    with file(update_file_path) as f:
      for line in f:
        if not line.startswith('#'):
          item = line.replace('\n', '')
          categories.append(item)
          full_path = item.split(' > ')
          current_structure = structure
          for xi, path in enumerate(full_path):
            if path not in current_structure:
              current_structure[path] = {}
            current_structure = current_structure[path]

    for i, item in enumerate(categories):
      full_path = item.split(' > ')
      path_map = structure
      current = full_path
      parent = current[:-1]
      category = {}
      category['id'] = hashlib.md5(''.join(current)).hexdigest()
      if parent:
        category['parent_record'] = Category.build_key(hashlib.md5(''.join(parent)).hexdigest())
      else:
        category['parent_record'] = None
      category['name'] = ' / '.join(current)
      category['state'] = ['indexable']
      leaf = False
      for path in full_path:
        if path in path_map:
          path_map = path_map[path]
        if not len(path_map):
          leaf = True
      if leaf:
        category['state'].append('visible')  # marks the category as leaf
      category = Category(**category)
      category._use_rule_engine = False
      category._use_record_engine = False
      category._use_memcache = False
      category._use_cache = False
      put_entities.append(category)
    tools.log.debug('Writing %s categories' % len(put_entities))
    orm.put_multi(put_entities)


class CatalogProcessCoverSet(orm.BaseModel):

  def run(self, context):
    uploading = context.action.key.id() == 'catalog_upload_images'
    catalog_image = None
    catalog_images = context._catalog._images.value
    if catalog_images is None:
      catalog_images = []
    catalog_images_active = filter(lambda x: x._state != 'deleted', catalog_images)
    total_catalog_images_active = len(catalog_images_active)
    total_catalog_images = len(catalog_images)
    catalog_cover = context._catalog.cover.value
    if uploading:
      if total_catalog_images_active:
        catalog_image = catalog_images_active[0] # when uploading always select first image and set it as cover
    elif total_catalog_images > 1: # this is update that sent images for reordering
      try:
        catalog_image = catalog_images_active[0] # when upading always get first image
      except IndexError as e: # means that catalog_images_active is empty and user deleted all images, so we have to remove cover as well
        catalog_image = None
    elif catalog_images and catalog_images[0]._state == 'deleted':
        catalog_image = None # in case the user has only 1 image and he requested that it gets deleted, catalog cover must be deleted too
    else:
      # if user is sending 1 image, which is usually when he edits catalog products, do nothing
      return
    if catalog_image:
      if not catalog_cover or catalog_cover.gs_object_name[:-6] != catalog_image.gs_object_name:
        context._catalog.cover = copy.deepcopy(catalog_image)
        context._catalog.cover.value.sequence = 0
        context._catalog.cover.process()
    elif catalog_cover:
      catalog_cover._state = 'deleted'


class CatalogDiscontinue(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    Catalog = context.models['31']
    account_key = context.input.get('account')
    account = account_key.get()
    if account is not None:
      catalogs = Catalog.query(Catalog.state.IN(['published', 'indexed']), ancestor=account.key).fetch(limit=4)
    for catalog in catalogs:
      data = {'action_id': 'sudo_discontinue',
              'action_model': '31',
              'key': catalog.key.urlsafe()}
      context._callbacks.append(('callback', data))
    if catalogs:
      data = {'action_id': 'account_discontinue',
              'action_model': '31',
              'key': account_key.urlsafe()}
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
                                          Catalog.discontinued_date < (datetime.datetime.now() - datetime.timedelta(days=catalog_discontinued_life))).fetch(limit=limit)
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
    context._catalog.parent_entity.read()  # read seller in-memory
    catalog_fields = {'parent_entity.name': orm.SuperStringProperty(search_document_field_name='seller_name'),
                      'parent_entity.key._root': orm.SuperKeyProperty(kind='23', search_document_field_name='seller_account_key'),
                      'parent_entity.logo.value.serving_url': orm.SuperStringProperty(search_document_field_name='seller_logo'),
                      'cover.value.serving_url': orm.SuperStringProperty(search_document_field_name='cover'),
                      'cover.value.proportion': orm.SuperStringProperty(search_document_field_name='cover_proportion')}
    product_fields = {'key_parent._parent.entity.name': orm.SuperStringProperty(search_document_field_name='catalog_name'),
                      'key_parent._parent._parent.entity.name': orm.SuperStringProperty(search_document_field_name='seller_name'),
                      'key_parent._parent._parent.entity.logo.value.serving_url': orm.SuperStringProperty(search_document_field_name='seller_logo')}
    products = []
    for image in context._catalog._images.value:
      products.extend(image.products.value)
    context._catalog._images = []  # dismember images from put queue to avoid too many rpcs
    write_index = True
    if not len(products):
      write_index = False  # catalogs with no products are not allowed to be indexed
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
    product_keys = []
    for image in context._catalog._images.value:
      product_keys.extend([product.key_urlsafe for product in image.products.value])
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


class CatalogProcessProducts(orm.BaseModel):

  def run(self, context):
    products = {}
    catalog_images = context._catalog._images.value
    if catalog_images:
      for catalog_image in catalog_images:
        if catalog_image.products.value:
          for product in catalog_image.products.value:
            product_key = product.key
            if product_key not in products:
              products[product_key] = []
            products[product_key].append(product)
      for product_key, _products in products.iteritems():
        if len(_products) > 1:
          for product in _products:
            if product._state == 'deleted':
              product._state = 'removed'


class CatalogProductSetDuplicatedPosition(orm.BaseModel):

  def run(self, context):
    products = context._catalog._images.value[0].products.value
    if products:
      for product in products:
        if product._state == 'duplicated':
          product.position_left = (product.image_width / 2) - 5 # this math cant be improved because we do not know product width, we only know it's height
          product.position_top = (product.image_height / 2) - 5 # but we assume anyways that it's gonna have minimum width of 64 and height 36