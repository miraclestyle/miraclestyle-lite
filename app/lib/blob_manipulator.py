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


def create_upload_url(upload_url, gs_bucket_name):
  return blobstore.create_upload_url(upload_url, gs_bucket_name=gs_bucket_name)


def parse(blob_keys):
  results = []
  if not isinstance(blob_keys, (list, tuple)):
    blob_keys = [blob_keys]
  for blob_key in blob_keys:
    if isinstance(blob_key, blobstore.BlobKey):
      results.append(blob_key)
  return results


def alter_image(original_image, make_copy=False, copy_name=None, transform=False, width=0, height=0, crop_to_fit=False, crop_offset_x=0.0, crop_offset_y=0.0):
  result = {}
  new_image = copy.deepcopy(original_image)
  original_gs_object_name = new_image.gs_object_name
  new_gs_object_name = new_image.gs_object_name
  if make_copy:
    new_gs_object_name = '%s_%s' % (new_image.gs_object_name, copy_name)
  blob_key = None
  try:
    if make_copy:
      readonly_blob = cloudstorage.open(original_gs_object_name[3:], 'r')
      blob = readonly_blob.read()
      readonly_blob.close()
      writable_blob = cloudstorage.open(new_gs_object_name[3:], 'w')
    else:
      readonly_blob = cloudstorage.open(new_gs_object_name[3:], 'r')
      blob = readonly_blob.read()
      readonly_blob.close()
      writable_blob = cloudstorage.open(new_gs_object_name[3:], 'w')
    if transform:
      image = images.Image(image_data=blob)
      image.resize(width,
                   height,
                   crop_to_fit=crop_to_fit,
                   crop_offset_x=crop_offset_x,
                   crop_offset_y=crop_offset_y)
      blob = image.execute_transforms(output_encoding=image.format)
      new_image.width = width
      new_image.height = height
      new_image.size = len(blob)
    writable_blob.write(blob)
    writable_blob.close()
    if original_gs_object_name != new_gs_object_name or new_image.serving_url is None:
      new_image.gs_object_name = new_gs_object_name
      blob_key = blobstore.create_gs_key(new_gs_object_name)
      new_image.image = blobstore.BlobKey(blob_key)
      new_image.serving_url = images.get_serving_url(new_image.image)
  except Exception as e:
    util.logger(e, 'exception')
    if blob_key != None:
      result['delete'] = blob_key
  else:
    result['save'] = new_image
  finally:
    return result
