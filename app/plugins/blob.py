# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import cloudstorage

from google.appengine.ext import blobstore
from google.appengine.api import images

from app import ndb, settings, memcache, util
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


def parse(blob_keys):
  results = []
  if not isinstance(blob_keys, (list, tuple)):
    blob_keys = [blob_keys]
  for blob_key in blob_keys:
    if isinstance(blob_key, blobstore.BlobKey):
      results.append(blob_key)
  return results


class URL(event.Plugin):
  
  gs_bucket_name = ndb.SuperStringProperty('5', indexed=False, required=True)
  
  def run(self, context):
    upload_url = context.input.get('upload_url')
    if upload_url:
      context.output['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=self.gs_bucket_name)
      raise event.TerminateAction()


class Update(event.Plugin):
  
  blob_delete = ndb.SuperStringProperty('5', indexed=False)
  blob_write = ndb.SuperStringProperty('6', indexed=False)
  
  def run(self, context):
    if self.blob_delete:
      blob_delete = get_attr(context, self.blob_delete)
    else:
      blob_delete = context.blob_delete
    if blob_delete:
      context.blob_unused.extend(parse(blob_delete))
    if self.blob_write:
      blob_write = get_attr(context, self.blob_write)
    else:
      blob_write = context.blob_write
    if blob_write:
      blob_write = parse(blob_write)
      for blob_key in blob_write:
        if blob_key in context.blob_unused:
          context.blob_unused.remove(blob_key)


class TransformImage(event.Plugin):
  
  blob_transform = ndb.SuperStringProperty('5', indexed=False)
  set_image = ndb.SuperStringProperty('6', indexed=False)
  
  def run(self, context):
    if self.blob_transform:
      blob_transform = get_attr(context, self.blob_transform)
    else:
      blob_transform = context.blob_transform
    if blob_transform:
      new_image = copy.deepcopy(blob_transform)
      gs_object_name = '%s_copy' % new_image.gs_object_name
      blob_key = blobstore.create_gs_key(gs_object_name)
      try:
        with cloudstorage.open(new_image.gs_object_name[3:], 'r') as r:
          blob = r.read()
          with cloudstorage.open(gs_object_name[3:], 'w') as w:
            image = images.Image(image_data=blob)
            image_width = image.width
            image_height = int(image.width * 1.5)  # Force aspect ratio
            image.resize(image_width, image_height, crop_to_fit=True, crop_offset_x=0.0, crop_offset_y=0.0)
            new_image.gs_object_name = gs_object_name
            new_image.width = image_width
            new_image.height = image_height
            blob = image.execute_transforms(output_encoding=image.format)
            new_image.size = len(blob)
            new_image.image = blobstore.BlobKey(blob_key)
            new_image.serving_url = images.get_serving_url(new_image.image)
            w.write(blob)
      except Exception as e:
        util.logger(e, 'exception')
        context.blob_delete.append(blob_key)
      finally:
        set_attr(context, self.set_image, new_image)
