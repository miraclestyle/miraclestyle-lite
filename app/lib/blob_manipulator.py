# -*- coding: utf-8 -*-
'''
Created on Jun 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import cloudstorage

from google.appengine.ext import blobstore
from google.appengine.api import images

from app import util


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
