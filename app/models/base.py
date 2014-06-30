# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import cgi

from google.appengine.ext import blobstore
from google.appengine.api import images

import cloudstorage

from app import ndb
from app.tools.manipulator import set_attr, get_attr, safe_eval


class ImageManager(object):
  
  def get(self):
    """
      The get method should just perform the logic that will retrieve the items either from datastore or the property
    """
    pass
  
  def delete(self):
    pass
  
  def process(self):
    pass
  
  def upload(self):
    pass
  
  def update(self):
    pass


def validate_images(objects):
  '''"objects" argument is a list of valid instance(s)
  of Image class that require validation!
  
  '''
  to_delete = []
  for obj in objects:
    if obj.width or obj.height:
      continue
    cloudstorage_file = cloudstorage.open(filename=obj.gs_object_name[3:])
    # This will throw an error if the file does not exist in cloudstorage.
    image_data = cloudstorage_file.read()  # We must read the file in order to analyize width/height of an image.
    # This will throw an error if the file is not an image, or is corrupted.
    try:
      image = images.Image(image_data=image_data)
      width = image.width  # This property causes _update_dimensions function that might fail to read the image if image meta-data is corrupted, indicating it's not good.
      height = image.height
    except images.NotImageError as e:
      # cannot do objects.remove while in for loop objects
      to_delete.append(obj)
    for o in to_delete:
      objects.remove(o)
    cloudstorage_file.close()
    obj.populate(**{'width': width,
                    'height': height})
    del image_data, image  # Free memory
  
  @ndb.tasklet
  def async(obj):
    if obj.serving_url is None:
      obj.serving_url = yield images.get_serving_url_async(obj.image)
    raise ndb.Return(obj)
  
  @ndb.tasklet
  def helper(objects):
    results = yield map(async, objects)
    raise ndb.Return(results)
  
  return helper(objects).get_result()


def _structured_image_property_format(prop, value):
  value = ndb._property_value_format(prop, value)
  if prop._repeated:
    blobs = value
  else:
    blobs = [value]
  out = []
  for blob in blobs:
    # These will throw errors if the 'blob' is not cgi.FileStorage.
    if not isinstance(blob, cgi.FieldStorage) and not prop._required:
      continue
    file_info = blobstore.parse_file_info(blob)
    blob_info = blobstore.parse_blob_info(blob)
    meta_required = ('image/jpeg', 'image/jpg', 'image/png')
    if file_info.content_type not in meta_required:
      raise ndb.PropertyError('invalid_image_type')  # First line of validation based on meta data from client.
    out.append(prop._modelclass(**{'size': file_info.size,
                                   'content_type': file_info.content_type,
                                   'gs_object_name': file_info.gs_object_name,
                                   'image': blob_info.key()}))
  if prop._validate_images:
    out = validate_images(out)
  if not prop._repeated:
    try:
      out = out[0]
    except IndexError as e:
      out = None
  return out


class SuperLocalStructuredImageProperty(ndb.SuperLocalStructuredProperty):
  
  def __init__(self, *args, **kwargs):
    self._validate_images = kwargs.pop('validate_images', None)
    super(SuperLocalStructuredImageProperty, self).__init__(*args, **kwargs)
  
  def format(self, value):
    return _structured_image_property_format(self, value)


class SuperStructuredImageProperty(ndb.SuperStructuredProperty):
  
  def __init__(self, *args, **kwargs):
    self._validate_images = kwargs.pop('validate_images', None)
    super(SuperStructuredImageProperty, self).__init__(*args, **kwargs)
  
  def format(self, value):
    return _structured_image_property_format(self, value)


class SuperImageKeyProperty(ndb._BaseProperty, ndb.BlobKeyProperty):
  
  def format(self, value):
    value = ndb._property_value_format(self, value)
    if self._repeated:
      blobs = value
      out = []
      to_delete = []
      for v in value:
        try:
          out.append(blobstore.parse_blob_info(v).key())
        except:
          to_delete.append(v)
          out.append(blobstore.BlobInfo(v))
      value = out
      for d in to_delete:
         blobs.remove(d)
    else:
      blobs = [value]
      try:
        value = blobstore.parse_blob_info(value).key()
      except:
        return blobstore.BlobKey(value)
    for blob in blobs:
      info = blobstore.parse_file_info(blob)
      meta_required = ('image/jpeg', 'image/jpg', 'image/png')
      if info.content_type not in meta_required:
        raise ndb.PropertyError('invalid_file_type')
      # This code below is used to validate if the blob that's uploaded to gcs is an image.
      gs_object_name = info.gs_object_name
      cloudstorage_file = cloudstorage.open(filename=gs_object_name[3:])
      image_data = cloudstorage_file.read()  # We must read the file in order to analyize width/height of an image.
      # Will throw error if the file is not an image, or it's just corrupted.
      load_image = images.Image(image_data=image_data)
      # Closes the pipeline.
      cloudstorage_file.close()
      del load_image, cloudstorage_file  # Free memory.
    return value


class Image(ndb.BaseModel):
  
  _kind = 69
  
  image = SuperImageKeyProperty('1', required=True, indexed=False)
  content_type = ndb.SuperStringProperty('2', required=True, indexed=False)
  size = ndb.SuperFloatProperty('3', required=True, indexed=False)
  width = ndb.SuperIntegerProperty('4', indexed=False)
  height = ndb.SuperIntegerProperty('5', indexed=False)
  gs_object_name = ndb.SuperStringProperty('6', indexed=False)
  serving_url = ndb.SuperStringProperty('7', indexed=False)


class Role(ndb.BaseExpando):
  
  _kind = 66
  
  # feature proposition (though it should create overhead due to the required drilldown process!)
  # parent_record = ndb.SuperKeyProperty('1', kind='Role', indexed=False)
  # complete_name = ndb.SuperTextProperty('2')
  name = ndb.SuperStringProperty('1', required=True)
  active = ndb.SuperBooleanProperty('2', required=True, default=True)
  permissions = ndb.SuperPickleProperty('3', required=True, default=[], compressed=False)  # List of Permissions instances. Validation is required against objects in this list, if it is going to be stored in datastore.
  
  _default_indexed = False
  
  def run(self, context):
    for permission in self.permissions:
      permission.run(self, context)


class GlobalRole(Role):
  
  _kind = 67
