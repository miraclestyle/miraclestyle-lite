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
  '''
  
  @classmethod
  @property
  def collector(cls):
    out = memcache.temp_memory_get(settings.TEMP_MEMORY_BLOBKEYMANAGER_KEY, None)
    if out is None:
      memcache.temp_memory_set(settings.TEMP_MEMORY_BLOBKEYMANAGER_KEY, {})
    return memcache.temp_memory_get(settings.TEMP_MEMORY_BLOBKEYMANAGER_KEY)
 
  @classmethod
  def normalize(cls, key_or_keys):
    if isinstance(key_or_keys, (list, tuple)):
      return key_or_keys
    else:
      return [key_or_keys]
    
  @classmethod
  def _delete(cls, phase, keys):
    # by default, collector has two stages
    # 'success' and 'finally'
    # in success he will either, set blobs that need to be deleted on success
    # or keep alive the blobs
    keys = cls.normalize(keys)
    for key in keys:
      if phase not in cls.collector:
        cls.collector[phase] = []
      if key not in cls.collector[phase]:
        cls.collector[phase].append(key)
      
  @classmethod
  def _collect(cls, phase, keys):
    phase = 'collector_%s' % phase
    keys = cls.normalize(keys)
    for key in keys:
      if phase not in cls.collector:
        cls.collector[phase] = []
      if key not in cls.collector[phase]:
        cls.collector[phase].append(key)
        
  @classmethod
  def collect(cls, keys):
    # this will ALWAYS save the targeted blobs
    cls._collect('finally', keys)
  
  @classmethod
  def collect_on_success(cls, keys):
    # this will DELETE the blobs upon ERROR and save them upon success
    cls._collect('success', keys)
    # it will delete them if the success phase fails
    cls.delete(keys)
  
  @classmethod
  def delete(cls, keys):
    # deletes them always
    cls._delete('finally', keys)
  
  @classmethod
  def delete_on_success(cls, keys):
    # deletes them only if the success
    cls._delete('success', keys)
 
 
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
  
  def _delete_possible_blobs(self, entities=None, forced=False):
    # this function is helper that will mark every suitable entities `image` blob key for deletation
    # if entities is not provided it will attempt to read from self._property_value
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
        if (entity._state == 'deleted' or forced) and entity.image:
          BlobKeyManager.delete_on_success(entity.image)
        
  def _pre_update_local(self):
    self._delete_possible_blobs()
    super(SuperStructuredPropertyImageManager, self)._pre_update_local() # finalize delete mode
 
  def _delete_remote(self):
    # this function had to be copied because it queries information, and it never saves its entities in memory
    # this could be improved however this is most efficient right now
    cursor = Cursor()
    limit = 200
    query = self._property._modelclass.query(ancestor=self._entity.key)
    while True:
      _entities, cursor, more = query.fetch_page(limit, start_cursor=cursor)
      if len(_entities):
        for entity in _entities:
          self._copy_record_arguments(entity)
        self._delete_possible_blobs(_entities, True) # this will mark ALL blobs for delete that are attached to the entities
        ndb.delete_multi(_entities)
        if not cursor or not more:
          break
      else:
        break
  
  def _delete_remote_single(self):
    property_value_key = ndb.Key(self._property._modelclass.get_kind(), self._entity.key_id_str, parent=self._entity.key)
    entity = property_value_key.get()
    self._copy_record_arguments(entity)
    self._delete_possible_blobs(entity, True) # this will mark ALL blobs for delete
    entity.key.delete()
    
  def _post_update_remote_single(self):
    self._delete_possible_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_single()
  
  def _post_update_remote_multi(self):
    self._delete_possible_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_multi()
  
  def _post_update_remote_multi_sequenced(self):
    self._delete_possible_blobs()
    super(SuperStructuredPropertyImageManager, self)._post_update_remote_multi_sequenced()
  
  def process(self):
    '''
      This function should be called inside a taskqueue.
      It will perform all needed operations based on the property configuration on how to handle its blobs.
      Resizing, cropping, and generation of serving url in the end.
    '''
     
  
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
