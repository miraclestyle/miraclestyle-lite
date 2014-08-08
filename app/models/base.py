# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import cgi
import cloudstorage
import copy
import time

from google.appengine.ext import blobstore
from google.appengine.api import images, urlfetch
from google.appengine.datastore.datastore_query import Cursor

from app import orm, mem, settings
from app.util import *


# @see https://developers.google.com/appengine/docs/python/googlecloudstorageclient/retryparams_class
default_retry_params = cloudstorage.RetryParams(initial_delay=0.2, max_delay=5.0,
                                                backoff_factor=2, max_retries=5,
                                                max_retry_period=60, urlfetch_timeout=30)
cloudstorage.set_default_retry_params(default_retry_params)


class Image(orm.BaseExpando):
  
  _kind = 69
  
  image = orm.SuperBlobKeyProperty('1', required=True, indexed=False)
  content_type = orm.SuperStringProperty('2', required=True, indexed=False)
  size = orm.SuperFloatProperty('3', required=True, indexed=False)
  gs_object_name = orm.SuperStringProperty('4', required=True, indexed=False)
  serving_url = orm.SuperStringProperty('5', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'proportion': orm.SuperFloatProperty('6')
    }


class Role(orm.BaseExpando):
  
  _kind = 66
  
  # feature proposition (though it should create overhead due to the required drilldown process!)
  # parent_record = orm.SuperKeyProperty('1', kind='Role', indexed=False)
  # complete_name = orm.SuperTextProperty('2')
  name = orm.SuperStringProperty('1', required=True)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  permissions = orm.SuperPickleProperty('3', required=True, default=[], compressed=False) # List of Permissions instances. Validation is required against objects in this list, if it is going to be stored in datastore.
  
  _default_indexed = False
  
  def run(self, context):
    for permission in self.permissions:
      permission.run(self, context)


class GlobalRole(Role):
  
  _kind = 67


class SuperStructuredPropertyImageManager(orm.SuperStructuredPropertyManager):
  
  def _update_blobs(self):
    if self.has_value() and isinstance(self._property, _BaseImageProperty):
      if self._property._repeated:
        entities = self._property_value
      else:
        entities = [self._property_value]
      for entity in entities:
        if (entity._state == 'deleted'):
          self._property.delete_blobs_on_success(entity.image)
        else:
          self._property.save_blobs_on_success(entity.image, False)
  
  def _pre_update_local(self):
    self._update_blobs()
    super(SuperStructuredPropertyImageManager, self)._pre_update_local()
  
  def _post_update_remote_single(self):
    self._update_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_single()
  
  def _post_update_remote_multi(self):
    self._update_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_multi()
  
  def _delete_remote(self):
    cursor = Cursor()
    limit = 200
    query = self._property.get_modelclass().query(ancestor=self._entity.key)
    while True:
      _entities, cursor, more = query.fetch_page(limit, start_cursor=cursor)
      if len(_entities):
        for entity in _entities:
          if isinstance(self._property, _BaseImageProperty):
            self._property.delete_blobs_on_success(entity.image)
        orm.delete_multi([entity.key for entity in _entities])
        if not cursor or not more:
          break
      else:
        break
  
  def _delete_remote_single(self):
    property_value_key = orm.Key(self._property.get_modelclass().get_kind(), self._entity.key_id_str, parent=self._entity.key)
    entity = property_value_key.get()
    if isinstance(self._property, _BaseImageProperty):
      self._property.delete_blobs_on_success(entity.image)
    entity.key.delete()
  
  def duplicate(self):
    '''Override duplicate. Parent duplicate method will retrieve all data into self._property_value, and later on,
    here we can finalize duplicate by copying the blob.
    
    '''
    super(SuperStructuredPropertyImageManager, self).duplicate()
    @orm.tasklet
    def async(entity):
      gs_object_name = entity.gs_object_name
      new_gs_object_name = '%s_duplicate' % entity.gs_object_name
      readonly_blob = cloudstorage.open(gs_object_name[3:], 'r')
      writable_blob = cloudstorage.open(new_gs_object_name[3:], 'w')
      # Less consuming memory write, can be only used when using brute force copy.
      # There is no copy feature in cloudstorage sdk, so we have to implement our own!
      while True:
        blob_segment = readonly_blob.read(1000000)  # Read 1mb per write, that should be enough.
        if not blob_segment:
          break
        writable_blob.write(blob_segment)
      readonly_blob.close()
      writable_blob.close()
      entity.gs_object_name = new_gs_object_name
      blob_key = blobstore.create_gs_key(new_gs_object_name)
      entity.image = blobstore.BlobKey(blob_key)
      entity.serving_url = yield images.get_serving_url_async(entity.image)
      self._property.save_blobs_on_success(entity.image)
      raise orm.Return(entity)
    
    @orm.tasklet
    def mapper(entities):
      out = yield map(async, entities)
      raise orm.Return(out)
    
    if isinstance(self._property, _BaseImageProperty):
      entities = self._property_value
      if not self._property._repeated:
        entities = [entities]
      mapper(entities).get_result()
    return self._property_value
  
  def process(self):
    '''This function should be called inside a taskqueue.
    It will perform all needed operations based on the property configuration on how to process its images.
    Resizing, cropping, and generation of serving url in the end.
    
    '''
    if self.has_value() and not self.has_future():  # In case value is a future we cannot proceed. Everything must be already loaded!
      if isinstance(self._property, _BaseImageProperty):
        if self._property._repeated:
          processed_entities = map(self._property.process, self.value)
          setattr(self._entity, self.property_name, processed_entities)
        else:
          processed_entity = self._property.process(self.value)
          setattr(self._entity, self.property_name, processed_entity)


class _BaseBlobProperty(object):
  '''Base helper class for blob-key-like orm properties.
  This property should be used in conjunction with orm Property baseclass, like so:
  class PDF(BaseBlobKeyInterface, orm.Property):
  ....
  def argument_format(self, value):
  Example usage:
  new_file = gcs.open(value.path)
  new_file.write(..)
  new_file.close()
  new_blobstore_key = blobstore.create_gs_key(gs_object_name=new_file.gs_object_name)
  self.blob_collect_on_success(new_blobstore_key)
  now upon failure anywhere in the application, the new_blobstore_key will be deleted.
  but if no error has occurred the new_blobstore_key will not be deleted from the blobstore.
  Functions below accept delete= kwarg. That argument is used if you dont want to add the blobkey automatically in queue for delete.
  Logically, all newly provided keys are automatically placed in delete queue which will later be stripped away from queue
  based on which state they were assigned.
  Possible states that we work with:
  - success => happens after iO engine has completed entire cycle without throwing any errors (including formatting errors)
  - error => happens immidiately after iO engine raises an error.
  - finally => happens after entire iO cycle has completed.
  
  '''
  @classmethod
  def get_blobs(cls):
    # This function acts as a getter from in-memory storage.
    blobs = mem.temp_get(settings.BLOBKEYMANAGER_KEY, None)
    if blobs is None:
      mem.temp_set(settings.BLOBKEYMANAGER_KEY, {'delete': []})
    blobs = mem.temp_get(settings.BLOBKEYMANAGER_KEY)
    return blobs
  
  @classmethod
  def normalize_blobs(cls, blobs):
    # Helper to transform single item into a list for iteration.
    if isinstance(blobs, (list, tuple)):
      return blobs
    else:
      return [blobs]
  
  @classmethod
  def _update_blobs(cls, update_blobs, state=None, delete=True):
    update_blobs = cls.normalize_blobs(update_blobs)
    blobs = cls.get_blobs()
    for blob in update_blobs:
      if state not in blobs:
        blobs[state] = []
      if blob not in blobs[state]:
        blobs[state].append(blob)
    if state is not None and not state.startswith('delete') and delete is True:
      # If state is said to be delete_* or delete then there is no need to store them in delete queue.
      cls._update_blobs(update_blobs, 'delete')
  
  @classmethod
  def delete_blobs(cls, blobs):
    # Delete blobes no matter what happens.
    cls._update_blobs(blobs, 'delete')
  
  @classmethod
  def delete_blobs_on_error(cls, blobs, delete=True):
    # Marks blobs to be deleted upon application error.
    cls._update_blobs(blobs, 'delete_error', delete)
  
  @classmethod
  def delete_blobs_on_success(cls, blobs, delete=True):
    # Marks blobs to be deleted upon success.
    cls._update_blobs(blobs, 'delete_success', delete)
  
  @classmethod
  def save_blobs(cls, blobs, delete=True):
    # Save blobes no matter what happens.
    cls._update_blobs(blobs, 'collect', delete)
  
  @classmethod
  def save_blobs_on_error(cls, blobs, delete=True):
    # Marks blobs to be preserved upon application error.
    cls._update_blobs(blobs, 'collect_error', delete)
  
  @classmethod
  def save_blobs_on_success(cls, blobs, delete=True):
    # Marks blobs to be preserved upon success.
    cls._update_blobs(blobs, 'collect_success', delete)


class _BaseImageProperty(_BaseBlobProperty):
  '''Base helper class for image-like properties.
  This class should work in conjunction with orm.Property, because it does not implement anything of orm.
  Example:
  class NewImageProperty(_BaseImageProperty, orm.Property):
  ...
  
  '''
  def __init__(self, *args, **kwargs):
    self._process = kwargs.pop('process', None)
    self._process_config = kwargs.pop('process_config', {})
    self._argument_format_upload = kwargs.pop('argument_format_upload', False)
    super(_BaseImageProperty, self).__init__(*args, **kwargs)
    self._managerclass = SuperStructuredPropertyImageManager
  
  def process(self, value):
    ''' @todo How efficient/fast is image = images.Image(filename=new_value.gs_object_name)???
    class Image(image_data=None, blob_key=None, filename=None)
    The Image constructor takes the data of the image to transform as a bytestring (the image_data argument)
    or the BlobKey of a Blobstore value, or a BlobInfo object, or a Google Cloud Storage image file name of the
    image to transform. Only one of these should be provided.
    
    '''
    config = self._process_config
    new_value = value
    gs_object_name = new_value.gs_object_name
    new_gs_object_name = new_value.gs_object_name
    if config.get('copy'):
      new_value = copy.deepcopy(value)
      new_gs_object_name = '%s_%s' % (new_value.gs_object_name, config.get('copy_name'))
    blob_key = None
    # We assume that self._process_config has at least either 'copy' or 'transform' keys!
    if config.pop('measure', True):
      if new_value.proportion is None:
        pause = 0.5
        for i in xrange(4):
          try:
            fetch_image = urlfetch.fetch('%s=s100' % new_value.serving_url)
            break
          except Exception as e:
            time.sleep(pause)
            pause = pause * 2
        image = images.Image(image_data=fetch_image.content)
        new_value.proportion = float(image.width) / float(image.height)
        del fetch_image, image
    if len(config):
      # @note No try block is implemented here. This code is no longer forgiving.
      # If any of the images fail to process, everything is lost/reverted, because one or more images:
      # - are no longer existant in the cloudstorage / .read();
      # - are not valid / not image exception;
      # - failed to resize / resize could not be done;
      # - failed to create gs key / blobstore failed for some reason;
      # - failed to create get_serving_url / serving url service failed for some reason;
      # - failed to write to cloudstorage / cloudstorage failed for some reason.
      readonly_blob = cloudstorage.open(gs_object_name[3:], 'r')
      blob = readonly_blob.read()
      readonly_blob.close()
      image = images.Image(image_data=blob)
      if config.get('transform'):
        image.resize(config.get('width'),
                     config.get('height'),
                     crop_to_fit=config.get('crop_to_fit', False),
                     crop_offset_x=config.get('crop_offset_x', 0.0),
                     crop_offset_y=config.get('crop_offset_y', 0.0))
        blob = image.execute_transforms(output_encoding=image.format)
      new_value.proportion = float(image.width) / float(image.height)
      new_value.size = len(blob)
      writable_blob = cloudstorage.open(new_gs_object_name[3:], 'w')
      writable_blob.write(blob)
      writable_blob.close()
      if gs_object_name != new_gs_object_name or new_value.serving_url is None:
        new_value.gs_object_name = new_gs_object_name
        blob_key = blobstore.create_gs_key(new_gs_object_name)
        new_value.image = blobstore.BlobKey(blob_key)
        new_value.serving_url = images.get_serving_url(new_value.image)
        self.save_blobs_on_success(new_value.image)
    return new_value
  
  def argument_format(self, value):
    if not self._argument_format_upload:
      return super(_BaseImageProperty, self).argument_format(value)
    value = self._property_value_format(value)
    if value is Nonexistent:
      return value
    if not self._repeated:
      value = [value]
    out = []
    for i, v in enumerate(value):
      if not isinstance(v, cgi.FieldStorage) and not self._required:
        return Nonexistent  # If the field is not required, and it's not an actual upload, immediately return Nonexistent.
      # These will throw errors if the 'v' is not cgi.FileStorage and it does not have compatible blob-key.
      file_info = blobstore.parse_file_info(v)
      blob_info = blobstore.parse_blob_info(v)
      meta_required = ('image/jpeg', 'image/jpg', 'image/png')  # We only accept jpg/png. This list can be and should be customizable on the property option itself?
      if file_info.content_type not in meta_required:
        raise orm.PropertyError('invalid_image_type')  # First line of validation based on meta data from client.
      new_image = self.get_modelclass()(**{'size': file_info.size,
                                           'content_type': file_info.content_type,
                                           'gs_object_name': file_info.gs_object_name,
                                           'image': blob_info.key(),
                                           '_sequence': i,
                                           'serving_url': images.get_serving_url(blob_info.key())})
      self.save_blobs_on_success(new_image.image)
      if self._process:
        new_image = self.process(new_image)
      out.append(new_image)
    if not self._repeated:
      out = out[0]
    return out


class SuperImageStorageStructuredProperty(_BaseImageProperty, orm.SuperStorageStructuredProperty):
  pass


class SuperImageLocalStructuredProperty(_BaseImageProperty, orm.SuperLocalStructuredProperty):
  pass


class SuperImageStructuredProperty(_BaseImageProperty, orm.SuperStructuredProperty):
  pass
