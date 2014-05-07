# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.ext import blobstore

from app import ndb, settings
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


class Read(event.Plugin):
  
  def run(self, context):
    start = context.input.get('images_cursor')
    end = start + settings.CATALOG_PAGE + 1  # Always ask for one extra image, so we can determine if there are more images to get in next round.
    if full:  # @todo Have no idea what is this?
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


class UploadImagesPrepare(event.Plugin):
  
  def run(self, context):
    from app.srv import marketing
    images = context.input.get('images')
    upload_url = context.input.get('upload_url')
    if upload_url:
      context.output['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.CATALOG_IMAGE_BUCKET)
      return  # @todo Do we brake entire plugins loop here, and if so, how do we do it?
    else:
      if not images: # if no images were saved, do nothing...
        return  # @todo Do we brake entire plugins loop here, and if so, how do we do it?
    i = marketing.CatalogImage.query(ancestor=context.entities['35'].key).count()  # Get last sequence.
    for image in images:
      image.set_key(str(i), parent=context.entities['35'].key)
      i += 1
    context.images = images


class UploadImagesWrite(event.Plugin):
  
  def run(self, context):
    ndb.put_multi(context.images)
    for image in context.images:
      if image:
        context.log_entities.append((image, ))
        blob.Manager.used_blobs(image.image)  # @todo Can we mark blobs as used prior being logged, or do we need to do it after logging?
    context.entities['35']._images.extend(context.images)
