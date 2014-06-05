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
from app.srv import event  # @todo We need this import for event.TerminateAction() exception. Is there a workaround?
from app.lib.attribute_manipulator import set_attr, get_attr


def parse(blob_keys):
  results = []
  if not isinstance(blob_keys, (list, tuple)):
    blob_keys = [blob_keys]
  for blob_key in blob_keys:
    if isinstance(blob_key, blobstore.BlobKey):
      results.append(blob_key)
  return results


def alter_image(original_image, **config):
  results = {}
  new_image = copy.deepcopy(original_image)
  original_gs_object_name = new_image.gs_object_name
  new_gs_object_name = new_image.gs_object_name
  if config.get('copy'):
    new_gs_object_name = '%s_%s' % (new_image.gs_object_name, config['sufix'])
  blob_key = None
  try:
    writable_blob = cloudstorage.open(new_gs_object_name[3:], 'w')
    if config.get('copy'):
      readonly_blob = cloudstorage.open(original_gs_object_name[3:], 'r')
      blob = readonly_blob.read()
    else:
      blob = writable_blob.read()
    if config.get('transform'):
      image = images.Image(image_data=blob)
      image.resize(config['width'],
                   config['height'],
                   crop_to_fit=config['crop_to_fit'],
                   crop_offset_x=config['crop_offset_x'],
                   crop_offset_y=config['crop_offset_y'])
      blob = image.execute_transforms(output_encoding=image.format)
      new_image.width = config['width']
      new_image.height = config['height']
      new_image.size = len(blob)
    writable_blob.write(blob)
    if config.get('copy'):
      readonly_blob.close()
    writable_blob.close()
    if original_gs_object_name != new_gs_object_name:
      new_image.gs_object_name = new_gs_object_name
      blob_key = blobstore.create_gs_key(new_gs_object_name)
      new_image.image = blobstore.BlobKey(blob_key)
      new_image.serving_url = images.get_serving_url(new_image.image)
  except Exception as e:
    util.logger(e, 'exception')
    if blob_key != None:
      results['blob_delete'] = blob_key
  finally:
    results['new_image'] = new_image
    return results


class URL(ndb.BaseModel):
  
  gs_bucket_name = ndb.SuperStringProperty('1', indexed=False, required=True)
  
  def run(self, context):
    upload_url = context.input.get('upload_url')
    if upload_url:
      context.output['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=self.gs_bucket_name)
      raise event.TerminateAction()


class Update(ndb.BaseModel):
  
  blob_delete = ndb.SuperStringProperty('1', indexed=False)
  blob_write = ndb.SuperStringProperty('2', indexed=False)
  
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


class AlterImage(ndb.BaseModel):
  
  source = ndb.SuperStringProperty('1', indexed=False)
  destination = ndb.SuperStringProperty('2', indexed=False)
  config = ndb.SuperJsonProperty('3', indexed=False, required=True, default={})
  
  def run(self, context):
    if self.source:
      original_image = get_attr(context, self.source)
    else:
      original_image = context.blob_transform
    if original_image:
      results = alter_image(original_image, self.config)
      if results.get('blob_delete'):
        context.blob_delete.append(results['blob_delete'])
      if results.get('new_image'):
        set_attr(context, self.destination, results['new_image'])


class AlterImages(ndb.BaseModel):
  
  source = ndb.SuperStringProperty('1', indexed=False)
  destination = ndb.SuperStringProperty('2', indexed=False)
  config = ndb.SuperJsonProperty('3', indexed=False, required=True, default={})
  
  def run(self, context):
    @ndb.tasklet
    def alter_image_async(source, destination):
      @ndb.tasklet
      def generate():
        original_image = get_attr(context, source)
        results = alter_image(original_image, self.config)
        if results.get('blob_delete'):
          context.blob_delete.append(results['blob_delete'])
        if results.get('new_image'):
          set_attr(context, destination, results['new_image'])
        raise ndb.Return(True)
      yield generate()
      raise ndb.Return(True)
    
    futures = []
    images = get_attr(context, self.source)
    for i, image in enumerate(images):
      source = '%s.%s' % (self.source, i)
      destination = '%s.%s' % (self.destination, i)
      future = alter_image_async(source, destination)
      futures.append(future)
    return ndb.Future.wait_all(futures)
