# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import math

from google.appengine.api import search

from app import ndb, settings, memcache, util
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


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


def get_product_templates(Template, catalog_key=None, catalog_images=None, complete=True):
  keys = []
  templates = []
  if catalog_images:
    for catalog_image in catalog_images:
      keys.extend([pricetag.product_template for pricetag in catalog_image.pricetags])
    keys = list(set(keys))
    templates = ndb.get_multi(keys)
  elif catalog_key:
    more = True
    offset = 0
    limit = 1000
    while more:
      entities = Template.query(ancestor=catalog_key).fetch(limit=limit, offset=offset)
      if len(entities):
        templates.extend(entities)
        keys.extend([entity.key for entity in entities])
        offset = offset + limit
      else:
        more = False
  images = None
  variants = None
  contents = None
  if complete:
    images = ndb.get_multi([ndb.Key('73', str(key.id()), parent=key) for key in keys])
    variants = ndb.get_multi([ndb.Key('74', str(key.id()), parent=key) for key in keys])
    contents = ndb.get_multi([ndb.Key('75', str(key.id()), parent=key) for key in keys])
  return {'templates': templates, 'images': images, 'variants': variants, 'contents': contents}


def get_product_instances(Instance, template_keys, complete=True):
  keys = []
  instances = []
  for template_key in template_keys:
    more = True
    offset = 0
    limit = 1000
    while more:
      entities = Instance.query(ancestor=template_key).fetch(limit=limit, offset=offset)
      if len(entities):
        instances.extend(entities)
        keys.extend([entity.key for entity in entities])
        offset = offset + limit
      else:
        more = False
  images = None
  contents = None
  if complete:
    images = ndb.get_multi([ndb.Key('73', str(key.id()), parent=key) for key in keys])
    contents = ndb.get_multi([ndb.Key('75', str(key.id()), parent=key) for key in keys])
  return {'instances': instances, 'images': images, 'contents': contents}


class Read(event.Plugin):
  
  read_from_start = ndb.SuperBooleanProperty('5', indexed=False, required=True, default=False)
  
  def run(self, context):
    start = context.input.get('images_cursor')
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
    context.values['35']._images = context.input.get('_images')
    new_images = []
    context.tmp['delete_images'] = []
    if context.values['35']._images:
      for i, image in enumerate(context.values['35']._images):
        image.set_key(str(i), parent=context.values['35'].key)
        new_images.append(image.key)
    if len(context.values['35']._images):
      context.values['35'].cover = context.values['35']._images[0]  # @todo Not sure if we need only image.image or entire entity here?
    for image in context.entities['35']._images:
      if image.key not in new_images:
        context.tmp['delete_images'].append(image)
    context.entities['35']._images = []


class UpdateWrite(event.Plugin):
  
  def run(self, context):
    if context.entities['35']._field_permissions['_images']['writable']:
      if len(context.tmp['delete_images']):
        ndb.delete_multi([image.key for image in context.tmp['delete_images']])
        context.blob_delete = [image.image for image in context.tmp['delete_images']]
    context.entities['35'].put()
    if len(context.entities['35']._images):
      ndb.put_multi(context.entities['35']._images)


class Delete(event.Plugin):
  
  def run(self, context):
    
    def delete(entities):
      ndb.delete_multi([entity.key for entity in entities])
      context.log_entities.extend([(entity, ) for entity in entities])
    
    catalog_images = get_catalog_images(context.models['36'], context.entities['35'].key)
    templates = get_product_templates(context.models['38'], catalog_key=context.entities['35'].key)
    instances = get_product_instances(context.models['39'], [template.key for template in templates])
    blob_templates_images = []
    for image in templates['images']:
      blob_templates_images.extend(image.images)
    blob_instances_images = []
    for image in instances['images']:
      blob_instances_images.extend(image.images)
    context.blob_delete.extend([image.image for image in blob_instances_images])
    context.blob_delete.extend([image.image for image in blob_templates_images])
    context.blob_delete.extend([image.image for image in catalog_images])
    delete(instances['contents'])
    delete(instances['images'])
    delete(instances['instances'])
    delete(templates['contents'])
    delete(templates['variants'])
    delete(templates['images'])
    delete(templates['templates'])
    delete(catalog_images)


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


class SearchWrite(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  index_name = ndb.SuperStringProperty('6', indexed=False)
  documents_per_index = ndb.SuperIntegerProperty('7', indexed=False)
  
  def run(self, context):
    if self.kind_id != None:
      kind_id = self.kind_id
    else:
      kind_id = context.model.get_kind()
    namespace = context.entities[kind_id].key_namespace
    if self.index_name != None:
      index_name = self.index_name
    elif namespace != None:
      index_name = namespace + '-' + kind_id
    else:
      index_name = kind_id
    documents = []
    fields = []
    fields.append(search.AtomField(name='key', value=context.entities[kind_id].key_urlsafe))
    fields.append(search.AtomField(name='kind', value=kind_id))
    fields.append(search.AtomField(name='id', value=context.entities[kind_id].key_id_str))
    fields.append(search.AtomField(name='namespace', value=context.entities[kind_id].key_namespace))
    fields.append(search.DateField(name='created', value=context.entities[kind_id].created))
    fields.append(search.DateField(name='updated', value=context.entities[kind_id].updated))
    fields.append(search.TextField(name='name', value=context.entities[kind_id].name))
    fields.append(search.DateField(name='publish_date', value=context.entities[kind_id].publish_date))
    fields.append(search.DateField(name='discontinue_date', value=context.entities[kind_id].discontinue_date))
    fields.append(search.AtomField(name='state', value=context.entities[kind_id].state))
    fields.append(search.AtomField(name='cover', value=context.entities[kind_id].cover.serving_url))
    fields.append(search.AtomField(name='seller_key', value=context.entities[kind_id].seller_key))
    fields.append(search.TextField(name='seller_name', value=context.entities[kind_id].namespace_entity.name))
    fields.append(search.AtomField(name='seller_logo', value=context.entities[kind_id].namespace_entity.logo.serving_url))
    #fields.append(search.NumberField(name='seller_feedback', value=context.entities[kind_id].namespace_entity.feedback))
    documents.append(search.Document(doc_id=context.entities[kind_id].key_urlsafe, fields=fields))
    def index_product_template(template):
      fields = []
      fields.append(search.AtomField(name='key', value=template.key_urlsafe))
      fields.append(search.AtomField(name='kind', value=template.get_kind()))
      fields.append(search.AtomField(name='id', value=template.key_id_str))
      fields.append(search.AtomField(name='namespace', value=template.key_namespace))
      fields.append(search.AtomField(name='product_category', value=template.product_category.urlsafe()))
      fields.append(search.TextField(name='name', value=template.name))
      fields.append(search.HtmlField(name='description', value=template.description))
      fields.append(search.AtomField(name='code', value=template.code))
      return search.Document(doc_id=template.key_urlsafe, fields=fields)
    catalog_images = get_catalog_images(context.models['36'], context.entities[kind_id].key)
    templates = get_product_templates(context.models['38'], catalog_images=catalog_images, complete=False)
    for template in templates['templates']:
      documents.append(index_product_template(template))
    if len(documents):
      documents_per_cycle = int(math.ceil(len(documents) / self.documents_per_index))
      for i in range(0, documents_per_cycle+1):
        documents_partition = documents[self.documents_per_index*i:self.documents_per_index*(i+1)]
        if documents_partition:
          try:
            index = search.Index(name=index_name)
            index.put(documents_partition)  # Batching puts is more efficient than adding documents one at a time.
          except:
            pass


class SearchDelete(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  index_name = ndb.SuperStringProperty('6', indexed=False)
  documents_per_index = ndb.SuperIntegerProperty('7', indexed=False)
  
  def run(self, context):
    if self.kind_id != None:
      kind_id = self.kind_id
    else:
      kind_id = context.model.get_kind()
    namespace = context.entities[kind_id].key_namespace
    if self.index_name != None:
      index_name = self.index_name
    elif namespace != None:
      index_name = namespace + '-' + kind_id
    else:
      index_name = kind_id
    documents = []
    documents.append(context.entities[kind_id].key_urlsafe)
    catalog_images = get_catalog_images(context.models['36'], context.entities[kind_id].key)
    templates = get_product_templates(context.models['38'], catalog_images=catalog_images, complete=False)
    for template in templates['templates']:
      documents.append(template.key_urlsafe)
    if len(documents):
      documents_per_cycle = int(math.ceil(len(documents) / self.documents_per_index))
      for i in range(0, documents_per_cycle+1):
        documents_partition = documents[self.documents_per_index*i:self.documents_per_index*(i+1)]
        if documents_partition:
          try:
            index = search.Index(name=index_name)
            index.delete(documents_partition)  # Batching deletes is more efficient than handling them one at a time.
          except:
            pass
