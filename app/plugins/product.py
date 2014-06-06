# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json
import copy
import hashlib

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, memcache, util
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr
from app.lib.list_manipulator import sort_by_list


def build_key_from_signature(context):
  variant_signature = context.input.get('variant_signature')
  key_id = hashlib.md5(json.dumps(variant_signature)).hexdigest()
  product_instance_key = context.model.build_key(key_id, parent=context.input.get('parent'))
  return product_instance_key


class Prepare(ndb.BaseModel):
  
  def run(self, context):
    context.entities[context.model.get_kind()] = context.model(parent=context.input.get('parent'))
    context.values[context.model.get_kind()] = context.model(parent=context.input.get('parent'))


class InstancePrepare(ndb.BaseModel):
  
  def run(self, context):
    product_instance_key = build_key_from_signature(context)
    context.entities[context.model.get_kind()] = context.model(key=product_instance_key)
    context.values[context.model.get_kind()] = context.model(key=product_instance_key)


class InstanceRead(ndb.BaseModel):
  
  def run(self, context):
    product_instance_key = build_key_from_signature(context)
    product_instance = product_instance_key.get()
    if not product_instance:
      raise event.TerminateAction('not_found_%s' % product_instance_key.urlsafe())
    context.entities[context.model.get_kind()] = product_instance
    context.values[context.model.get_kind()] = copy.deepcopy(product_instance)


class TemplateReadInstances(ndb.BaseModel):
  
  page_size = ndb.SuperIntegerProperty('1', indexed=False, required=True, default=10)
  
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


class UploadImagesSet(ndb.BaseModel):
  
  def run(self, context):
    images = context.input.get('images')
    if not images:
      raise event.TerminateAction()
    context.values[context.model.get_kind()].images.extend(images)


class UpdateSet(ndb.BaseModel):
  
  def run(self, context):
    entity_images = context.entities[context.model.get_kind()].images
    updated_images, delete_images = sort_by_list(entity_images, context.input.get('sort_images'), 'image')
    for image in delete_images:
      context.blob_delete.append(image.image)
      updated_images.remove(image)
    context.values[context.model.get_kind()].images = updated_images


class WriteImages(ndb.BaseModel):
  
  def run(self, context):
    context.blob_write = [image.image for image in context.entities[context.model.get_kind()].images]
    if not context.entities[context.model.get_kind()]._field_permissions['_images']['writable']:
      context.blob_delete = []


class ProcessImages(ndb.BaseModel):
  
  def run(self, context):
    images = context.values[context.model.get_kind()].images
    if len(images):
      images = ndb.validate_images(images)
      context.blob_delete.extend([image.image for image in images])
      context.values[context.model.get_kind()].images = images


class DeleteImages(ndb.BaseModel):
  
  def run(self, context):
    context.blob_delete = [image.image for image in context.entities[context.model.get_kind()].images]


class CategoryUpdate(ndb.BaseModel):
  
  file_path = ndb.SuperStringProperty('1', indexed=False, required=True)
  
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
