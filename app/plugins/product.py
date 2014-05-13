# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy

from google.appengine.datastore.datastore_query import Cursor

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
    context.entities[context.model.get_kind()] = context.model(parent=context.input.get('catalog'))
    context.values[context.model.get_kind()] = context.model(parent=context.input.get('catalog'))


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
