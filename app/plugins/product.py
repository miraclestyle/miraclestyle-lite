# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import hashlib

from app import ndb, settings
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


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
    variant_signature = context.input.get('variant_signature')
    key_id = hashlib.md5(str(variant_signature)).hexdigest()
    context.entities[context.model.get_kind()] = context.model(id=key_id, parent=context.input.get('parent'))
    context.values[context.model.get_kind()] = context.model(id=key_id, parent=context.input.get('parent'))


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
    context.values[context.model.get_kind()] = ndb.copy.deepcopy(context.entities[context.model.get_kind()])
    
    context.values[context.model.get_kind()]._images[0].content_type = 'foo'
    
    # test for deep copy
    #assert context.values[context.model.get_kind()]._images[0].content_type == context.entities[context.model.get_kind()]._images[0].content_type
    


class UploadImagesSet(event.Plugin):
  
  def run(self, context):
    _images = context.input.get('_images')
    if not _images:
      raise event.TerminateAction()
    context.values[context.model.get_kind()]._images.extend(_images)


class UpdateSet(event.Plugin):
  
  def run(self, context):
    new_images = []
    context.delete_blobs = []
    if context.values[context.model.get_kind()]._images:
      for image in context.values[context.model.get_kind()]._images:
        new_images.append(image.image)
    for image in context.entities[context.model.get_kind()]._images:
      if image.image not in new_images:
        context.delete_blobs.append(image.image)

      
class WriteImages(event.Plugin):
  
  def run(self, context):
    from app.srv import product
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _images = product.Images(key=_images_key)
    _images.images = context.entities[context.model.get_kind()]._images
    _images.put()
    context.log_entities.append((_images, ))
    context.write_blobs = [image.image for image in context.entities[context.model.get_kind()]._images]
    if not context.entities[context.model.get_kind()]._field_permissions['_images']['writable']:
      context.delete_blobs = []


class ProcessImages(event.Plugin):
  
  def run(self, context):
    _images = context.values[context.model.get_kind()]._images
    if len(_images):
      for i, image in enumerate(_images):
        if image is None:
          _images.remove(image)
      if len(_images):
        _images = ndb.validate_images(_images)
      context.values[context.model.get_kind()]._images = _images


class WriteVariants(event.Plugin):
  
  def run(self, context):
    from app.srv import product
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _variants = product.Variants(key=_variants_key)
    _variants.variants = context.entities[context.model.get_kind()]._variants
    _variants.put()
    context.log_entities.append((_variants, ))


class WriteContents(event.Plugin):
  
  def run(self, context):
    from app.srv import product
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _contents = product.Contents(key=_contents_key)
    _contents.contents = context.entities[context.model.get_kind()]._contents
    _contents.put()
    context.log_entities.append((_contents, ))


class DeleteImages(event.Plugin):
  
  def run(self, context):
    from app.srv import product
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _images = _images_key.get()
    context.delete_blobs = _images.images
    _images.delete()
    context.log_entities.append((_images, ))


class DeleteVariants(event.Plugin):
  
  def run(self, context):
    from app.srv import product
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _variants = _variants_key.get()
    _variants.delete()
    context.log_entities.append((_variants, ))


class DeleteContents(event.Plugin):
  
  def run(self, context):
    from app.srv import product
    _images_key, _variants_key, _contents_key = build_keyes(context)
    _contents = _contents_key.get()
    _contents.delete()
    context.log_entities.append((_contents, ))
    
    
class CategoryUpdate(event.Plugin):
  
  def run(self, context):
    # this code builds leaf categories for selection with complete names, 3.8k of them
    from app.srv.product import Category
    data = []
    with file(settings.PRODUCT_CATEGORY_DATA_FILE) as f:
      for line in f:
        if not line.startswith('#'):
          data.append(line.replace("\n", ''))
        
    write_data = []
    sep = ' > '
    parent = None
    dig = 0
    for ii,item in enumerate(data):
      new_cat = {}
      current = item.split(sep)
      try:
        next = data[ii+1].split(sep)
      except IndexError as e:
        next = current
      if len(next) == len(current):
         current_total = len(current)-1
         last = current[current_total]
         parent = current[current_total-1]
         new_cat['id'] = hashlib.md5(last).hexdigest()
         new_cat['parent_record'] = Category.build_key(hashlib.md5(parent).hexdigest())
         new_cat['name'] = last
         new_cat['complete_name'] = " / ".join(current[:current_total+1])
         new_cat['state'] = 'searchable'
         write_data.append(Category(**new_cat))
    ndb.put_multi(write_data)
