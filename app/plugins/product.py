# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json
import copy
import hashlib

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings, memcache, util
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr
from app.lib.list_manipulator import sort_by_list


def build_key_from_signature(context):
  variant_signature = context.input.get('variant_signature')
  key_id = hashlib.md5(json.dumps(variant_signature)).hexdigest()
  product_instance_key = context.model.build_key(key_id, parent=context.input.get('parent'))
  return product_instance_key


def build_keyes(context):
  entity = context.entities[context.model.get_kind()]
  return [ndb.Key('73', entity.key_id_str, parent=entity.key),
          ndb.Key('74', entity.key_id_str, parent=entity.key),
          ndb.Key('75', entity.key_id_str, parent=entity.key)]


class Prepare(event.Plugin):
  
  def run(self, context):
    context.entities[context.model.get_kind()] = context.model(parent=context.input.get('parent'))
    context.values[context.model.get_kind()] = context.model(parent=context.input.get('parent'))


class InstancePrepare(event.Plugin):
  
  def run(self, context):
    product_instance_key = build_key_from_signature(context)
    context.entities[context.model.get_kind()] = context.model(key=product_instance_key)
    context.values[context.model.get_kind()] = context.model(key=product_instance_key)


class InstanceRead(event.Plugin):
  
  def run(self, context):
    product_instance_key = build_key_from_signature(context)
    product_instance = product_instance_key.get()
    if not product_instance:
      raise event.TerminateAction('not_found_%s' % product_instance_key.urlsafe())
    context.entities[context.model.get_kind()] = product_instance
    context.values[context.model.get_kind()] = copy.deepcopy(product_instance)


class Read(event.Plugin):
  
  def run(self, context):
    _images, _variants, _contents = ndb.get_multi(build_keyes(context))
    if _images and _images.images:
      context.entities[context.model.get_kind()]._images = _images.images
    else:
      context.entities[context.model.get_kind()]._images = []
    if _variants and _variants.variants:
      context.entities[context.model.get_kind()]._variants = _variants.variants
    else:
      context.entities[context.model.get_kind()]._variants = []
    if _contents and _contents.contents:
      context.entities[context.model.get_kind()]._contents = _contents.contents
    else:
      context.entities[context.model.get_kind()]._contents = []
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])


class TemplateReadInstances(event.Plugin):
  
  page_size = ndb.SuperIntegerProperty('5', indexed=False, required=True, default=10)
  
  def run(self, context):
    Instance = context.models['39']
    cursor = Cursor(urlsafe=context.input.get('instances_cursor'))
    ancestor = context.entities[context.model.get_kind()].key
    _instances, cursor, more = Instance.query(ancestor=ancestor).fetch_page(self.page_size, start_cursor=cursor)
    if cursor:
      cursor = cursor.urlsafe()
    if _instances:
      context.entities[context.model.get_kind()]._instances = _instances
    else:
      context.entities[context.model.get_kind()]._instances = []
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])
    context.tmp['instances_cursor'] = cursor
    context.tmp['instances_more'] = more


class UploadImagesSet(event.Plugin):
  
  def run(self, context):
    _images = context.input.get('_images')
    if not _images:
      raise event.TerminateAction()
    context.values[context.model.get_kind()]._images.extend(_images)


class UpdateSet(event.Plugin):
  
  def run(self, context):
    entity_images = context.entities[context.model.get_kind()]._images
    updated_images, delete_images = sort_by_list(entity_images, context.input.get('sort_images'), 'image')
    for image in delete_images:
      context.blob_delete.append(image.image)
      updated_images.remove(image)
    context.values[context.model.get_kind()]._images = updated_images


class WriteImages(event.Plugin):
  
  def run(self, context):
    Images = context.models['73']
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _images = Images(key=_images_key)
    _images.images = context.entities[context.model.get_kind()]._images
    _images.put()
    context.log_entities.append((_images, ))
    context.blob_write = [image.image for image in context.entities[context.model.get_kind()]._images]
    if not context.entities[context.model.get_kind()]._field_permissions['_images']['writable']:
      context.blob_delete = []


class ProcessImages(event.Plugin):
  
  def run(self, context):
    _images = context.values[context.model.get_kind()]._images
    if len(_images):
      _images = ndb.validate_images(_images)
      context.blob_delete.extend([image.image for image in _images])
      context.values[context.model.get_kind()]._images = _images


class WriteVariants(event.Plugin):
  
  def run(self, context):
    Variants = context.models['74']
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _variants = Variants(key=_variants_key)
    _variants.variants = context.entities[context.model.get_kind()]._variants
    _variants.put()
    context.log_entities.append((_variants, ))


class WriteContents(event.Plugin):
  
  def run(self, context):
    Contents = context.models['75']
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _contents = Contents(key=_contents_key)
    _contents.contents = context.entities[context.model.get_kind()]._contents
    _contents.put()
    context.log_entities.append((_contents, ))


class DeleteImages(event.Plugin):
  
  def run(self, context):
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _images = _images_key.get()
    context.blob_delete = _images.images
    _images.delete()
    context.log_entities.append((_images, ))


class DeleteVariants(event.Plugin):
  
  def run(self, context):
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _variants = _variants_key.get()
    _variants.delete()
    context.log_entities.append((_variants, ))


class DeleteContents(event.Plugin):
  
  def run(self, context):
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _contents = _contents_key.get()
    _contents.delete()
    context.log_entities.append((_contents, ))


class CategoryUpdate(event.Plugin):
  
  file_path = ndb.SuperStringProperty('5', indexed=False, required=True)
  
  def run(self, context):
    # this code builds leaf categories for selection with complete names, 3.8k of them
    Category = context.models['17']
    data = []
    with file(self.file_path) as f:
      for line in f:
        if not line.startswith('#'):
          data.append(line.replace('\n', ''))
    write_data = []
    sep = ' > '
    parent = None
    dig = 0
    for i, item in enumerate(data):
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
        new_cat['state'] = 'searchable'
        write_data.append(Category(**new_cat))
    ndb.put_multi(write_data)
