# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy

from google.appengine.ext import blobstore

from app import ndb, settings
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


def read_catalog_images(context, full=None):
  start = context.input.get('images_cursor')
  end = start + settings.CATALOG_PAGE + 1  # Always ask for one extra image, so we can determine if there are more images to get in next round.
  if full:
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
  context.images_cursor = start + settings.CATALOG_PAGE  # @todo Next images cursor. Not sure if this is needed or the client does the mageic?
  context.more_images = more


class Read(event.Plugin):
  
  def run(self, context):
    read_catalog_images(context)
    context.values['35']._images = copy.deepcopy(context.entities['35']._images)

class UpdateRead(event.Plugin):
  
  def run(self, context):
    read_catalog_images(context, True)
    context.values['35']._images = copy.deepcopy(context.entities['35']._images)


class UpdateSet(event.Plugin):
  
  def run(self, context):
    context.values['35'].name = context.input.get('name')
    context.values['35'].discontinue_date = context.input.get('discontinue_date')
    context.values['35'].publish_date = context.input.get('publish_date')
    context.values['35']._images = context.input.get('_images')
    new_images = []
    context.delete_image_keys = []
    context.delete_blob_image_keys = []
    if context.values['35']._images:
      for i, image in enumerate(context.values['35']._images):
        image.set_key(str(i), parent=context.values['35'].key)
        new_images.append(image.key)
    if len(context.values['35']._images):
      context.values['35'].cover = context.values['35']._images[0].key
    for image in context.entities['35']._images:
      if image.key not in new_images:
        context.delete_image_keys.append(image.key)
        context.delete_blob_image_keys.append(image.image)
    context.entities['35']._images = []


class UpdateWrite(event.Plugin):
  
  def run(self, context):
    if context.entities['35']._field_permissions['_images']['writable']:
      if len(context.delete_image_keys):
        ndb.delete_multi(context.delete_image_keys)
      if len(context.delete_blob_image_keys):
        blob.Manager.unused_blobs(context.delete_blob_image_keys)
    context.entities['35'].put()
    if len(context.entities['35']._images):
      ndb.put_multi(context.entities['35']._images)


class UploadImagesSet(event.Plugin):
  
  def run(self, context):
    from app.srv import marketing
    images = context.input.get('images')
    upload_url = context.input.get('upload_url')
    if upload_url:
      context.output['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.CATALOG_IMAGE_BUCKET)
      raise event.TerminateAction()
    else:
      if not images:  # If no images were saved, do nothing.
        raise event.TerminateAction()
    i = marketing.CatalogImage.query(ancestor=context.entities['35'].key).count()  # Get last sequence.
    for image in images:
      image.set_key(str(i), parent=context.entities['35'].key)
      i += 1
    context.entities['35']._images = []
    context.values['35']._images = images


class UploadImagesWrite(event.Plugin):
  
  def run(self, context):
    if len(context.entities['35']._images):
      ndb.put_multi(context.entities['35']._images)
      for image in context.entities['35']._images:
        if image:
          context.log_entities.append((image, ))


class UploadImagesUsedBlobs(event.Plugin):
  
  def run(self, context):
    for image in context.entities['35']._images:
      if image:
        blob.Manager.used_blobs(image.image)
