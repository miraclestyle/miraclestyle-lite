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
from app.tools.base import blob_alter_image

class BlobKeyManager():
  '''
    Example usage:
    
    new_file = gcs.open(...)
    new_file.write(..)
    new_file.close()
    
    new_blobstore_key = blobstore.create_gs_key(gs_object_name=new_file.gs_object_name)
    BlobKeyManager.collect_on_success(new_blobstore_key) 
     
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
  def collector(cls):
    # this function acts as a getter from in-memory storage
    out = memcache.temp_memory_get(settings.BLOBKEYMANAGER_KEY, None)
    if out is None:
      memcache.temp_memory_set(settings.BLOBKEYMANAGER_KEY, {'delete' : []})
    out = memcache.temp_memory_get(settings.BLOBKEYMANAGER_KEY)
    return out
 
  @classmethod
  def normalize(cls, key_or_keys):
    # helper to transform single item into a list for iteration
    if isinstance(key_or_keys, (list, tuple)):
      return key_or_keys
    else:
      return [key_or_keys]
    
  @classmethod
  def delete(cls, keys):
    # this method will delete list of provided blob keys no matter which state
    # but depending on methods called later on in the code will determine which are to be deleted for real
    cls._store(keys, 'delete')
    
  @classmethod
  def delete_on_error(cls, keys, delete=True):
    # marks keys to be deleted upon application error
    cls._store(keys, 'delete_error', delete)
  
  @classmethod
  def delete_on_success(cls, keys, delete=True):
    # marks keys to be deleted upon success
    cls._store(keys, 'delete_success', delete)
  
  @classmethod
  def collect(cls, keys, delete=True):
    # collect keys no matter what happens
    cls._store(keys, 'collect', delete)
  
  @classmethod
  def collect_on_success(cls, keys, delete=True):
    # collect keys on success
    cls._store(keys, 'collect_success', delete)
  
  @classmethod
  def collect_on_error(cls, keys, delete=True):
    # collect keys on application error
    cls._store(keys, 'collect_error', delete)
    
  @classmethod
  def _store(cls, keys, state=None, delete=True):
    keys = cls.normalize(keys)
    collector = cls.collector()
    for key in keys:
      if state not in collector:
        collector[state] = []
      if key not in collector[state]:
        collector[state].append(key)
    if state is not None and not state.startswith('delete') and delete is True: 
      # if state is said to be delete_* or delete then there is no need to store them in delete queue
      cls._store(keys, 'delete')
 
def validate_images(objects):
  '''"objects" argument is a list of valid instance(s)
  of Image class that require validation!
  
  This function is used mainly for property that turns its usage on.
  
  '''
  to_delete = []
  for obj in objects:
    if obj.width or obj.height: # validate images will not perform any measurements if image already has defined width and height.
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
      if o.image:
        BlobKeyManager.delete(o.image) # ensure that this gets deleted since we catch the exception above
      objects.remove(o)
    cloudstorage_file.close()
    obj.populate(**{'width': width,
                    'height': height})
  
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

class SuperStructuredPropertyImageManager(ndb.SuperStructuredPropertyManager):
  
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
            BlobKeyManager.delete_on_success(entity.image)
          else:
            BlobKeyManager.collect_on_success(entity.image, False)
        
  def _pre_update_local(self):
    self._process_blobs()
    super(SuperStructuredPropertyImageManager, self)._pre_update_local() # finalize delete mode
 
  def _delete_remote(self):
    # this function had to be copied because it queries information, and it never saves its entities in memory
    # delete_remote is used by both multi and multi_sequenced
    cursor = Cursor()
    limit = 200
    query = self._property._modelclass.query(ancestor=self._entity.key)
    while True:
      _entities, cursor, more = query.fetch_page(limit, start_cursor=cursor)
      if len(_entities):
        for entity in _entities:
          self._copy_record_arguments(entity)
        self._process_blobs(_entities, True) # this will force-mark ALL blobs for delete that are attached to the entities
        ndb.delete_multi(_entities)
        if not cursor or not more:
          break
      else:
        break
  
  def _delete_remote_single(self):
    # same happens with remote_single
    # we must copy over the code because delete_single singlehandedly removes entity.
    property_value_key = ndb.Key(self._property._modelclass.get_kind(), self._entity.key_id_str, parent=self._entity.key)
    entity = property_value_key.get()
    self._copy_record_arguments(entity)
    self._process_blobs(entity, True) # this will mark ALL blobs for delete
    entity.key.delete()
   
  # we override these three methods because we call self._process_blobs() beforehand
  # this could be avoided by overriding def post_update() but we need to decide which is better approach
  def _post_update_remote_single(self):
    self._process_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_single()
  
  def _post_update_remote_multi(self):
    self._process_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_multi()
  
  def _post_update_remote_multi_sequenced(self):
    self._process_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_multi_sequenced()
  
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
    modified_entities, blob_keys_to_delete = blob_alter_image(entities, alter_image_config)
    setattr(self._entity, self.property_name, modified_entities)  # Comply with expando and virtual fields.
    # delete blob keys that were ordered to be deleted
    # blobs must be deleted on full success
    BlobKeyManager.delete_on_success(blob_keys_to_delete)
    
     
  
class _BaseImageProperty(object):

  def __init__(self, *args, **kwargs):
    self._validate_images = kwargs.pop('validate_images', None)
    self._alter_image_config = kwargs.pop('alter_image_config', None)
    super(_BaseImageProperty, self).__init__(*args, **kwargs)
    self._managerclass = SuperStructuredPropertyImageManager
  
  def format(self, value):
    prop = self
    value = ndb._property_value_format(prop, value)
    if prop._repeated:
      blobs = value
    else:
      blobs = [value]
    out = []
    for blob in blobs:
      if not isinstance(blob, cgi.FieldStorage) and not prop._required: # if the prop is not required pass it
        continue
      # These will throw errors if the 'blob' is not cgi.FileStorage.
      file_info = blobstore.parse_file_info(blob)
      blob_info = blobstore.parse_blob_info(blob)
      meta_required = ('image/jpeg', 'image/jpg', 'image/png') # we only accept jpg/png
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

class SuperEntityStorageStructuredImageProperty(_BaseImageProperty, ndb.SuperEntityStorageStructuredProperty):
  pass

class SuperLocalStructuredImageProperty(_BaseImageProperty, ndb.SuperLocalStructuredProperty):
  pass

class SuperStructuredImageProperty(_BaseImageProperty, ndb.SuperStructuredProperty):
  pass
  

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
