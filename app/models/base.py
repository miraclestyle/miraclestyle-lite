# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import cgi
import cloudstorage

from google.appengine.ext import blobstore
from google.appengine.api import images
from google.appengine.datastore.datastore_query import Cursor

from app import ndb, memcache, settings
from app.tools.manipulator import set_attr, get_attr, safe_eval


class Image(ndb.BaseModel):
  
  _kind = 69
  
  image = ndb.SuperBlobKeyProperty('1', required=True, indexed=False)
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


class SuperStructuredPropertyImageManager(ndb.SuperStructuredPropertyManager):
  
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
  
  def _pre_update_local(self):
    self._update_blobs()
    super(SuperStructuredPropertyImageManager, self)._pre_update_local()
  
  def _post_update_remote_single(self):
    self._update_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_single()
  
  def _post_update_remote_multi(self):
    self._update_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_multi()
  
  def _post_update_remote_multi_sequenced(self):
    self._update_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_multi_sequenced()
  
  def _delete_remote(self):
    cursor = Cursor()
    limit = 200
    query = self._property._modelclass.query(ancestor=self._entity.key)
    while True:
      _entities, cursor, more = query.fetch_page(limit, start_cursor=cursor)
      if len(_entities):
        for entity in _entities:
          self._copy_record_arguments(entity)
          self._property.delete_blobs_on_success(entity.image)
        delete_multi([entity.key for entity in _entities])
        if not cursor or not more:
          break
      else:
        break
  
  def _delete_remote_single(self):
    property_value_key = ndb.Key(self._property._modelclass.get_kind(), self._entity.key_id_str, parent=self._entity.key)
    entity = property_value_key.get()
    self._copy_record_arguments(entity)
    self._property.delete_blobs_on_success(entity.image)
    entity.key.delete()
  
  def process(self):
    '''This function should be called inside a taskqueue.
    It will perform all needed operations based on the property configuration on how to handle its blobs.
    Resizing, cropping, and generation of serving url in the end.
      
      Idempotency overhead in this one is the crop, resize and similar "modify-image" features
      might be called many times on same entity (and its gcs file), which in turn would resize the same image multiple times.
      
      This cant be avoided when transactions or general failures of app engine come into play, here is the example:
      
      try:
       entity.images.process()
      except:
       transaction_rollback()
       
      So the google cloud storage files might be already modified 
      and the entity was reverted to previous state, so in next retry of taskqueue it will retry to do the same
      thing on the entities.
      
      As for the copying process, we always wipe out the image upon code failure, so stacking of copied data wont happen.
      
      !!NOTE: Single entity storage can be problematic in this case because single entity structure is usually:
      
      class Single:
      
        images = ndb.SuperStructuredPropertyImageManager(...)
        
      so in that case you would have to call
      
      entity.image.value.images.process()
      
      because if you call entity.image.process() it wont do nothing, basically because `image` property on which .process() 
      was called is just instance of SuperStructuredPropertyImageManager, and its property value is instance of entity 
      that would usually contain property that is repeated list of images.
      
      @todo: We could however solve this by iterating over every entity field and calling .process() if its instance of SuperStructuredPropertyImageManager?
      like this
      for field in entity.fields:
        if field instance of storage_image_entity:
         entity[field].process()
    '''
    if not self.has_value():
      raise ndb.PropertyError('Cannot call %s.process() because read() was not called beforehand.' % self)
    if self._property._repeated:
      processed_entities = []
      for entity in self.value:
        processed_entity = self._property.process(entity)
        if processed_entity is not None:
          processed_entities.append(processed_entity)
      setattr(self._entity, self.property_name, processed_entities)
    else:
      processed_entity = self._property.process(self.value)
      if processed_entity is not None:
        setattr(self._entity, self.property_name, processed_entity)


class _BaseBlobProperty(object):
  '''Base helper class for blob-key-like ndb properties.
  This property should be used in conjunction with ndb Property baseclass, like so:
  class PDF(BaseBlobKeyInterface, ndb.Property):
  ....
  def format(self, value):
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
    blobs = memcache.temp_memory_get(settings.BLOBKEYMANAGER_KEY, None)
    if blobs is None:
      memcache.temp_memory_set(settings.BLOBKEYMANAGER_KEY, {'delete': []})
    blobs = memcache.temp_memory_get(settings.BLOBKEYMANAGER_KEY)
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
    # This method will delete list of provided blob keys no matter which state
    # but depending on methods called later on in the code will determine which are to be deleted for real.
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


class _BaseImageProperty(object):
  '''Base helper class for image-like properties.
  This class should work in conjunction with ndb.Property, because it does not implement anything of ndb.
  Example:
  class NewImageProperty(_BaseImageProperty, ndb.Property):
  ...
  
  '''
  def __init__(self, *args, **kwargs):
    self._process = kwargs.pop('process', None)
    self._process_config = kwargs.pop('process_config', {})
    super(_BaseImageProperty, self).__init__(*args, **kwargs)
    self._managerclass = SuperStructuredPropertyImageManager
  
  # This method is not utilising yield images.get_serving_url_async technique for obtaining serving urls for image!
  # It requires further refinement, and if possible should deprecate _blob_alter_image and measure_and_validate!
  def process(self, value):
    if value and hasattr(value, 'image') and isinstance(value.image, blobstore.BlobKey):
      new_value = value
      gs_object_name = new_value.gs_object_name
      new_gs_object_name = new_value.gs_object_name
      if self._process_config('copy'):
        new_value = copy.deepcopy(value)
        new_gs_object_name = '%s_%s' % (new_value.gs_object_name, self._process_config('copy_name'))
      blob_key = None
      if len(self._process_config) or not new_value.width or not new_value.height:  # We assume that self._process_config has at least either 'copy' or 'transform' keys!
        try:
          readonly_blob = cloudstorage.open(gs_object_name[3:], 'r')
          blob = readonly_blob.read()
          readonly_blob.close()
          writable_blob = cloudstorage.open(new_gs_object_name[3:], 'w')
          image = images.Image(image_data=blob)
          if self._process_config('transform'):
            image.resize(self._process_config('width'),
                         self._process_config('height'),
                         crop_to_fit=self._process_config('crop_to_fit'),
                         crop_offset_x=self._process_config('crop_offset_x'),
                         crop_offset_y=self._process_config('crop_offset_y'))
            blob = image.execute_transforms(output_encoding=image.format)
          new_value.width = image.width
          new_value.height = image.height
          new_value.size = len(blob)
          if len(self._process_config):
            writable_blob.write(blob)  # @todo Not sure if this is ok!?
          writable_blob.close()
          if gs_object_name != new_gs_object_name or new_value.serving_url is None:
            new_value.gs_object_name = new_gs_object_name
            blob_key = blobstore.create_gs_key(new_gs_object_name)
            new_value.image = blobstore.BlobKey(blob_key)
            new_value.serving_url = images.get_serving_url(new_value.image)
          return new_value
        except Exception as e:
          util.logger(e, 'exception')
          if blob_key != None:
            self.delete_blobs(blob_key)
          elif new_value.image:
            self.delete_blobs(new_value.image)
          raise ndb.PropertyError('processing_image_failed')
      return new_value
    else:
      raise ndb.PropertyError('not_image')
  
  # This method remains here for reference!
  def _blob_alter_image(self, value):
    result = {}
    if original_image and hasattr(original_image, 'image') and isinstance(original_image.image, blobstore.BlobKey):
      new_image = original_image # we cannot use deep copy here because it should mutate on entity.itself
      original_gs_object_name = new_image.gs_object_name
      new_gs_object_name = new_image.gs_object_name
      if make_copy:
        new_image = copy.deepcopy(original_image) # deep copy is fine when we want copies of it
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
        elif new_image.image:
          result['delete'] = new_image.image
      else:
        result['save'] = new_image
    return result
  
  # This method remains here for reference!
  def measure_and_validate(self, values):
    '''"values" argument is a list of valid instance(s) of Image class that require validation!
    This function is used mainly for property that turns its usage on.
    
    '''
    delete_values = []
    for value in values:
      if value.width or value.height:  # measure_and_validate will not perform any measurements if image already has defined width and height.
        continue
      cloudstorage_file = cloudstorage.open(filename=value.gs_object_name[3:])
      # This will throw an error if the file does not exist in cloudstorage.
      image_data = cloudstorage_file.read()
      # This will throw an error if the file is not an image, or is corrupted.
      try:
        image = images.Image(image_data=image_data)
        width = image.width  # This property causes _update_dimensions function that might fail to read the image if image meta-data is corrupted, indicating it's not good.
        height = image.height
        value.populate(**{'width': width, 'height': height})
      except images.NotImageError as e:
        # Cannot do values.remove while in for loop values.
        delete_values.append(value)
      cloudstorage_file.close()
    for value in delete_values:
      if value.image:
        self.delete_blobs(value.image)
      values.remove(value)
    
    @ndb.tasklet
    def async(value):
      if value.serving_url is None:
        value.serving_url = yield images.get_serving_url_async(value.image)
      raise ndb.Return(value)
    
    @ndb.tasklet
    def mapper(values):
      results = yield map(async, values)
      raise ndb.Return(results)
    
    return mapper(values).get_result()
  
  def format(self, value):
    value = self._property_value_format(value)
    if not self._repeated:
      value = [value]
    out = []
    for v in value:
      if not isinstance(v, cgi.FieldStorage) and not self._required:  # If the prop is not required, skip it.
        continue
      # These will throw errors if the 'v' is not cgi.FileStorage.
      file_info = blobstore.parse_file_info(v)
      blob_info = blobstore.parse_blob_info(v)
      meta_required = ('image/jpeg', 'image/jpg', 'image/png')  # We only accept jpg/png!
      if file_info.content_type not in meta_required:
        raise ndb.PropertyError('invalid_image_type')  # First line of validation based on meta data from client.
      new_image = self._modelclass(**{'size': file_info.size,
                                      'content_type': file_info.content_type,
                                      'gs_object_name': file_info.gs_object_name,
                                      'image': blob_info.key()})
      if self._process:
        new_image = self.process(new_image)
      out.append(new_image)
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out


class SuperImageStorageStructuredProperty(_BaseBlobProperty, _BaseImageProperty, ndb._BaseProperty, ndb.SuperStorageStructuredProperty):
  pass


class SuperImageLocalStructuredProperty(_BaseBlobProperty, _BaseImageProperty, ndb._BaseProperty, ndb.SuperLocalStructuredProperty):
  pass


class SuperImageStructuredProperty(_BaseBlobProperty, _BaseImageProperty, ndb._BaseProperty, ndb.SuperStructuredProperty):
  pass
