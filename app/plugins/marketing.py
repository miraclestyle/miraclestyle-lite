# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import math
import datetime

from google.appengine.api import search

from app import ndb, settings, memcache, util
from app.srv import event
from app.plugins import blob
from app.lib.attribute_manipulator import set_attr, get_attr
from app.lib.list_manipulator import sort_by_list


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


def get_catalog_products(Template, Instance, catalog_key=None, catalog_images=None, complete=True, categories=False):
  
  @ndb.tasklet
  def complete_instance_async(entity):
    keys = [ndb.Key('73', str(entity.key.id()), parent=entity.key),
            ndb.Key('75', str(entity.key.id()), parent=entity.key)]
    results = yield ndb.get_multi_async(keys)
    images = results[0]
    contents = contents[1]
    if images:
      entity._images_entity = images
      entity._images = images.images
    if contents:
      entity._contents_entity = contents
      entity._contents = contents.contents
    raise ndb.Return(entity)
  
  @ndb.tasklet
  def complete_template_async(entity):
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
    keys = [ndb.Key('73', str(entity.key.id()), parent=entity.key),
            ndb.Key('74', str(entity.key.id()), parent=entity.key),
            ndb.Key('75', str(entity.key.id()), parent=entity.key)]
    results = yield ndb.get_multi_async(keys)
    images = results[0]
    variants = results[1]
    contents = contents[2]
    if instances:
      entity._instances = yield map(complete_instance_async, instances)
    if images:
      entity._images_entity = images
      entity._images = images.images
    if variants:
      entity._variants_entity = variants
      entity._variants = variants.variants
    if contents:
      entity._contents_entity = contents
      entity._contents = contents.contents
    raise ndb.Return(entity)
  
  @ndb.tasklet
  def categories_async(entity):
    category = yield entity.product_category.get_async()
    entity._product_category = category
    raise ndb.Return(entity)
  
  @ndb.tasklet
  def complete_template_mapper(entities):
    results = yield map(complete_template_async, entities)
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
  if categories:
    templates = categories_mapper(templates).get_result()
  if complete:
    templates = complete_template_mapper(templates).get_result()
  return templates


class DuplicateRead(event.Plugin):
  
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
    context.tmp['product_templates'] = templates
    context.tmp['new_product_templates'] = templates


class DuplicateCatalog(event.Plugin):
  
  def run(self, context):
    # this should be one  transaction
    # with PluginGroup concept this can be done trough plugins other then creating separate transaction functions inside a plugin
    catalog = context.entities['35']
    new_catalog = copy.deepcopy(catalog)
    new_catalog.created = datetime.datetime.now()
    new_catalog.updated = datetime.datetime.now()
    new_catalog.state = 'unpublished'
    new_catalog.set_key(None, namespace=catalog.key.namespace())
    context.tmp['new_catalog'] = new_catalog
    # copy the catalog cover
    blob.CopyImage(set_image='tmp.new_catalog.cover', blob_transform='entities.35.cover').run(context) # direct copy of cover
    new_catalog.put()
    context.log_entities.append((new_catalog, )) # LOG NEW CATALOG
    # copy the catalog images
    blob.duplicate_images_async(context, new_catalog._images, 'tmp.new_catalog._images', 'entities.35._images')
    for i,image in enumerate(new_catalog._images):
      image.set_key(str(i), parent=new_catalog.key)
      context.log_entities.append((image, ))# LOG CATALOG IMAGE
    ndb.put_multi(new_catalog._images)
    # copy product templates
    @ndb.tasklet
    def async_product_template(product, i):
      field = 'tmp.new_product_templates.%s._images' % i
      field_source = 'tmp.product_templates.%s._images' % i
      @ndb.tasklet
      def generate(): # For future.wait_all to work the tasklets that build the futures must yield another tasklet which is actaully a future with .get_result()
        blob.duplicate_images_async(context, get_attr(context, field), field, field_source)
        product.set_key(None, parent=new_catalog.key)
        context.log_entities.append((product, ))# LOG PRODUCT TEMPLATE
        raise ndb.Return(True)
      yield generate()
      raise ndb.Return(True)
 
    def helper_product_template(products):
      futures = []
      for i,product in enumerate(products):
        futures.append(async_product_template(product, i))
      return ndb.Future.wait_all(futures)
    
    helper_product_template(context.tmp['new_product_templates'])
    ndb.put_multi(context.tmp['new_product_templates'])
 
    Images = context.models['73']
    Variants = context.models['74']
    Contents = context.models['75']
    
    puts = []
    for product_template in context.tmp['new_product_templates']:
      puts.append(Images(parent=product_template.key, images=product_template._images, id=product_template.key_id_str))
      puts.append(Variants(parent=product_template.key, variants=product_template._variants, id=product_template.key_id_str))
      puts.append(Contents(parent=product_template.key, contents=product_template._contents, id=product_template.key_id_str))
    ndb.put_multi(puts)
    
    
class DuplicateProductTemplateInstances(event.Plugin):
  
  def run(self, context):
    # copy product instances of every product template
    @ndb.tasklet
    def async_product_instance(product_template, instance, instance_i, product_template_i):
      field = 'tmp.new_product_templates.%s._instances.%s._images' % (product_template_i, instance_i)
      field_source = 'tmp.product_templates.%s._instances.%s._images' % (product_template_i, instance_i)
      @ndb.tasklet
      def generator():
        blob.duplicate_images_async(context, get_attr(context, field), field, field_source)
        instance.set_key(instance.key.id(), parent=product_template.key)
        context.log_entities.append((instance, )) # LOG INSTANCES
        raise ndb.Return(True)
      yield generator()
      raise ndb.Return(instance)
 
    def helper_product_instance(product_template, instances, product_template_i):
      futures = []
      for instance_i,instance in enumerate(instances):
        futures.append(async_product_instance(product_template, instance, instance_i, product_template_i))
      return ndb.Future.wait_all(futures)
 
    instances = []
    for product_template_i,product_template in enumerate(context.tmp['new_product_templates']):
      helper_product_instance(product_template, product_template._instances, product_template_i)
      instances.extend(product_template._instances)
    ndb.put_multi(instances)
    
    Images = context.models['73']
    Contents = context.models['75']
    
    puts = []
    for instance in instances:
      puts.append(Images(parent=instance.key, images=instance._images, id=instance.key_id_str))
      puts.append(Contents(parent=instance.key, contents=instance._contents, id=instance.key_id_str))
    ndb.put_multi(puts)



class Read(event.Plugin):
  
  read_from_start = ndb.SuperBooleanProperty('5', indexed=False, required=True, default=False)
  
  def run(self, context):
    start = context.input.get('images_cursor')
    if not start:
      start = 0
    end = start + settings.CATALOG_PAGE + 1  # Always ask for one extra image, so we can determine if there are more images to get in next round.
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
    context.tmp['images_cursor'] = start + settings.CATALOG_PAGE  # @todo Next images cursor. Not sure if this is needed or the client does the mageic?
    context.tmp['images_more'] = more


class UpdateSet(event.Plugin):
  
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


class UpdateWrite(event.Plugin):
  
  def run(self, context):
    if context.entities['35']._field_permissions['_images']['writable']:
      if len(context.tmp['delete_images']):
        ndb.delete_multi([image.key for image in context.tmp['delete_images']])
        context.log_entities.extend([(image, ) for image in context.tmp['delete_images']])
        context.blob_delete = [image.image for image in context.tmp['delete_images']]
    if len(context.entities['35']._images):
      ndb.put_multi(context.entities['35']._images)
      context.log_entities.extend([(image, ) for image in context.entities['35']._images])


class UploadImagesSet(event.Plugin):
  
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


class UploadImagesWrite(event.Plugin):
  
  def run(self, context):
    if len(context.entities['35']._images):
      ndb.put_multi(context.entities['35']._images)
      context.tmp['catalog_image_keys'] = []
      for image in context.entities['35']._images:
        if image:
          context.tmp['catalog_image_keys'].append(image.key.urlsafe())
          context.blob_write.append(image.image)
          context.log_entities.append((image, ))


class ProcessImages(event.Plugin):
  
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


class ProcessCoverSet(event.Plugin):
  
  def run(self, context):
    if len(context.entities['35']._images):
      if context.entities['35'].cover:
        if context.entities['35'].cover.gs_object_name[:-6] != context.entities['35']._images[0].gs_object_name:
          context.values['35'].cover = context.entities['35']._images[0]
      else:
        context.values['35'].cover = context.entities['35']._images[0]
    else:
      context.values['35'].cover = None


class ProcessCoverTransform(event.Plugin):
  
  def run(self, context):
    if context.tmp.get('original_cover') and context.tmp.get('new_cover'):
      if str(context.tmp['original_cover'].image) != str(context.tmp['new_cover'].image):
        context.blob_delete.append(context.tmp['original_cover'].image)
        context.blob_transform = context.tmp['new_cover']
    elif context.tmp.get('original_cover'):
      context.blob_delete.append(context.tmp['original_cover'].image)
    elif context.tmp.get('new_cover'):
      context.blob_transform = context.tmp['new_cover']


class Delete(event.Plugin):
  
  def run(self, context):
    
    def delete(*args):
      entities = []
      for argument in args:
        entities.extend(argument)
      ndb.delete_multi([entity.key for entity in entities])
      context.log_entities.extend([(entity, ) for entity in entities])
    
    catalog_images = get_catalog_images(context.models['36'], context.entities['35'].key)
    templates = get_catalog_products(context.models['38'], context.models['39'], catalog_key=context.entities['35'].key)
    template_images = []
    template_variants = []
    template_contents = []
    instances = []
    instance_images = []
    instance_contents = []
    blob_templates_images = []
    blob_instances_images = []
    for template in templates:
      template_images.append(template._images_entity)
      template_variants.append(template._variants_entity)
      template_contents.append(template._contents_entity)
      blob_templates_images.extend(template._images)
      for instance in template._instances:
        instances.append(instance)
        instance_images.append(instance._images_entity)
        instance_contents.append(instance._contents_entity)
        blob_instances_images.extend(instance._images)
    context.blob_delete.extend([image.image for image in blob_instances_images])
    context.blob_delete.extend([image.image for image in blob_templates_images])
    context.blob_delete.extend([image.image for image in catalog_images])
    delete(instance_contents, instance_images, instances,
           template_contents, template_variants, template_images, templates, catalog_images)


class CronPublish(event.Plugin):
  
  page_size = ndb.SuperIntegerProperty('5', indexed=False, required=True, default=10)
  
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


class CronDiscontinue(event.Plugin):
  
  page_size = ndb.SuperIntegerProperty('5', indexed=False, required=True, default=10)
  
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


class CronDelete(event.Plugin):
  
  page_size = ndb.SuperIntegerProperty('5', indexed=False, required=True, default=10)
  catalog_life = ndb.SuperIntegerProperty('6', indexed=False, required=True, default=180)
  
  def run(self, context):
    Catalog = context.models['35']
    catalogs = Catalog.query(Catalog.state == 'discontinued',
                             Catalog.updated < (datetime.datetime.now() - datetime.timedelta(days=self.catalog_life)),
                             namespace=context.namespace).fetch(limit=self.page_size)
    for catalog in catalogs:
      data = {'action_id': 'delete',
              'action_model': '35',
              'key': catalog.key.urlsafe()}
      context.callback_payloads.append(('callback', data))


class SearchWrite(event.Plugin):
  
  index_name = ndb.SuperStringProperty('5', indexed=False)
  documents_per_index = ndb.SuperIntegerProperty('6', indexed=False)
  
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
    templates = get_catalog_products(context.models['38'], context.models['39'], catalog_images=catalog_images, complete=False, categories=True)
    write_index = True
    if not len(templates):
      # write_index = False  @todo We shall not allow indexing of catalogs without products attached!
      pass
    for template in templates:
      documents.append(index_product_template(template))
    for template in templates:
      if template._product_category.state != 'indexable':
        write_index = False
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


class SearchDelete(event.Plugin):
  
  index_name = ndb.SuperStringProperty('5', indexed=False)
  documents_per_index = ndb.SuperIntegerProperty('6', indexed=False)
  
  def run(self, context):
    documents = []
    documents.append(context.entities['35'].key_urlsafe)
    catalog_images = get_catalog_images(context.models['36'], context.entities['35'].key)
    templates = get_catalog_products(context.models['38'], catalog_images=catalog_images, complete=False)
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
