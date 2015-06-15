# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.ndb.model import _BaseValue

from .base import *
from .base import _BaseImageProperty

__all__ = ['PropertyValue', 'StructuredPropertyValue', 'ReferencePropertyValue',
           'LocalStructuredPropertyValue', 'ReferenceStructuredPropertyValue',
           '_ImagePropertyValue', 'RemoteStructuredPropertyValue',
           'RemoteStructuredImagePropertyValue', 'LocalStructuredImagePropertyValue']


class PropertyValue(object):

  def __init__(self, property_instance, entity, **kwds):
    self._property = property_instance
    self._entity = entity
    self._kwds = kwds
    self._property_value_options = {}

  def __repr__(self):
    return '%s(entity=instance of %s, property=%s, property_value=%s, kwds=%s)' % (self.__class__.__name__,
                                                                                   self._entity.__class__.__name__,
                                                                                   self._property.__class__.__name__,
                                                                                   self.value, self._kwds)

  @property
  def property_name(self):
    # Retrieves code name of the field for setattr usage. If _code_name is not available it will use _name
    name = self._property._code_name
    if not name:
      name = self._property._name
    return name

  @property
  def value_options(self):
    ''''_property_value_options' is used for storing and returning information that
    is related to property value(s). For exmaple: 'more' or 'cursor' parameter in querying.
    '''
    return self._property_value_options

  def has_value(self):
    return hasattr(self, '_property_value')

  @property
  def value(self):
    return getattr(self, '_property_value', None)

  @property
  def read_value(self):
    # read value is used mainly for def get_output() because it will output whatever the client instructed it to read
    # by default the read_value will return self.value, which in most of the cases is the case
    return self.value

  def get_output(self):
    return self.read_value


class StructuredPropertyValue(PropertyValue):

  def _set_parent(self, entities=None):
    '''This function should be called whenever a new entity is instanced / retrieved inside a root entity.
    It either accepts entities, or it will use self.value to iterate.
    Its purpose is to maintain hierarchy like so:
    catalog._parent = None # its root
     product._parent = catalog
       product_instance._parent = product
         product_instance.contents[0]._parent = product_instance
         ....
    So based on that, you can always reach for the top by simply finding which ._parent is None.
    '''
    as_list = False
    if entities is None:
      entities = self.value
      as_list = self._property._repeated
    else:
      as_list = isinstance(entities, list)
    if entities is not None:
      if as_list:
        for entity in entities:
          if entity._parent is None:
            entity._parent = self._entity
          else:
            continue
      else:
        if entities._parent is None:
          entities._parent = self._entity
    return entities

  def set(self, property_value):
    '''We always verify that the property_value is instance
    of the model that is specified in the property configuration.

    Set will always iterate the property_value to individually set values on existing set of values, or
    append new value if its new. This is to solve problem with seting stuctured value
    '''
    if property_value is not None:
      property_value_copy = property_value
      if not self._property._repeated:
        property_value_copy = [property_value_copy]
      for property_value_item in property_value_copy:
        if not isinstance(property_value_item, self._property.get_modelclass()):
          raise ValueError('Expected %s, got %s' % (self._property.get_modelclass().get_kind(), property_value_item.get_kind()))
      if not self._property._repeated:
        if self.has_value() and self._property_value is not None:
          self._property_value.populate_from(property_value)
        else:
          if property_value._state is None:
            property_value._state = 'created'
          self._property_value = property_value
      else:
        if self.has_value() and self._property_value is not None:
          existing = dict((ent.key.urlsafe(), ent) for ent in self._property_value if ent.key)
          new_list = []
          for ent in property_value:
            # this is to support proper setting of data for existing instances
            exists = ent.key
            if exists is not None:
              exists = existing.get(ent.key.urlsafe())
            else:
              ent._state = 'created'
            if exists is not None:
              exists.populate_from(ent)
              new_list.append(exists)
            else:
              new_list.append(ent)
          del property_value[:]
          property_value.extend(new_list)
        self._property_value = property_value
      self._set_parent()

  def _deep_read(self, read_arguments=None):
    '''This function will keep calling .read() on its sub-entity-like-properties until it no longer has structured properties.
    This solves the problem of loading data in hierarchy.
    '''
    if self.has_value():
      entities = self.read_value
      if not self._property._repeated:
        if not entities:
          entities = []
        else:
          entities = [entities]
      futures = []
      for entity in entities:
        for field_key, field in entity.get_fields().iteritems():
          if hasattr(field, 'is_structured') and field.is_structured:
            has_arguments = field_key in read_arguments
            if has_arguments or (hasattr(field, '_autoload') and field._autoload):
              if not has_arguments:
                read_arguments[field_key] = {'config': {}}
              value = getattr(entity, field_key)
              field_read_arguments = read_arguments.get(field_key, {})
              value.read_async(field_read_arguments)
              futures.append((value, field_read_arguments))
      for future, field_read_arguments in futures:
        future.read(field_read_arguments)  # Again, enforce read and re-loop if any.

  def _read_sync(self, read_arguments):
    '''Read sync should never be called directly, its primary use is for .read()
    the self._property_value in this method will always be list of futures, or a future.
    '''

  def _read(self, read_arguments):
    '''Purpose of _read is to perform proper logic which will populate _property_value with futures or real values
    depending on the nature of the property.
    '''

  def read_async(self, read_arguments=None):
    '''Prepares read arguments for _read function. This function is called internaly trough ORM when possible,
    however, it can be called publicly as well. Beware however, it will only perform the call if no value is present
    or if force_read in config is True.
    '''
    if read_arguments is None:
      read_arguments = {}
    if self._property._read_arguments is not None and isinstance(self._property._read_arguments, dict):
      tools.merge_dicts(read_arguments, self._property._read_arguments)
    config = read_arguments.get('config', {})
    if self._property._readable:
      if (not self.has_value()) or config.get('force_read'):  # it will not attempt to start rpcs if there's already something set in _property_value
        self._read(read_arguments)

  def read(self, read_arguments=None):
    '''Reads the property values in sync mode. Calls read_async and _read_sync to complete full read.
    Also calls _format_callback on the results, sets hierarchy and starts read recursion if possible.
    This function should always be called publicly if data is needed right away from the desired property.
    '''
    if read_arguments is None:
      read_arguments = {}
    if self._property._readable:
      self.read_async(read_arguments)  # first perform all in async mode
      self._read_sync(read_arguments)  # then immidiately perform in sync mode
      format_callback = self._property._format_callback
      if callable(format_callback):
        self._property_value = format_callback(self._entity, self._property_value)
      self._set_parent()
      self._deep_read(read_arguments)
      return self.value


class ReferencePropertyValue(PropertyValue):

  def has_future(self):
    value = self.value
    if isinstance(value, list):
      if len(value):
        value = value[0]
    return isinstance(value, Future)

  def set(self, value):
    if isinstance(value, Key):
      self._property_value = value.get_async()
    else:
      self._property_value = value

  def _read(self):
    target_field = self._property._target_field
    if not target_field and not self._property._callback:
      target_field = self.property_name
    if self._property._callback:
      self._property_value = self._property._callback(self._entity)
    elif target_field:
      field = getattr(self._entity, target_field)
      if field is None:  # If value is none the key was not set, therefore value must be null.
        self._property_value = None
        return self.value
      if not isinstance(field, Key):
        raise ValueError('Targeted field value must be instance of Key. Got %s' % field)
      if self._property._kind is not None and field.kind() != self._property._kind:
        raise ValueError('Kind must be %s, got %s' % (self._property._kind, field.kind()))
      self._property_value = field.get_async()

  def read_async(self):
    if not self.has_value():
      self._read()

  def read(self):
    self.read_async()
    if self.has_future():
      if isinstance(self._property_value, list):
        self._property_value = map(lambda x: x.get_result(), self._property_value)
      else:
        self._property_value = self._property_value.get_result()
      if self._property._format_callback:
        if isinstance(self._property_value, list):
          self._property_value = map(lambda x: self._property._format_callback(self._entity, x), self._property_value)
        else:
          self._property_value = self._property._format_callback(self._entity, self._property_value)
    return self.value

  def delete(self):
    self._property_value = None


class LocalStructuredPropertyValue(StructuredPropertyValue):

  def __init__(self, *args, **kwargs):
    super(LocalStructuredPropertyValue, self).__init__(*args, **kwargs)
    self._structured_values = []
    self._property_value_by_read_arguments = None

  @property
  def read_value(self):
    # property used for fetching values that were retrived using read_arguments
    value = self.value  # trigger value's logic
    if self._property_value_by_read_arguments is None:
      return value
    return self._property_value_by_read_arguments

  @property
  def value(self):
    # overrides base value to solve unwrapping problem that appears when entity is about to be saved to datastore
    # _BaseValue is used to wrap data by ndb
    if self.has_value():
      wrapped = False
      if self._property._repeated:
        if self._property_value:
          if isinstance(self._property_value[0], _BaseValue):
            wrapped = True
      else:
        if isinstance(self._property_value, _BaseValue):
          wrapped = True
      if wrapped:
        self._property._get_user_value(self._entity)  # _get_user_value will unwrap values from _BaseValue when possible
    return super(LocalStructuredPropertyValue, self).value

  def post_update(self):
    for structured in self._structured_values:
      if hasattr(structured, 'post_update'):
        structured.post_update()
    if self.has_value() and self._property._repeated:
      if self._property._repeated:
        values = self.value
        if self._property_value_by_read_arguments is not None:
          for i, val in enumerate(self._property_value_by_read_arguments):
            matches = filter(lambda x: x.key == val.key, values)
            if matches:
              self._property_value_by_read_arguments[i] = matches[0]
          new_entities = [v for v in values if v._state == 'created']
          self._property_value_by_read_arguments.extend(new_entities)
          self._property_value_by_read_arguments.sort(key=lambda x: x._sequence, reverse=True)

  def _read(self, read_arguments):
    property_value = self._property._get_user_value(self._entity)
    property_value_as_list = property_value
    if read_arguments is None:
      read_arguments = {}
    config = read_arguments.get('config', {})
    if property_value_as_list is not None:
      if not self._property._repeated:
        property_value_as_list = [property_value_as_list]
      total = len(property_value_as_list) - 1
      if self._property._repeated:
        supplied_keys = config.get('keys', [])
        supplied_keys = BaseVirtualKeyProperty(kind=self._property.get_modelclass().get_kind(), repeated=True).value_format(supplied_keys)
        if self._property_value_by_read_arguments is not None:
          self._property_value_by_read_arguments = []
      self._property_value_options.update(config)
      for i, value in enumerate(property_value_as_list):
        value._sequence = total - i
        if self._property._repeated and supplied_keys is not None:
          if value.key in supplied_keys:
            if self._property_value_by_read_arguments is None:
              self._property_value_by_read_arguments = []
            self._property_value_by_read_arguments.append(value)
      self._property_value = property_value
    else:
      if self._property._repeated:
        self._property_value = []

  def pre_update(self):
    if self.has_value():
      fields = self._property.get_modelclass().get_fields()
      delete_states = ['removed', 'deleted']

      def collect_structured(value):
        for field_key, field in fields.iteritems():
          if hasattr(field, 'is_structured') and field.is_structured:
            property_value = getattr(value, field_key)
            self._structured_values.append(property_value)

      def delete_structured(entity):
        for structured in self._structured_values:
          repeated = structured._property._repeated
          structured = structured.read()  # read and mark for delete
          if structured is not None:
            if not repeated:
              structured = [structured]
            for structure in structured:
              if entity.key == structure.key.parent():
                structure._state = 'deleted'

      if self._property._repeated:
        delete_entities = []
        for entity in self._property_value:
          if hasattr(entity, 'prepare'):
            entity.prepare(parent=self._entity.key)
          collect_structured(entity)
          if (entity._state in delete_states and self._property._deleteable) \
                  or (not self._property._addable and not hasattr(entity, '_original')):
            # if the property is deleted and deleteable
            # or if property is not addable and it does not exist in originals, remove it.
            delete_entities.append(entity)
            if entity._state == 'deleted':
              delete_structured(entity)

        for delete_entity in delete_entities:
          self._property_value.remove(delete_entity)

        if not self._property._updateable:  # if the property is not updatable we must revert all data to original
          for i, ent in enumerate(self._property_value):
            if hasattr(ent, '_original'):
              self._property_value[i] = copy.deepcopy(ent._original)
      else:
        if hasattr(self._property_value, 'prepare'):
          self._property_value.prepare(parent=self._entity.key)
        collect_structured(self._property_value)
        if self._property_value._state in delete_states and self._property._deleteable:
          if self._property_value._state == 'deleted':
            delete_structured(self._property_value)
          self._property_value = None  # Comply with expando and virtual fields.
      self._property._set_value(self._entity, self._property_value, True)

  def delete(self):
    if self._property._deleteable:
      self.read()
      if self.has_value():
        property_value = self._property_value
        if not self._property._repeated:
          property_value = [self._property_value]
        fields = self._property.get_modelclass().get_fields()
        for value in property_value:
          for field_key, field in fields.iteritems():
            if hasattr(field, 'is_structured') and field.is_structured:
              val = getattr(value, field_key)
              val.delete()
          value._state = 'deleted'

  def duplicate(self):
    if not self._property._duplicable:
      return
    self.read()
    values = self.value
    if self._property._repeated:
      entities = []
      for entity in values:
        entities.append(entity.duplicate())
    else:
      entities = values.duplicate()
    self._property_value = entities
    self._set_parent()
    self._property._set_value(self._entity, entities, True)  # this is because using other method would cause duplicate results via duplicate process.
    return self._property_value

  def add(self, entities):
    '''Primarly used to extend values repeated property
    '''
    if self._property._repeated:
      if self.has_value():
        if self._property_value:
          try:
            last = self._property_value[0]._sequence
            if last is None:
              last = 0
          except IndexError:
            last = 0
          last_sequence = last + 1
          for ent in entities:
            ent._sequence += last_sequence
    else:
      tools.log.warn('cannot use .add() on non repeated property')
    # Always trigger setattr on the property itself
    setattr(self._entity, self.property_name, entities)


class RemoteStructuredPropertyValue(StructuredPropertyValue):

  def has_future(self):
    value = self.value
    if isinstance(value, list):
      if len(value):
        value = value[0]
    return isinstance(value, Future)

  def _read_single(self, read_arguments):
    model = self._property.get_modelclass()
    if not hasattr(model, 'prepare_key'):
      property_value_key = Key(self._property.get_modelclass().get_kind(), self._entity.key_id_str, parent=self._entity.key)
    else:
      property_value_key = model.prepare_key(parent=self._entity.key)
    self._property_value = property_value_key.get_async()

  def _read_repeated(self, read_arguments):
    config = read_arguments.get('config', {})
    search = config.get('search', {})
    supplied_keys = config.get('keys')
    if supplied_keys:
      model = self._property.get_modelclass()
      supplied_keys = BaseVirtualKeyProperty(kind=model.get_kind(), repeated=True).value_format(supplied_keys)
      for supplied_key in supplied_keys:
        if supplied_key.parent() != self._entity.key:
          raise ValueError('invalid_parent_for_key_%s' % supplied_key.urlsafe())
      entities = get_multi_async(supplied_keys)
      self._property_value_options.update(config)
    else:
      if 'search' not in config:
        config['search'] = search
      search['ancestor'] = self._entity.key.urlsafe()
      if 'options' not in search:
        search['options'] = {'limit': 10}
      limit = search['options']['limit']
      search_property = self._property.search
      search_property._cfg.update({'ancestor_kind': self._entity.get_kind()})
      search_arguments = search_property.value_format(search)
      if search_arguments.get('keys'):
        entities = get_multi_async(search_arguments.get('keys'))
      else:
        options = search_property.build_datastore_query_options(search_arguments)
        query = search_property.build_datastore_query(search_arguments)
        if limit == 0:
          entities = query.fetch_async(options=options)
        else:
          entities = query.fetch_page_async(options.limit, options=options)
      if 'property' in search:
        del search['property']
      search['options']['limit'] = limit
      self._property_value_options['search'] = search
    self._property_value = entities

  def _read(self, read_arguments):
    if self._property._repeated:
      self._read_repeated(read_arguments)
    else:
      self._read_single(read_arguments)

  def _read_sync(self, read_arguments):
    '''Will perform all needed operations on how to retrieve all values from Future(s).
    '''
    if self.has_future():
      if self._property._repeated:
        property_value = []
        if isinstance(self._property_value, list):  # this is for get_multi_async, fetch_async()
          get_async_results(self._property_value)
        elif isinstance(self._property_value, Future):  # this is for .fetch_page_async()
          property_value = self._property_value.get_result()
          if isinstance(property_value, tuple):
            cursor = property_value[1]
            if cursor:
              cursor = cursor.urlsafe()
            tools.remove_value(property_value[0])
            self._property_value = property_value[0]
            self._property_value_options['search']['options']['start_cursor'] = cursor
            self._property_value_options['more'] = property_value[2]
          else:
            self._property_value = property_value
      else:  # this is for key.get_async()
        result = self._property_value.get_result()
        if result is None:
          model = self._property.get_modelclass()
          if not hasattr(model, 'prepare_key'):
            remote_single_key = Key(model.get_kind(), self._entity.key_id_str, parent=self._entity.key)
          else:
            remote_single_key = model.prepare_key(parent=self._entity.key)
          result = self._property.get_modelclass()(key=remote_single_key)
        self._property_value = result

  def _post_update_single(self):
    if not hasattr(self._property_value, 'prepare'):
      if self._property_value.key_parent != self._entity.key:
        self._property_value.set_key(self._entity.key_id_str, parent=self._entity.key)
    else:
      self._property_value.prepare(parent=self._entity.key)
    if self._property_value._state == 'deleted' and self._property._deleteable:
      self._property_value.key.delete()
    elif self._property._updateable or (not getattr(self._property_value, '_original', None)
                                        and self._property._addable):
      # put only if the property is updateable, or if its not set and its addable, do the put.
      self._property_value.put()

  def _post_update_repeated(self):
    delete_entities = []
    for entity in self._property_value:
      if not hasattr(entity, 'prepare'):
        if entity.key_parent != self._entity.key:
          key_id = entity.key_id
          entity.set_key(key_id, parent=self._entity.key)
      else:
        entity.prepare(parent=self._entity.key)
      if entity._state == 'deleted' and self._property._deleteable:
        delete_entities.append(entity)
    for delete_entity in delete_entities:
      self._property_value.remove(delete_entity)
    for i, entity in enumerate(self._property_value[:]):
      is_new = entity._state == 'created'
      if not self._property._addable and is_new:
        # if property does not allow new values remove it from put queue
        self._property_value.remove(entity)
      elif not self._property._updateable and not is_new:
        # if updates are not permitted, then always revert to original value
        # note that if addable is true, then user will be in able to add new items no matter what
        self._property_value[i] = copy.deepcopy(entity._original)
    delete_multi([entity.key for entity in delete_entities])
    put_multi(self._property_value)

  def post_update(self):
    if self.has_value():
      if not self._property._repeated:
        self._post_update_single()
      else:
        self._post_update_repeated()
    else:
      pass

  def _delete_single(self):
    self.read()
    self._property_value.key.delete()

  def _delete_repeated(self):
    cursor = Cursor()
    limit = 200
    while True:
      _entities, cursor, more = self._property.get_modelclass().query(ancestor=self._entity.key).fetch_page(limit, start_cursor=cursor, use_cache=False, use_memcache=False)
      if len(_entities):
        self._set_parent(_entities)
        delete_multi([entity.key for entity in _entities])
        if not cursor or not more:
          break
      else:
        break

  def delete(self):
    if self._property._deleteable:
      if not self._property._repeated:
        self._delete_single()
      else:
        self._delete_repeated()

  def _duplicate_single(self):
    self.read()
    duplicated = self._property_value.duplicate()
    self._property_value = duplicated

  def _duplicate_repeated(self):
    '''Fetch ALL entities that belong to this entity.
    On every entity called, .duplicate() function will be called in order to ensure complete recursion.
    '''
    entities = []
    _entities = self._property.get_modelclass().query(ancestor=self._entity.key).fetch()
    if len(_entities):
      for entity in _entities:
        entity.read()
        self._set_parent(entity)
        entities.append(entity.duplicate())
    self._property_value = entities

  def duplicate(self):
    if not self._property._duplicable:
      return
    if not self._property._repeated:
      self._duplicate_single()
    else:
      self._duplicate_repeated()
    self._set_parent()

  def add(self, entities):
    '''Primarly used to extend values list of the property, or override change it if its used on non repeated property.
    '''
    if self._property._repeated:
      if self.has_value():
        entities.extend(self._property_value)
    # Always trigger setattr on the property itself
    setattr(self._entity, self.property_name, entities)


class ReferenceStructuredPropertyValue(StructuredPropertyValue):

  def has_future(self):
    value = self.value
    if isinstance(value, list):
      if len(value):
        value = value[0]
    return isinstance(value, Future)

  def _read(self, read_arguments):
    target_field = self._property._target_field
    callback = self._property._callback
    if not target_field and not callback:
      target_field = self.property_name
    if callback:
      self._property_value = callback(self._entity)
    elif target_field:
      field = getattr(self._entity, target_field)
      if field is None:  # If value is none the key was not set, therefore value must be null.
        self._property_value = None
        return
      if not isinstance(field, Key):
        raise ValueError('Targeted field value must be instance of Key. Got %s' % field)
      if self._property.get_modelclass().get_kind() != field.kind():
        raise ValueError('Kind must be %s, got %s' % (self._property.get_modelclass().get_kind(), field.kind()))
      self._property_value = field.get_async()

  def _read_sync(self, read_arguments):
    if self.has_future():
      if isinstance(self._property_value, list):
        self._property_value = map(lambda x: x.get_result(), self._property_value)
      else:
        self._property_value = self._property_value.get_result()

  def delete(self):
    self._property_value = None

  def duplicate(self):
    pass


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
        if hasattr(entity, '_original'):
          if entity.image != entity._original.image:
            self._property.delete_blobs_on_success(entity._original.image)

  def duplicate(self):
    '''Override duplicate. Parent duplicate method will retrieve all data into self._property_value, and later on,
    here we can finalize duplicate by copying the blob.
    '''
    if not self._property._duplicable:
      return
    super(_ImagePropertyValue, self).duplicate()

    @tasklet
    def async(entity):
      gs_object_name = entity.gs_object_name
      new_gs_object_name = entity.generate_duplicated_string(gs_object_name)
      writable_blob = cloudstorage.open(new_gs_object_name[3:], 'w', content_type=entity.content_type)
      if settings.DEVELOPMENT_SERVER:  # gcs does not work on development server when using modules for some reason...
        blob = urlfetch.fetch('%s/_ah/gcs%s' % (settings.HOST_URL, gs_object_name[3:]))
        writable_blob.write(blob.content)
      else:
        readonly_blob = cloudstorage.open(gs_object_name[3:], 'r')
        # Less consuming memory write, can be only used when using brute force copy.
        # There is no copy feature in cloudstorage sdk, so we have to implement our own!
        while True:
          blob_segment = readonly_blob.read(2000000)  # Read 2mb per write, that should be enough.
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
      raise Return(entity)

    @tasklet
    def mapper(entities):
      out = yield map(async, entities)
      raise Return(out)

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


class LocalStructuredImagePropertyValue(_ImagePropertyValue, LocalStructuredPropertyValue):

  def pre_update(self):
    self._update_blobs()
    super(LocalStructuredImagePropertyValue, self).pre_update()

  def delete(self):
    super(LocalStructuredImagePropertyValue, self).delete()
    self._update_blobs()


class RemoteStructuredImagePropertyValue(_ImagePropertyValue, RemoteStructuredPropertyValue):

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
    while True:
      _entities, cursor, more = self._property.get_modelclass().query(ancestor=self._entity.key).fetch_page(limit, start_cursor=cursor, use_cache=False, use_memcache=False)
      if len(_entities):
        self._set_parent(_entities)
        for entity in _entities:
          self._property.delete_blobs_on_success(entity.image)
          if hasattr(entity, '_original') and entity.image != entity._original.image:
            self._property.delete_blobs_on_success(entity._original.image)
        delete_multi([entity.key for entity in _entities])
        if not cursor or not more:
          break
      else:
        break
