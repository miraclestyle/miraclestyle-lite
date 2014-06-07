# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import math
import datetime

from google.appengine.api import search

from app import ndb, memcache, util
from app.srv import event
from app.plugins import blob
from app.lib.attribute_manipulator import set_attr, get_attr
from app.lib.list_manipulator import sort_by_list
from app.lib.blob_manipulator import alter_image


def get_catalog_images(CatalogImage, catalog_key):
  catalog_images = []
  more = True
  offset = 0
  limit = 1000
  while more:
    entities = CatalogImage.query(ancestor=catalog_key).fetch(limit=limit, offset=offset)
    if len(entities):
      catalog_images.extend(entities)
      offset = offset + limit
    else:
      more = False
  return catalog_images


def get_catalog_products(Template, Instance, catalog_key=None, catalog_images=None, include_instances=True, include_categories=False):
  
  @ndb.tasklet
  def instances_async(entity):
    instances = []
    more = True
    offset = 0
    limit = 1000
    while more:
      entities = yield Instance.query(ancestor=template_key).fetch_async(limit=limit, offset=offset)
      if len(entities):
        instances.extend(entities)
        offset = offset + limit
      else:
        more = False
    if instances:
      entity._instances = instances
    raise ndb.Return(entity)
  
  @ndb.tasklet
  def categories_async(entity):
    category = yield entity.product_category.get_async()
    entity._product_category = category
    raise ndb.Return(entity)
  
  @ndb.tasklet
  def instances_mapper(entities):
    results = yield map(instances_async, entities)
    raise ndb.Return(results)
  
  @ndb.tasklet
  def categories_mapper(entities):
    results = yield map(categories_async, entities)
    raise ndb.Return(results)
  
  templates = []
  if catalog_images:
    keys = []
    for catalog_image in catalog_images:
      keys.extend([pricetag.product_template for pricetag in catalog_image.pricetags])
    keys = list(set(keys))
    templates = ndb.get_multi(keys)
    if not templates:
      templates = []
  elif catalog_key:
    more = True
    offset = 0
    limit = 1000
    while more:
      entities = Template.query(ancestor=catalog_key).fetch(limit=limit, offset=offset)
      if len(entities):
        templates.extend(entities)
        offset = offset + limit
      else:
        more = False
  if include_instances:
    templates = instances_mapper(templates).get_result()
  if include_categories:
    templates = categories_mapper(templates).get_result()
  return templates


class DuplicateRead(ndb.BaseModel):
  
  def run(self, context):
    catalog = context.entities['35']
    catalog._images = []
    catalog_images = get_catalog_images(context.models['36'], context.entities['35'].key)
    catalog_images.sort(key=lambda x : int(x.key.id()))
    if catalog_images:
      catalog._images = catalog_images
    templates = get_catalog_products(context.models['38'], context.models['39'], catalog_images=catalog_images)
    if not templates:
      templates = []
    context.tmp['original_product_templates'] = templates
    context.tmp['copy_product_templates'] = templates  # @todo Is this supposed to be deep copy!?


# @todo Not sure if multiple cloudstorage operations can run  inside single transaction?!!
class DuplicateWrite(ndb.BaseModel):
  
  def run(self, context):
    def copy_images(source, destination):
      @ndb.tasklet
      def alter_image_async(source, destination):
        @ndb.tasklet
        def generate():
          original_image = get_attr(context, source)
          results = alter_image(original_image, copy=True, sufix='copy')
          if results.get('blob_delete'):
            context.blob_delete.append(results['blob_delete'])
          if results.get('new_image'):
            set_attr(context, destination, results['new_image'])
          raise ndb.Return(True)
        yield generate()
        raise ndb.Return(True)
      
      futures = []
      images = get_attr(context, source)
      for i, image in enumerate(images):
        source = '%s.%s' % (source, i)
        destination = '%s.%s' % (destination, i)
        future = alter_image_async(source, destination)
        futures.append(future)
      return ndb.Future.wait_all(futures)
    
    @ndb.tasklet
    def copy_template_async(template, source, destination):
      @ndb.tasklet
      def generate():
        copy_images(source, destination)
        template.set_key(None, parent=new_catalog.key)
        context.log_entities.append((template, ))
        raise ndb.Return(True)
      yield generate()
      raise ndb.Return(True)
    
    @ndb.tasklet
    def copy_istance_async(template, instance, source, destination):
      @ndb.tasklet
      def generate():
        copy_images(source, destination)
        instance.set_key(instance.key.id(), parent=template.key)
        context.log_entities.append((instance, ))
        raise ndb.Return(True)
      yield generate()
      raise ndb.Return(True)
    
    def copy_template_mapper(templates):
      futures = []
      for i, template in enumerate(templates):
        source = 'tmp.original_product_templates.%s.images' % i
        destination = 'tmp.copy_product_templates.%s.images' % i
        futures.append(copy_template_async(template, source, destination))
      return ndb.Future.wait_all(futures)
    
    def copy_instance_mapper(template, template_i):
      futures = []
      for instance_i, instance in enumerate(template._instances):
        source = 'tmp.original_product_templates.%s._instances.%s.images' % (template_i, instance_i)
        destination = 'tmp.copy_product_templates.%s._instances.%s.images' % (template_i, instance_i)
        futures.append(copy_istance_async(template, instance, source, destination))
      return ndb.Future.wait_all(futures)
    
    catalog = context.entities['35']
    new_catalog = copy.deepcopy(catalog)
    new_catalog.created = datetime.datetime.now()
    new_catalog.updated = datetime.datetime.now()  # @todo This field updates automatically, no need for setting the date!
    new_catalog.state = 'unpublished'
    new_catalog.set_key(None, namespace=catalog.key.namespace())
    cover_results = alter_image(context.entities['35'].cover, copy=True, sufix='cover')
    if cover_results.get('blob_delete'):
      context.blob_delete.append(cover_results['blob_delete'])
    if cover_results.get('new_image'):
      new_catalog.cover = cover_results['new_image']
    else:
      new_catalog.cover = None
    new_catalog.put()
    context.log_entities.append((new_catalog, ))
    context.tmp['new_catalog'] = new_catalog
    copy_images('entities.35._images', 'tmp.new_catalog._images')
    for i, image in enumerate(new_catalog._images):
      image.set_key(str(i), parent=new_catalog.key)
      context.log_entities.append((image, ))
    ndb.put_multi(new_catalog._images)
    copy_template_mapper(context.tmp['copy_product_templates'])
    ndb.put_multi(context.tmp['copy_product_templates'])
    instances = []
    for template_i, template in enumerate(context.tmp['copy_product_templates']):
      copy_instance_mapper(template, template_i)
      instances.extend(template._instances)
    ndb.put_multi(instances)


class Read(ndb.BaseModel):
  
  read_from_start = ndb.SuperBooleanProperty('1', indexed=False, required=True, default=False)
  catalog_page = ndb.SuperIntegerProperty('2', indexed=False, required=True, default=10)
  
  def run(self, context):
    start = context.input.get('images_cursor')
    if not start:
      start = 0
    end = start + self.catalog_page + 1  # Always ask for one extra image, so we can determine if there are more images to get in next round.
    if self.read_from_start:
      start = 0
    images = ndb.get_multi([ndb.Key('36', str(i), parent=context.entities['35'].key) for i in range(start, end)])
    count = len(images)
    more = True
    results = []
    for i, image in enumerate(images):
      if image != None:
        results.append(image)
      elif i == (count - 1):
        more = False  # If the last item is None, then we assume there are no more images in catalog to get in next round!
    if more:
      results.pop(len(results) - 1)  # We respect catalog page amount, so if there are more images, remove the last one.
    context.entities['35']._images = results
    context.values['35']._images = copy.deepcopy(context.entities['35']._images)
    context.tmp['images_cursor'] = start + self.catalog_page  # @todo Next images cursor. Not sure if this is needed or the client does the mageic?
    context.tmp['images_more'] = more


class UpdateSet(ndb.BaseModel):
  
  def run(self, context):
    context.values['35'].name = context.input.get('name')
    context.values['35'].discontinue_date = context.input.get('discontinue_date')
    context.values['35'].publish_date = context.input.get('publish_date')
    pricetags = context.input.get('pricetags')
    sort_images = context.input.get('sort_images')
    entity_images, delete_images = sort_by_list(context.entities['35']._images, sort_images, 'image')
    context.tmp['delete_images'] = []
    for delete in delete_images:
      entity_images.remove(delete)
      context.tmp['delete_images'].append(delete)
    context.values['35']._images = entity_images
    if context.values['35']._images:
      for i, image in enumerate(context.values['35']._images):
        image.set_key(str(i), parent=context.entities['35'].key)
        image.pricetags = pricetags[i].pricetags
    context.entities['35']._images = []


class UpdateWrite(ndb.BaseModel):
  
  def run(self, context):
    if context.entities['35']._field_permissions['_images']['writable']:
      if len(context.tmp['delete_images']):
        ndb.delete_multi([image.key for image in context.tmp['delete_images']])
        context.log_entities.extend([(image, ) for image in context.tmp['delete_images']])
        context.blob_delete = [image.image for image in context.tmp['delete_images']]
    if len(context.entities['35']._images):
      ndb.put_multi(context.entities['35']._images)
      context.log_entities.extend([(image, ) for image in context.entities['35']._images])


class UploadImagesSet(ndb.BaseModel):
  
  def run(self, context):
    CatalogImage = context.models['36']
    _images = context.input.get('_images')
    if not _images:  # If no images were saved, do nothing.
      raise event.TerminateAction()
    i = CatalogImage.query(ancestor=context.entities['35'].key).count()  # Get last sequence.
    for image in _images:
      image.set_key(str(i), parent=context.entities['35'].key)
      i += 1
    context.entities['35']._images = []
    context.values['35']._images = _images


class UploadImagesWrite(ndb.BaseModel):
  
  def run(self, context):
    if len(context.entities['35']._images):
      ndb.put_multi(context.entities['35']._images)
      context.tmp['catalog_image_keys'] = []
      for image in context.entities['35']._images:
        if image:
          context.tmp['catalog_image_keys'].append(image.key.urlsafe())
          context.blob_write.append(image.image)
          context.log_entities.append((image, ))


class ProcessImages(ndb.BaseModel):
  
  def run(self, context):
    if len(context.input.get('catalog_image_keys')):
      catalog_image_keys = []
      for catalog_image_key in context.input.get('catalog_image_keys'):
        if catalog_image_key.parent() == context.entities['35'].key:
          catalog_image_keys.append(catalog_image_key)
      if catalog_image_keys:
        catalog_images = ndb.get_multi(catalog_image_keys)
        # You are not permitted to remove elements from the list while iterating over it using a for loop.
        def mark_catalog_images(catalog_image):
          if catalog_image is None:
            return False
          context.blob_delete.append(catalog_image.image)
          return True
        catalog_images = filter(mark_catalog_images, catalog_images)
        if catalog_images:
          catalog_images = ndb.validate_images(catalog_images)
          ndb.put_multi(catalog_images)
          for catalog_image in catalog_images:
            context.log_entities.append((catalog_image, ))
            context.blob_write.append(catalog_image.image)  # Do not delete those blobs that survived!


class ProcessCoverSet(ndb.BaseModel):
  
  def run(self, context):
    if len(context.entities['35']._images):
      if context.entities['35'].cover:
        if context.entities['35'].cover.gs_object_name[:-6] != context.entities['35']._images[0].gs_object_name:
          context.values['35'].cover = context.entities['35']._images[0]
      else:
        context.values['35'].cover = context.entities['35']._images[0]
    else:
      context.values['35'].cover = None


class ProcessCoverTransform(ndb.BaseModel):
  
  def run(self, context):
    if context.tmp.get('original_cover') and context.tmp.get('new_cover'):
      if str(context.tmp['original_cover'].image) != str(context.tmp['new_cover'].image):
        context.blob_delete.append(context.tmp['original_cover'].image)
        context.blob_transform = context.tmp['new_cover']
    elif context.tmp.get('original_cover'):
      context.blob_delete.append(context.tmp['original_cover'].image)
    elif context.tmp.get('new_cover'):
      context.blob_transform = context.tmp['new_cover']


class Delete(ndb.BaseModel):
  
  def run(self, context):
    
    def delete(*args):
      entities = []
      for argument in args:
        entities.extend(argument)
      ndb.delete_multi([entity.key for entity in entities])
      context.log_entities.extend([(entity, ) for entity in entities])
    
    catalog_images = get_catalog_images(context.models['36'], context.entities['35'].key)
    templates = get_catalog_products(context.models['38'], context.models['39'], catalog_key=context.entities['35'].key)
    instances = []
    context.blob_delete.extend([image.image for image in catalog_images])
    for template in templates:
      context.blob_delete.extend([image.image for image in template.images])
      for instance in template._instances:
        instances.append(instance)
        context.blob_delete.extend([image.image for image in instance.images])
    delete(instances, templates, catalog_images)


class CronPublish(ndb.BaseModel):
  
  page_size = ndb.SuperIntegerProperty('1', indexed=False, required=True, default=10)
  
  def run(self, context):
    Catalog = context.models['35']
    catalogs = Catalog.query(Catalog.state == 'locked',
                             Catalog.publish_date <= datetime.datetime.now(),
                             namespace=context.namespace).fetch(limit=self.page_size)
    for catalog in catalogs:
      if catalog._is_eligible:
        data = {'action_id': 'publish',
                'action_model': '35',
                'message': 'Published by Cron.',
                'key': catalog.key.urlsafe()}
        context.callback_payloads.append(('callback', data))


class CronDiscontinue(ndb.BaseModel):
  
  page_size = ndb.SuperIntegerProperty('1', indexed=False, required=True, default=10)
  
  def run(self, context):
    Catalog = context.models['35']
    catalogs = Catalog.query(Catalog.state == 'published',
                             Catalog.discontinue_date <= datetime.datetime.now(),
                             namespace=context.namespace).fetch(limit=self.page_size)
    for catalog in catalogs:
      data = {'action_id': 'discontinue',
              'action_model': '35',
              'message': 'Expired',
              'key': catalog.key.urlsafe()}
      context.callback_payloads.append(('callback', data))


class CronDelete(ndb.BaseModel):
  
  page_size = ndb.SuperIntegerProperty('1', indexed=False, required=True, default=10)
  catalog_unpublished_life = ndb.SuperIntegerProperty('2', indexed=False, required=True, default=180)
  catalog_discontinued_life = ndb.SuperIntegerProperty('3', indexed=False, required=True, default=7)
  
  def run(self, context):
    Catalog = context.models['35']
    catalogs = []
    unpublished_catalogs = Catalog.query(Catalog.state == 'unpublished',
                                         Catalog.created < (datetime.datetime.now() - datetime.timedelta(days=self.catalog_unpublished_life)),
                                         namespace=context.namespace).fetch(limit=self.page_size)
    discontinued_catalogs = Catalog.query(Catalog.state == 'discontinued',
                                          Catalog.updated < (datetime.datetime.now() - datetime.timedelta(days=self.catalog_discontinued_life)),
                                          namespace=context.namespace).fetch(limit=self.page_size)
    catalogs.extend(unpublished_catalogs)
    catalogs.extend(discontinued_catalogs)
    for catalog in catalogs:
      data = {'action_id': 'delete',
              'action_model': '35',
              'key': catalog.key.urlsafe()}
      context.callback_payloads.append(('callback', data))


class SearchWrite(ndb.BaseModel):
  
  index_name = ndb.SuperStringProperty('1', indexed=False)
  documents_per_index = ndb.SuperIntegerProperty('2', indexed=False)
  
  def run(self, context):
    documents = []
    fields = []
    fields.append(search.AtomField(name='key', value=context.entities['35'].key_urlsafe))
    fields.append(search.AtomField(name='kind', value='35'))
    fields.append(search.AtomField(name='id', value=context.entities['35'].key_id_str))
    fields.append(search.AtomField(name='namespace', value=context.entities['35'].key_namespace))
    fields.append(search.DateField(name='created', value=context.entities['35'].created))
    fields.append(search.DateField(name='updated', value=context.entities['35'].updated))
    fields.append(search.TextField(name='name', value=context.entities['35'].name))
    fields.append(search.DateField(name='publish_date', value=context.entities['35'].publish_date))
    fields.append(search.DateField(name='discontinue_date', value=context.entities['35'].discontinue_date))
    fields.append(search.AtomField(name='state', value=context.entities['35'].state))
    fields.append(search.AtomField(name='cover', value=context.entities['35'].cover.serving_url))
    fields.append(search.AtomField(name='cover_width', value=str(context.entities['35'].cover.width)))
    fields.append(search.AtomField(name='cover_height', value=str(context.entities['35'].cover.height)))
    fields.append(search.TextField(name='seller_name', value=context.entities['35'].namespace_entity.name))
    fields.append(search.AtomField(name='seller_logo', value=context.entities['35'].namespace_entity.logo.serving_url))
    fields.append(search.AtomField(name='seller_logo_width', value=str(context.entities['35'].namespace_entity.logo.width)))
    fields.append(search.AtomField(name='seller_logo_height', value=str(context.entities['35'].namespace_entity.logo.height)))
    #fields.append(search.NumberField(name='seller_feedback', value=context.entities['35'].namespace_entity.feedback))
    documents.append(search.Document(doc_id=context.entities['35'].key_urlsafe, fields=fields))
    def index_product_template(template):
      fields = []
      fields.append(search.AtomField(name='key', value=template.key_urlsafe))
      fields.append(search.AtomField(name='kind', value='38'))
      fields.append(search.AtomField(name='id', value=template.key_id_str))
      fields.append(search.AtomField(name='namespace', value=template.key_namespace))
      fields.append(search.AtomField(name='ancestor', value=template.key_parent.urlsafe()))
      fields.append(search.TextField(name='catalog_name', value=template.parent_entity.name))
      fields.append(search.TextField(name='seller_name', value=template.namespace_entity.name))
      fields.append(search.AtomField(name='seller_logo', value=template.namespace_entity.logo.serving_url))
      fields.append(search.AtomField(name='seller_logo_width', value=str(template.namespace_entity.logo.width)))
      fields.append(search.AtomField(name='seller_logo_height', value=str(template.namespace_entity.logo.height)))
      fields.append(search.AtomField(name='product_category', value=template.product_category.urlsafe()))
      fields.append(search.AtomField(name='product_category_parent_record', value=template._product_category.parent_record.urlsafe()))
      fields.append(search.TextField(name='product_category_name', value=template._product_category.name))
      fields.append(search.TextField(name='product_category_complete_name', value=template._product_category.complete_name))
      fields.append(search.TextField(name='name', value=template.name))
      fields.append(search.HtmlField(name='description', value=template.description))
      fields.append(search.AtomField(name='code', value=template.code))
      return search.Document(doc_id=template.key_urlsafe, fields=fields)
    catalog_images = get_catalog_images(context.models['36'], context.entities['35'].key)
    templates = get_catalog_products(context.models['38'], context.models['39'],
                                     catalog_images=catalog_images, include_instances=False, include_categories=True)
    write_index = True
    if not len(templates):
      # write_index = False  @todo We shall not allow indexing of catalogs without products attached!
      pass
    for template in templates:
      documents.append(index_product_template(template))
      if template._product_category.state != 'indexable':
        write_index = False
        break
    indexing = False
    if write_index and len(documents):
      indexing = True
      documents_per_cycle = int(math.ceil(len(documents) / self.documents_per_index))
      for i in range(0, documents_per_cycle+1):
        documents_partition = documents[self.documents_per_index*i:self.documents_per_index*(i+1)]
        if documents_partition:
          try:
            index = search.Index(name=self.index_name)
            index.put(documents_partition)  # Batching puts is more efficient than adding documents one at a time.
          except:
            indexing = False
            pass
    if indexing:
      context.tmp['message'] = 'Indexing succeeded!'
    else:
      if len(documents):
        if write_index:
          context.tmp['message'] = 'Indexing failed!'
        else:
          context.tmp['message'] = 'Indexing not allowed!'
      else:
        context.tmp['message'] = 'No documents to index!'


class SearchDelete(ndb.BaseModel):
  
  index_name = ndb.SuperStringProperty('1', indexed=False)
  documents_per_index = ndb.SuperIntegerProperty('2', indexed=False)
  
  def run(self, context):
    documents = []
    documents.append(context.entities['35'].key_urlsafe)
    catalog_images = get_catalog_images(context.models['36'], context.entities['35'].key)
    templates = get_catalog_products(context.models['38'], context.models['39'],
                                     catalog_images=catalog_images, include_instances=False)
    for template in templates:
      documents.append(template.key_urlsafe)
    unindexing = False
    if len(documents):
      unindexing = True
      documents_per_cycle = int(math.ceil(len(documents) / self.documents_per_index))
      for i in range(0, documents_per_cycle+1):
        documents_partition = documents[self.documents_per_index*i:self.documents_per_index*(i+1)]
        if documents_partition:
          try:
            index = search.Index(name=self.index_name)
            index.delete(documents_partition)  # Batching deletes is more efficient than handling them one at a time.
          except:
            unindexing = False
            pass
    if unindexing:
      context.tmp['message'] = 'Unindexing succeeded!'
    else:
      if len(documents):
        context.tmp['message'] = 'Unindexing failed!'
      else:
        context.tmp['message'] = 'No documents to unindex!'
