# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import cgi
import cloudstorage
import copy

from google.appengine.ext import blobstore
from google.appengine.api import images, urlfetch
from google.appengine.datastore.datastore_query import Cursor

from app import orm, mem, settings
from app.util import *


# @see https://developers.google.com/appengine/docs/python/googlecloudstorageclient/retryparams_class
default_retry_params = cloudstorage.RetryParams(initial_delay=0.2, max_delay=5.0, backoff_factor=2,
                                                max_retries=5, max_retry_period=60, urlfetch_timeout=30)
cloudstorage.set_default_retry_params(default_retry_params)


##########################################
########## Extra system models! ##########
##########################################


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


#########################################################
########## Superior properties implementation! ##########
#########################################################


class _ImagePropertyValue(object):
  
  def _update_blobs(self):
    if self.has_value():
      if self._property._repeated:
        entities = self._property_value
      else:
        entities = [self._property_value]
      for entity in entities:
        if (entity._state == 'deleted'):
          self._property.delete_blobs_on_success(entity.image)
        else:
          self._property.save_blobs_on_success(entity.image, False)
      if hasattr(self._entity, '_original'):
        original_entities = getattr(self._entity._original, self.property_name, None)
        if original_entities is not None:
          original_entities = original_entities.value
          if not self._property._repeated:
            if entities[0] is not None and original_entities is not None and entities[0].image != original_entities.image:
              self._property.delete_blobs_on_success(original_entities.image)
          else:
            tmp = dict((ent.key.urlsafe(), ent) for ent in entities if ent.key)
            if original_entities is not None:
              for original in original_entities:
                entity = tmp.get(original.key.urlsafe())
                if entity is not None:
                  if entity.image != original.image:
                    self._property.delete_blobs_on_success(original.image)
  
  def duplicate(self):
    '''Override duplicate. Parent duplicate method will retrieve all data into self._property_value, and later on,
    here we can finalize duplicate by copying the blob.
    '''
    super(_ImagePropertyValue, self).duplicate()
    @orm.tasklet
    def async(entity):
      gs_object_name = entity.gs_object_name
      try:
        gs_object_name = entity.parse_duplicate_appendix(gs_object_name)
      except IndexError:
        pass
      new_gs_object_name = '%s_duplicate_%s' % (gs_object_name, entity.duplicate_appendix)
      readonly_blob = cloudstorage.open(gs_object_name[3:], 'r')
      writable_blob = cloudstorage.open(new_gs_object_name[3:], 'w', content_type=entity.content_type)
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
      blob_key = yield blobstore.create_gs_key_async(new_gs_object_name)
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
    if self.has_value():
      processed_value = self._property.process(self.value)
      setattr(self._entity, self.property_name, processed_value)


class LocalStructuredImagePropertyValue(_ImagePropertyValue, orm.LocalStructuredPropertyValue):
  
  def pre_update(self):
    self._update_blobs()
    super(LocalStructuredImagePropertyValue, self).pre_update()


class RemoteStructuredImagePropertyValue(_ImagePropertyValue, orm.RemoteStructuredPropertyValue):
  
  def post_update(self):
    self._update_blobs()
    super(RemoteStructuredImagePropertyValue, self).post_update()
  
  def _delete_single(self):
    self.read()
    self._property.delete_blobs_on_success(self._property_value.image)
    self._property_value.key.delete()
  
  def _delete_repeated(self):
    cursor = Cursor()
    limit = 200
    query = self._property.get_modelclass().query(ancestor=self._entity.key)
    while True:
      _entities, cursor, more = query.fetch_page(limit, start_cursor=cursor)
      if len(_entities):
        self._set_parent(_entities)
        for entity in _entities:
          self._property.delete_blobs_on_success(entity.image)
        orm.delete_multi([entity.key for entity in _entities])
        if not cursor or not more:
          break
      else:
        break


orm.PROPERTY_VALUES.extend((LocalStructuredImagePropertyValue, RemoteStructuredImagePropertyValue))


class _BaseBlobProperty(object):
  '''Base helper class for blob-key-like orm properties.
  This property should be used in conjunction with orm Property baseclass, like so:
  class PDF(BaseBlobKeyInterface, orm.Property):
  ....
  def value_format(self, value):
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
    self._process_config = kwargs.pop('process_config', {})
    super(_BaseImageProperty, self).__init__(*args, **kwargs)
  
  def generate_serving_urls(self, values):
    @orm.tasklet
    def generate(value):
      if value.serving_url is None:
        value.serving_url = yield images.get_serving_url_async(value.image)
      raise orm.Return(True)
    
    @orm.tasklet
    def mapper(values):
      yield map(generate, values)
      raise orm.Return(True)
    
    mapper(values).get_result()
  
  def generate_measurements(self, values):
    ctx = orm.get_context()
    @orm.tasklet
    def measure(value):
      if value.proportion is None:
        pause = 0.5
        for i in xrange(4):
          try:
            fetched_image = yield ctx.urlfetch('%s=s100' % value.serving_url)  # http://stackoverflow.com/q/14944317/376238
            break
          except Exception as e:
            time.sleep(pause)
            pause = pause * 2
        image = images.Image(image_data=fetched_image.content)
        value.proportion = float(image.width) / float(image.height)
        raise orm.Return(True)
    
    @orm.tasklet
    def mapper(values):
      yield map(measure, values)
      raise orm.Return(True)
    
    mapper(values).get_result()
  
  def process(self, values):
    ''' @note
    This method is primarily used for images' transformation and copying.
    '''
    @orm.tasklet
    def process_image(value, i, values):
      config = self._process_config
      new_value = value
      gs_object_name = new_value.gs_object_name
      new_gs_object_name = new_value.gs_object_name
      if config.get('copy'):
        new_value = copy.deepcopy(value)
        new_gs_object_name = '%s_%s' % (new_value.gs_object_name, config.get('copy_name'))
      blob_key = None
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
        blob = yield image.execute_transforms_async(output_encoding=image.format)
      new_value.proportion = float(image.width) / float(image.height)
      new_value.size = len(blob)
      writable_blob = cloudstorage.open(new_gs_object_name[3:], 'w', content_type=new_value.content_type)
      writable_blob.write(blob)
      writable_blob.close()
      if gs_object_name != new_gs_object_name:
        new_value.gs_object_name = new_gs_object_name
        blob_key = yield blobstore.create_gs_key_async(new_gs_object_name)
        new_value.image = blobstore.BlobKey(blob_key)
        new_value.serving_url = None
      values[i] = new_value
      raise orm.Return(True)
    
    @orm.tasklet
    def mapper(values):
      for i, v in enumerate(values):
        yield process_image(v, i, values)
      raise orm.Return(True)
    
    single = False
    if not isinstance(values, list):
      values = [values]
      single = True
    mapper(values).get_result()
    self.generate_serving_urls(values)
    if single:
      values = values[0]
    return values
  
  def value_format(self, value):
    if (self._repeated and (not len(value) or not isinstance(value[0], cgi.FieldStorage))) or (not self._repeated and not isinstance(value, cgi.FieldStorage)):
      return super(_BaseImageProperty, self).value_format(value)
    value = self._property_value_format(value)
    if value is Nonexistent:
      return value
    if not self._repeated:
      value = [value]
    out = []
    for i, v in enumerate(value):
      if isinstance(v, dict):
        out.append(self._structured_property_format(v))
      else:
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
                                             '_sequence': i})
        out.append(new_image)
    if self._process_config.get('transform') or self._process_config.get('copy'):
      self.process(out)
    else:
      self.generate_serving_urls(out)
      if self._process_config.get('measure', True):
        self.generate_measurements(out)
    map(lambda x: self.save_blobs_on_success(x.image), out)
    if not self._repeated:
      out = out[0]
    return out


class SuperImageRemoteStructuredProperty(_BaseImageProperty, orm.SuperRemoteStructuredProperty):
  
  _value_class = RemoteStructuredImagePropertyValue


class SuperImageLocalStructuredProperty(_BaseImageProperty, orm.SuperLocalStructuredProperty):
  
  _value_class = LocalStructuredImagePropertyValue


class SuperImageStructuredProperty(_BaseImageProperty, orm.SuperStructuredProperty):
  
  _value_class = LocalStructuredImagePropertyValue
