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
  
  def _pre_update_local(self):
    self._process_blobs()
    super(SuperStructuredPropertyImageManager, self)._pre_update_local()
  
  # This could be avoided by overriding def post_update() however, we need to decide which is better approach.
  def _post_update_remote_single(self):
    self._process_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_single()
  
  def _post_update_remote_multi(self):
    self._process_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_multi()
  
  def _post_update_remote_multi_sequenced(self):
    self._process_blobs()
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
        self._process_blobs(_entities, True)  # This will force/mark ALL blobs for deletion that are attached to the entities.
        delete_multi([entity.key for entity in _entities])
        if not cursor or not more:
          break
      else:
        break
  
  def _delete_remote_single(self):
    property_value_key = ndb.Key(self._property._modelclass.get_kind(), self._entity.key_id_str, parent=self._entity.key)
    entity = property_value_key.get()
    self._copy_record_arguments(entity)
    self._process_blobs(entity, True) # This will mark ALL blobs for deletion.
    entity.key.delete()
  
  def _blob_alter_image(self, original_image, make_copy=False, copy_name=None, transform=False, width=0, height=0, crop_to_fit=False, crop_offset_x=0.0, crop_offset_y=0.0):
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
  
  def _process_blobs(self, entities=None, forced=False):
    # this function is helper that will decide which every entity.image blob key needs to be marked for deletation
    # if `entities` is not provided it will attempt to read from self._property_value
    # otherwise nothing will happen because no value is provided @see self.has_value()
    # this function will also mark the entity.image to be preserved by calling BlobKeyManager.collect_on_success(entity.image, False)
    # that means it will first check if blob key was previously marked for deletation 
    # (this way we know that's a new blob key)
    if not entities:
      if self.has_value():
        if self._property._repeated:
          entities = self._property_value
        else:
          entities = [self._property_value]
    else:
      if not isinstance(entities, (list, tuple)):
        entities = [entities]
    if entities:
      for entity in entities:
        # it is important that entity.image exists and 
        # that the state == 'deleted'
        # if force=True is specified, it will call delete no matter what the state is
        if hasattr(entity, 'image') and entity.image and isinstance(entity.image, blobstore.BlobKey): 
          # this ifs above are because single entity storage structure can differ
          if (entity._state == 'deleted' or forced):
            self._property.blob_delete_on_success(entity.image)
          else:
            self._property.blob_collect_on_success(entity.image, False)
  
  def process(self):
    '''
      This function should be called inside a taskqueue.
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
    alter_image_config = self._property._alter_image_config
    if not alter_image_config:
      alter_image_config = {}
    if not self.has_value():
      raise ndb.PropertyError('Cannot call %s.process() because read() was not called beforehand.' % self)
    entities = self.value
    if not self._property._repeated:
      entities = [entities]
    # we do not use validate_images here because we can validate it and measure it in blob_alter_image instead
    write_entities = []
    blob_delete = []
    for entity in entities:
      if entity and hasattr(entity, 'image') and isinstance(entity.image, blobstore.BlobKey):
        result = self._blob_alter_image(entity, **config)
        if result.get('save'):
          write_entities.append(result['save'])
        if result.get('delete'):
          blob_delete.append(result['delete'])
    modified_entities, blob_keys_to_delete = blob_alter_image(entities, alter_image_config)
    if 
    setattr(self._entity, self.property_name, modified_entities)  # Comply with expando and virtual fields.
    # delete blob keys that were ordered to be deleted
    # blobs must be deleted on full success
    self._property.blob_delete_on_success(blob_keys_to_delete)

def blob_alter_image(entities, config):
  if entities and isinstance(entities, list):
    write_entities = []
    blob_delete= []
    for entity in entities:
      if entity and hasattr(entity, 'image') and isinstance(entity.image, blobstore.BlobKey):
        result = _blob_alter_image(entity, **config)
        if result.get('save'):
          write_entities.append(result['save'])
        if result.get('delete'):
          blob_delete.append(result['delete'])
    return (write_entities, blob_delete)

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
    self._measure_and_validate = kwargs.pop('measure_and_validate', None)
    self._alter_image_config = kwargs.pop('alter_image_config', {})
    super(_BaseImageProperty, self).__init__(*args, **kwargs)
    self._managerclass = SuperStructuredPropertyImageManager
  
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
        self.blob_delete(value.image)  # Ensure that this gets deleted since we catch the exception above
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
      out.append(self._modelclass(**{'size': file_info.size,
                                     'content_type': file_info.content_type,
                                     'gs_object_name': file_info.gs_object_name,
                                     'image': blob_info.key()}))
    if self._measure_and_validate:
      out = self.measure_and_validate(out)
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
