# -*- coding: utf-8 -*-
from base import *
from base import _BaseValue

__all__ = ['PROPERTY_VALUES', 'PropertyValue', 'StructuredPropertyValue', 'LocalStructuredPropertyValue',
          'RemoteStructuredPropertyValue', 'ReferencePropertyValue', '_BaseProperty', '_BaseStructuredProperty',
          'BaseProperty', 'SuperComputedProperty', 'SuperLocalStructuredProperty', 'SuperStructuredProperty',
          'SuperMultiLocalStructuredProperty', 'SuperRemoteStructuredProperty', 'SuperReferenceStructuredProperty',
          'SuperPickleProperty', 'SuperDateTimeProperty', 'SuperJsonProperty', 'SuperTextProperty', 'SuperStringProperty',
          'SuperFloatProperty', 'SuperIntegerProperty', 'SuperKeyProperty', 'SuperVirtualKeyProperty', 'SuperBooleanProperty',
          'SuperDecimalProperty', 'SuperSearchProperty', 'SuperReferenceProperty', 'SuperRecordProperty',
          'SuperPropertyStorageProperty', 'SuperPluginStorageProperty', 'SuperBlobKeyProperty']

PROPERTY_VALUES = []


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
  
  def _deep_read(self, read_arguments=None):  # @todo Just as entity.read(), this function fails it's purpose by calling both read_async() and read()!!!!!!!!
    '''This function will keep calling .read() on its sub-entity-like-properties until it no longer has structured properties.
    This solves the problem of loading data in hierarchy.
    '''
    if self.has_value():
      entities = self.read_value # @todo this should be .value, but for locally structured .read_value
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
      util.merge_dicts(read_arguments, self._property._read_arguments)
    config = read_arguments.get('config', {})
    if self._property._readable:
      if (not self.has_value()) or config.get('force_read'): # it will not attempt to start rpcs if there's already something set in _property_value
        self._read(read_arguments)
  
  def read(self, read_arguments=None):
    '''Reads the property values in sync mode. Calls read_async and _read_sync to complete full read.
    Also calls _format_callback on the results, sets hierarchy and starts read recursion if possible.
    This function should always be called publicly if data is needed right away from the desired property.
    '''
    if read_arguments is None:
      read_arguments = {}
    if self._property._readable:
      self.read_async(read_arguments) # first perform all in async mode
      self._read_sync(read_arguments) # then immidiately perform in sync mode
      format_callback = self._property._format_callback
      if callable(format_callback):
        self._property_value = format_callback(self._entity, self._property_value)
      self._set_parent()
      self._deep_read(read_arguments)
      return self.value
   

class LocalStructuredPropertyValue(StructuredPropertyValue):

  def __init__(self, *args, **kwargs):
    super(LocalStructuredPropertyValue, self).__init__(*args, **kwargs)
    self._structured_values = []
    self._property_value_by_read_arguments = None

  @property
  def read_value(self):
    # property used for fetching values that were retrived using read_arguments
    value = self.value # trigger value's logic
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
        self._property._get_user_value(self._entity) # _get_user_value will unwrap values from _BaseValue when possible
    return super(LocalStructuredPropertyValue, self).value

  def post_update(self):
    for structured in self._structured_values:
      if hasattr(structured, 'post_update'):
        structured.post_update()
    if self.has_value() and self._property._repeated:
      if self._property._repeated:
        values = self.value
        if self._property_value_by_read_arguments is not None:
          for i,val in enumerate(self._property_value_by_read_arguments):
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
        supplied_keys = SuperVirtualKeyProperty(kind=self._property.get_modelclass().get_kind(), repeated=True).value_format(supplied_keys)
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
          structured = structured.read() # read and mark for delete
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

        if not self._property._updateable: # if the property is not updatable we must revert all data to original
          for i,ent in enumerate(self._property_value):
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
    self._property._set_value(self._entity, entities, True) # this is because using other method would cause duplicate results via duplicate process.
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
      util.log.warn('cannot use .add() on non repeated property')
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
      supplied_keys = SuperVirtualKeyProperty(kind=model.get_kind(), repeated=True).value_format(supplied_keys)
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
        if isinstance(self._property_value, list): # this is for get_multi_async, fetch_async()
          get_async_results(self._property_value)
        elif isinstance(self._property_value, Future): # this is for .fetch_page_async()
          property_value = self._property_value.get_result()
          if isinstance(property_value, tuple):
            cursor = property_value[1]
            if cursor:
              cursor = cursor.urlsafe()
            util.remove_value(property_value[0])
            self._property_value = property_value[0]
            self._property_value_options['search']['options']['start_cursor'] = cursor
            self._property_value_options['more'] = property_value[2]
          else:
            self._property_value = property_value
      else: # this is for key.get_async()
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
    elif self._property._updateable or (not getattr(self._property_value, '_original', None) \
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
      if self._property._kind != None and field.kind() != self._property._kind:
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


PROPERTY_VALUES.extend((LocalStructuredPropertyValue, RemoteStructuredPropertyValue, ReferencePropertyValue))


class _BaseProperty(object):
  '''Base property class for all superior properties.
  '''
  _max_size = None
  _value_filters = None
  _searchable = None
  _search_document_field_name = None
  initialized = False
  
  def __init__(self, *args, **kwargs):
    self._max_size = kwargs.pop('max_size', self._max_size)
    self._value_filters = kwargs.pop('value_filters', self._value_filters)
    self._searchable = kwargs.pop('searchable', self._searchable)
    self._search_document_field_name = kwargs.pop('search_document_field_name', self._search_document_field_name)
    super(_BaseProperty, self).__init__(*args, **kwargs)
   
  @property 
  def can_be_none(self): # checks if the property can be set to None
    return True
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    '''
    choices = self._choices
    if choices:
      choices = list(self._choices)
    dic = {'verbose_name': self._verbose_name,
           'indexed': self._indexed,
           'name': self._name,
           'code_name': self._code_name,
           'required': self._required,
           'max_size': self._max_size,
           'choices': choices,
           'default': self._default,
           'repeated': self._repeated,
           'is_structured': self.is_structured,
           'searchable': self._searchable,
           'search_document_field_name': self._search_document_field_name,
           'type': self.__class__.__name__}
    if hasattr(self, '_compressed'):
      dic['compressed'] = self._compressed
    return dic
  
  def property_keywords_format(self, kwds, skip_kwds):
    limits = {'name': 20, 'code_name': 20, 'verbose_name': 50, 'search_document_field_name': 20}
    for k, v in kwds.items():
      if k in skip_kwds:
        v = getattr(self, k, None)
      else:
        if k in ('name', 'verbose_name', 'search_document_field_name'):
          v = unicode(v)
          if len(v) > limits[k]:
            raise FormatError('property_%s_too_long' % k)
        elif k in ('indexed', 'required', 'repeated', 'searchable'):
          v = bool(v)
        elif k == 'choices':
          if v is not None:
            if not isinstance(v, list):
              raise FormatError('expected_list_for_choices')
        elif k == 'default':
          if v is not None:
            v = self.value_format(v) # default value must be acceptable by property value format standards
        elif k == 'max_size':
          if v is not None:
            v = int(v)
      kwds[k] = v
  
  def _property_value_validate(self, value):
    if self._max_size:
      if len(value) > self._max_size:
        raise FormatError('max_size_exceeded')
    if value is None and self._required:
      raise FormatError('required')
    if hasattr(self, '_choices') and self._choices:
      if value not in self._choices:
        raise FormatError('not_in_specified_choices')
  
  def _property_value_filter(self, value):
    if self._value_filters:
      if isinstance(self._value_filters, (list, tuple)):
        for value_filter in self._value_filters:
          value = value_filter(self, value)
      else:
        value = self._value_filters(self, value)
    return value
  
  def _property_value_format(self, value):
    if value is util.Nonexistent:
      if self._default is not None:
        value = copy.deepcopy(self._default)
      elif self._required:
        raise FormatError('required')
      else:
        return value  # Returns util.Nonexistent
    if self._repeated:
      out = []
      if not isinstance(value, (list, tuple)):
        value = [value]
      for v in value:
        self._property_value_validate(v)
        out.append(v)
      return self._property_value_filter(out)
    else:
      self._property_value_validate(value)
      return self._property_value_filter(value)
  
  @property
  def search_document_field_name(self):
    if self._search_document_field_name is not None:
      return self._search_document_field_name
    return self._code_name if self._code_name is not None else self._name
  
  def get_search_document_field(self, value):
    raise NotImplemented('Search representation of property %s not available.' % self)
  
  def resolve_search_document_field(self, value):
    if self._repeated:
      return self.value_format(value.split(' '))
    else:
      return self.value_format(value)
  
  @property
  def is_structured(self):
    return False
  
  def initialize(self):
    '''This function is called by io def init() in io.py to prepare the field for work.
    This is mostly because of get_modelclass lazy-loading of modelclass.
    In order to allow proper loading of modelclass for structured properties for example, we must wait for all python
    classes to initilize into _kind_map.
    Only then we will be in able to pick out the model by its kind from _kind_map registry.
    '''
    pass


class _BaseStructuredProperty(_BaseProperty):
  '''Base class for structured property.
  '''
  _readable = True
  _updateable = True
  _addable = True
  _deleteable = True
  _autoload = True
  _duplicable = True
  _format_callback = None
  _value_class = LocalStructuredPropertyValue
  
  def __init__(self, *args, **kwargs):
    args = list(args)
    self._readable = kwargs.pop('readable', self._readable)
    self._updateable = kwargs.pop('updateable', self._updateable)
    self._deleteable = kwargs.pop('deleteable', self._deleteable)
    self._autoload = kwargs.pop('autoload', self._autoload)
    self._addable = kwargs.pop('addable', self._addable)
    self._format_callback = kwargs.pop('format_callback', self._format_callback)
    self._read_arguments = kwargs.pop('read_arguments', {})
    self._duplicable = kwargs.pop('duplicable', self._duplicable)
    if not kwargs.pop('generic', None): # this is because storage structured property does not need the logic below
      if isinstance(args[0], basestring):
        set_arg = Model._kind_map.get(args[0])
        if set_arg is not None: # if model is not scanned yet, do not set it to none
          args[0] = set_arg
    super(_BaseStructuredProperty, self).__init__(*args, **kwargs)
  
  def get_modelclass(self, **kwargs):
    '''Function that will attempt to lazy-set model if its kind id was specified.
    If model could not be found it will raise an error. This function is used instead of directly accessing
    self._modelclass in our code.
    This function was mainly invented for purpose of structured and multi structured property. See its usage
    trough the code for reference.
    '''
    if isinstance(self._modelclass, basestring):
      # model must be scanned when it reaches this call
      find = Model._kind_map.get(self._modelclass)
      if find is None:
        raise ValueError('Could not locate model with kind %s' % self._modelclass)
      else:
        self._modelclass = find
    return self._modelclass
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    '''
    dic = super(_BaseStructuredProperty, self).get_meta()
    dic['modelclass'] = self.get_modelclass().get_fields()
    dic['modelclass_kind'] = self.get_modelclass().get_kind()
    dic['value_class'] = self._value_class.__name__
    other = ['_autoload', '_readable', '_updateable', '_deleteable', '_read_arguments']
    for o in other:
      dic[o[1:]] = getattr(self, o)
    return dic
  
  def property_keywords_format(self, kwds, skip_kwds):
    super(_BaseStructuredProperty, self).property_keywords_format(kwds, skip_kwds)
    if 'modelclass' not in skip_kwds:
      model = Model._kind_map.get(kwds['modelclass_kind'])
      if model is None:
        raise FormatError('invalid_kind')
      kwds['modelclass'] = model
    '''
    What to do with this?
    if 'managerclass' not in skip_kwds:
      possible_managers = dict((manager.__name__, manager) for manager in PROPERTY_MANAGERS)
      if kwds['managerclass'] not in possible_managers:
        raise FormatError('invalid_manager_supplied')
      else:
        kwds['managerclass'] = possible_managers.get(kwds['managerclass'])
    '''
  
  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()
  
  def value_format(self, value, path=None):
    if path is None:
      path = self._code_name
    source_value = value
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    out = []
    if not self._repeated:
      if not isinstance(value, dict) and not self._required:
        return util.Nonexistent
      value = [value]
    elif source_value is None:
      return util.Nonexistent
    for v in value:
      ent = self._structured_property_format(v, path)
      out.append(ent)
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out
  
  def _set_value(self, entity, value, override=False):
    # __set__
    if override:
      return super(_BaseStructuredProperty, self)._set_value(entity, value)
    value_instance = self._get_value(entity)
    if self._repeated:
      if value_instance.has_value():
        if value_instance.value:
          current_values = value_instance.value
        else:
          current_values = []
        if value:
          for val in value:
            generate = True
            if val.key:
              for i,current_value in enumerate(current_values):
                if current_value.key == val.key:
                  current_value.populate_from(val)
                  generate = False
                  break
            if generate:
              if not val.key:
                val.generate_unique_key()
                if val._state is None:
                  val._state = 'created'
              current_values.append(val)
          current_values.sort(key=lambda x: x._sequence, reverse=True)
      else:
        current_values = value
        if current_values is None:
          current_values = []
        else:
          for val in current_values:
            if not val.key:
              val.generate_unique_key()
              if val._state is None:
                val._state = 'created'
    elif not self._repeated:
      if value is not None:
        current_values = value_instance.value
        if current_values is not None:
          current_values.populate_from(value)
        else:
          current_values = value
          if not current_values.key:
            current_values.generate_unique_key()
      else:
        current_values = value
    value_instance.set(current_values)
    return super(_BaseStructuredProperty, self)._set_value(entity, current_values)
  
  def _delete_value(self, entity):
    # __delete__
    value_instance = self._get_value(entity)
    value_instance.delete()
  
  def _get_value(self, entity):
    # __get__
    super(_BaseStructuredProperty, self)._get_value(entity)
    value_name = '%s_value' % self._name
    if value_name in entity._values:
      value_instance = entity._values[value_name]
    else:
      value_instance = self._value_class(property_instance=self, entity=entity)
      entity._values[value_name] = value_instance
    return value_instance
  
  def _structured_property_field_format(self, fields, values, path):
    _state = allowed_state(values.get('_state'))
    _sequence = values.get('_sequence')
    key = values.get('key')
    kind = values.get('kind')
    errors = {}
    for value_key, value in values.items():
      field = fields.get(value_key)
      if field:
        if hasattr(field, 'value_format'):
          new_path = '%s.%s' % (path, field._code_name)
          try:
            if hasattr(field, '_structured_property_field_format'):
              val = field.value_format(value, new_path)
            else:
              val = field.value_format(value)
          except FormatError as e:
            if isinstance(e.message, dict):
              for k, v in e.message.iteritems():
                if k not in errors:
                  errors[k] = []
                if isinstance(v, (list, tuple)):
                  errors[k].extend(v)
                else:
                  errors[k].append(v)
            else:
              if e.message not in errors:
                errors[e.message] = []
              errors[e.message].append(new_path)
            continue
          if val is util.Nonexistent:
            del values[value_key]
          else:
            values[value_key] = val
        else:
          del values[value_key]
      else:
        del values[value_key]
    if len(errors):
      raise FormatError(errors)
    if key:
      values['key'] = SuperVirtualKeyProperty(kind=kind, required=True).value_format(key)
    values['_state'] = _state  # Always keep track of _state for rule engine!
    if _sequence is not None:
      values['_sequence'] = _sequence
  
  def _structured_property_format(self, entity_as_dict, path):
    provided_kind_id = entity_as_dict.get('kind')
    fields = self.get_model_fields(kind=provided_kind_id)
    entity_as_dict.pop('class_', None)  # Never allow class_ or any read-only property to be set for that matter.
    try:
      self._structured_property_field_format(fields, entity_as_dict, path)
    except FormatError as e:
      raise FormatError(e.message)
    modelclass = self.get_modelclass(kind=provided_kind_id)
    return modelclass(**entity_as_dict)
  
  @property
  def is_structured(self):
    return True
  
  def initialize(self):
    self.get_modelclass()  # Enforce premature loading of lazy-set model logic to prevent errors.

  def _prepare_for_put(self, entity):
    value_instance = self._get_value(entity)  # For its side effects.
    if value_instance.value is None and self._repeated:
      value_instance.set([])
    super(_BaseStructuredProperty, self)._prepare_for_put(entity)


class BaseProperty(_BaseProperty, Property):
  '''Base property class for all properties capable of having _max_size option.'''


class SuperComputedProperty(_BaseProperty, ComputedProperty):
  pass


class SuperLocalStructuredProperty(_BaseStructuredProperty, LocalStructuredProperty):
  
  _autoload = True # always automatically load structured props since they dont take any io
  
  def __init__(self, *args, **kwargs):
    super(SuperLocalStructuredProperty, self).__init__(*args, **kwargs)
    self._keep_keys = True # all keys must be stored by default


class SuperStructuredProperty(_BaseStructuredProperty, StructuredProperty):
  
  _autoload = True # always automatically load structured props since they dont take any io
  
  def _serialize(self, entity, pb, prefix='', parent_repeated=False, projection=None):
    '''Internal helper to serialize this property to a protocol buffer.
    Subclasses may override this method.
    Args:
      entity: The entity, a Model (subclass) instance.
      pb: The protocol buffer, an EntityProto instance.
      prefix: Optional name prefix used for StructuredProperty
        (if present, must end in '.').
      parent_repeated: True if the parent (or an earlier ancestor)
        is a repeated Property.
      projection: A list or tuple of strings representing the projection for
        the model instance, or None if the instance is not a projection.
    '''
    values = self._get_base_value_unwrapped_as_list(entity)
    for value in values:
      if value is not None:
        name = prefix + self._name + '.' + 'stored_key'
        p = pb.add_raw_property()
        p.set_name(name)
        p.set_multiple(self._repeated or parent_repeated)
        v = p.mutable_value()
        ref = value.key.reference()
        rv = v.mutable_referencevalue()  # A Reference
        rv.set_app(ref.app())
        if ref.has_name_space():
          rv.set_name_space(ref.name_space())
        for elem in ref.path().element_list():
          rv.add_pathelement().CopyFrom(elem)
    return super(SuperStructuredProperty, self)._serialize(
        entity, pb, prefix=prefix, parent_repeated=parent_repeated,
        projection=projection)
  
  def _deserialize(self, entity, p, depth=1):
    stored_key = 'stored_key'
    super(SuperStructuredProperty, self)._deserialize(entity, p, depth)
    basevalues = self._retrieve_value(entity)
    if not self._repeated:
      basevalues = [basevalues]
    for basevalue in basevalues:
      if isinstance(basevalue, _BaseValue):
        # NOTE: It may not be a _BaseValue when we're deserializing a
        # repeated structured property.
        subentity = basevalue.b_val
      if hasattr(subentity, stored_key):
        subentity.key = subentity.store_key
        delattr(subentity, stored_key)
      elif stored_key in subentity._properties:
        subentity.key = subentity._properties[stored_key]._get_value(subentity)
        del subentity._properties[stored_key]


class SuperMultiLocalStructuredProperty(_BaseStructuredProperty, LocalStructuredProperty):
  
  _kinds = None
  
  def __init__(self, *args, **kwargs):
    '''So basically:
    argument: SuperMultiLocalStructuredProperty(('3' or ModelItself, '21' or ModelItself))
    will allow instancing of both 51 and 21 that is provided from the input.
    This property should not be used for datastore. Its specifically used for arguments.
    Currently we do not have the code that would allow this to be saved in datastore:
    Entity.images
    => Image
    => OtherTypeOfEntity
    => OtherTypeOfEntityA
 
    In order to support different instances in the repeated list we would also need to store KIND and implement
    additional logic that will load proper model based on protobuff.
    '''
    args = list(args)
    if isinstance(args[0], (tuple, list)):
      self._kinds = args[0]
      set_model1 = Model._kind_map.get(args[0][0]) # by default just pass the first one
      if set_model1 is not None:
        args[0] = set_model1
    if isinstance(args[0], basestring):
      set_model1 = Model._kind_map.get(args[0]) # by default just pass the first one
      if set_model1 is not None: # do not set it if it wasnt scanned yet
        args[0] = set_model1
    super(SuperMultiLocalStructuredProperty, self).__init__(*args, **kwargs)
  
  def get_modelclass(self, kind=None, **kwds):
    if self._kinds and kind:
      if kind:
        _kinds = []
        for other in self._kinds:
          if isinstance(other, Model):
            _the_kind = other.get_kind()
          else:
            _the_kind = other
          _kinds.append(_the_kind)
        if kind not in _kinds:
          raise ValueError('Expected Kind to be one of %s, got %s' % (_kinds, kind))
        model = Model._kind_map.get(kind)
        return model
    return super(SuperMultiLocalStructuredProperty, self).get_modelclass()
  
  def get_meta(self):
    out = super(SuperMultiLocalStructuredProperty, self).get_meta()
    out['kinds'] = self._kinds
    return out
  
  def property_keywords_format(self, kwds, skip_kwds):
    super(SuperMultiLocalStructuredProperty, self).property_keywords_format(kwds, skip_kwds)
    if 'kinds' not in skip_kwds:
      kwds['kinds'] = map(lambda x: unicode(x), kwds['kinds'])


class SuperRemoteStructuredProperty(_BaseStructuredProperty, Property):
  '''This property is not meant to be used as property storage. It should be always defined as virtual property.
  E.g. the property that never gets saved to the datastore.
  '''
  _indexed = False
  _repeated = False
  _readable = True
  _updateable = True
  _deleteable = True
  _autoload = False
  _value_class = RemoteStructuredPropertyValue
  search = None
  
  def __init__(self, modelclass, name=None, compressed=False, keep_keys=True, **kwds):
    if isinstance(modelclass, basestring):
      set_modelclass = Model._kind_map.get(modelclass)
      if set_modelclass is not None:
        modelclass = set_modelclass
    kwds['generic'] = True
    self.search = kwds.pop('search', None)
    if self.search is None:
      self.search = {'cfg':{
              'filters': {},
              'indexes': [{'ancestor': True, 'filters': [], 'orders': []}],
            }}
    super(SuperRemoteStructuredProperty, self).__init__(name, **kwds)
    self._modelclass = modelclass
  
  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()
  
  def _set_value(self, entity, value):
    # __set__
    value_instance = self._get_value(entity)
    value_instance.set(value)
  
  def _prepare_for_put(self, entity):
    self._get_value(entity)  # For its side effects.

  def initialize(self):
    super(SuperRemoteStructuredProperty, self).initialize()
    default_search_cfg = {'cfg': {'search_arguments': {'kind': self._modelclass.get_kind()},
                          'search_by_keys': False,
                          'filters': {},
                          'indexes': [{'ancestor': True, 'filters': [], 'orders': []}]}}
    util.merge_dicts(self.search, default_search_cfg)
    self.search = SuperSearchProperty(**self.search)

  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    '''
    dic = super(SuperRemoteStructuredProperty, self).get_meta()
    dic['search'] = self.search
    return dic


class SuperReferenceStructuredProperty(SuperRemoteStructuredProperty):
  '''Reference structured is the same as remote, except it uses different default value class and its default flags for
  updating, deleting are always false.
  
  '''
  _value_class = ReferenceStructuredPropertyValue
  _updateable = False
  _deleteable = False
  _addable = False
  
  def __init__(self, *args, **kwargs):
    self._callback = kwargs.pop('callback', None)
    self._target_field = kwargs.pop('target_field', None)
    super(SuperReferenceStructuredProperty, self).__init__(*args, **kwargs)
    self._updateable = False
    self._deleteable = False

  def value_format(self, value, path=None):
    # reference type properties can never be updated by the client
    return util.Nonexistent


class SuperPickleProperty(_BaseProperty, PickleProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    return value


class SuperDateTimeProperty(_BaseProperty, DateTimeProperty):
 
  @property
  def can_be_none(self):
    field = self
    if ((field._auto_now or field._auto_now_add) and field._required):
      return False
    return True
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    out = []
    if not self._repeated:
      value = [value]
    for v in value:
      out.append(datetime.datetime.strptime(v, settings.DATETIME_FORMAT))
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      return search.DateField(name=self.search_document_field_name, value=value)
  
  def resolve_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return value
    else:
      return value
  
  def get_meta(self):
    dic = super(SuperDateTimeProperty, self).get_meta()
    dic['auto_now'] = self._auto_now
    dic['auto_now_add'] = self._auto_now_add
    return dic
  
  def property_keywords_format(self, kwds, skip_kwds):
    super(SuperDateTimeProperty, self).property_keywords_format(kwds, skip_kwds)
    for kwd in ('auto_now', 'auto_now_add'):
      if kwd not in skip_kwds:
        kwds[kwd] = bool(kwds[kwd])


class SuperJsonProperty(_BaseProperty, JsonProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if isinstance(value, basestring):
      return json.loads(value)
    else:
      return value
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: json.dumps(v), value))
    else:
      value = json.dumps(value)
    return search.TextField(name=self.search_document_field_name, value=value)


class SuperTextProperty(_BaseProperty, TextProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if value is None:
      return value
    if self._repeated:
      return [unicode(v) for v in value]
    else:
      return unicode(value)
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(value)
    return search.HtmlField(name=self.search_document_field_name, value=value)


class SuperStringProperty(_BaseProperty, StringProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if self._repeated:
      values = []
      for v in value:
        if v is not None:
          v = unicode(v)
          values.append(v)
      return values
    else:
      if value is not None:
        value = unicode(value)
      return value
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = unicode(' ').join(value)
    return search.TextField(name=self.search_document_field_name, value=unicode(value))


class SuperFloatProperty(_BaseProperty, FloatProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if self._repeated:
      return [float(v) for v in value]
    else:
      return float(value)
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    return search.NumberField(name=self.search_document_field_name, value=value)


class SuperIntegerProperty(_BaseProperty, IntegerProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if self._repeated:
      return [long(v) for v in value]
    else:
      if not self._required and value is None:
        return value
      return long(value)
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    return search.NumberField(name=self.search_document_field_name, value=value)


class SuperKeyProperty(_BaseProperty, KeyProperty):
  '''This property is used on models to reference ndb.Key property.
  Its format function will convert urlsafe string into a ndb.Key and check if the key
  exists in the datastore. If the key does not exist, it will throw an error.
  If key existence feature isn't required, SuperVirtualKeyProperty() can be used in exchange.
  
  '''
  def value_format(self, value, skip_get=False):
    try:
      value = self._property_value_format(value)
      if value is util.Nonexistent:
        return value
      if not self._repeated and not self._required and (value is None or len(value) < 1):
        # if key is not required, and value is either none or length is not larger than 1, its considered as none
        return None
      try:
        if self._repeated:
          out = [Key(urlsafe=v) for v in value]
        else:
          out = [Key(urlsafe=value)]
      except ValueError:
        raise FormatError('malformed_key')
      for key in out:
        if self._kind and key.kind() != self._kind:
          raise FormatError('invalid_kind')
      if not skip_get:
        entities = get_multi(out)
        for i, entity in enumerate(entities):
          if entity is None:
            raise FormatError('not_found')
      if not self._repeated:
        try:
          out = out[0]
        except IndexError as e:
          out = None
      return out
    except Exception as e:
      if e.message == 'not_found':
        raise FormatError('not_found') # if its not found, its not found
      # Failed to build from urlsafe, proceed with KeyFromPath.
      value = self._property_value_format(value)
      if value is util.Nonexistent:
        return value
      out = []
      if self._repeated:
        for key_path in value:
          kwds = {}
          try:
            kwds = key_path[1]
          except IndexError:
            pass
          key = Key(*key_path[0], **kwds)
          if self._kind and key.kind() != self._kind:
            raise FormatError('invalid_kind')
          out.append(key)
        if not skip_get:
          entities = get_multi(out)
          for i, entity in enumerate(entities):
            if entity is None:
              raise FormatError('not_found')
      else:
        kwds = {}
        try:
          kwds = value[1]
        except IndexError:
          pass
        out = Key(*value[0], **kwds)
        if self._kind and out.kind() != self._kind:
          raise FormatError('invalid_kind')
        entity = out.get()
        if entity is None:
          raise FormatError('not_found')
      return out
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: v.urlsafe(), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      try:
        value = value.urlsafe()
      except:
        value = str(value)
      return search.AtomField(name=self.search_document_field_name, value=value)

  def resolve_search_document_field(self, value):
    if value == 'None':
      value = None
    return super(SuperKeyProperty, self).resolve_search_document_field(value)
    
  def get_meta(self):
    dic = super(SuperKeyProperty, self).get_meta()
    dic['kind'] = self._kind
    return dic


class SuperVirtualKeyProperty(SuperKeyProperty):
  '''This property is exact as SuperKeyProperty, except its format function is not making any calls
  to the datastore to check the existence of the provided urlsafe key. It will simply format the
  provided urlsafe key into a ndb.Key.
  
  '''
  def value_format(self, value):
    return super(SuperVirtualKeyProperty, self).value_format(value, skip_get=True)


class SuperBooleanProperty(_BaseProperty, BooleanProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if self._repeated:
      return [bool(long(v)) for v in value]
    else:
      return bool(long(value))
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      value = str(value)
      return search.AtomField(name=self.search_document_field_name, value=value)
  
  def resolve_search_document_field(self, value):
    if self._repeated:
      out = []
      for v in value.split(' '):
        if v == 'True':
          out.append(True)
        else:
          out.append(False)
    else:
      return value == 'True'


class SuperBlobKeyProperty(_BaseProperty, BlobKeyProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    out = []
    if not self._repeated:
      value = [value]
    for v in value:
      # This alone will raise error if the upload is malformed.
      try:
        blob = blobstore.parse_blob_info(v).key()
      except:
        blob = blobstore.BlobKey(v)
      out.append(blob)
    if not self._repeated:
      try:
        out = out[0]
      except IndexError as e:
        out = None
    return out
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      value = str(value)
      return search.AtomField(name=self.search_document_field_name, value=value)


class SuperDecimalProperty(SuperStringProperty):
  '''Decimal property that accepts only decimal.Decimal.'''
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    if (value is None or (isinstance(value, basestring) and not len(value))) and not self._required:
      return util.Nonexistent
    if self._repeated:
      i = 0
      try:
        out = []
        for i, v in enumerate(value):
          out.append(decimal.Decimal(v))
        value = out
      except:
        raise FormatError('invalid_number_on_sequence_%s' % i)
    else:
      try:
        value = decimal.Decimal(value)
      except:
        raise FormatError('invalid_number')
    if value is None:
      raise FormatError('invalid_number')
    return value
  
  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      value = str(value)
      # Specifying this as a number field will either convert it to INT or FLOAT.
      return search.NumberField(name=self.search_document_field_name, value=value)
  
  def _validate(self, value):
    if not isinstance(value, decimal.Decimal):
      raise ValueError('expected_decimal')
  
  def _to_base_type(self, value):
    return str(value)
  
  def _from_base_type(self, value):
    return decimal.Decimal(value)


class SuperSearchProperty(SuperJsonProperty):
  
  def __init__(self, *args, **kwargs):
    '''Filters work like this:
    First you configure SuperSearchProperty with search_arguments, filters and indexes parameters.
    This configuration takes place at the property definition place.
    cfg = {
      'use_search_engine': True,
      'search_arguments': {'kind': '35'...},
      'ancestor_kind': '35',
      'filters': {'field1': SuperStringProperty(required=True)}},  # With this config you define expected filter value property.
      'orders': {'created': {'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}}},  # This parameter is used for search engine default values!
      'indexes': [{'ancestor': True, 'filters': [('field1', [op1, op2]), ('field2', [op1]), ('field3', [op2])], 'orders': [('field1', ['asc', 'desc'])]},
                  {'ancestor': False, 'filters': [('field1', [op1]), ('field2', [op1])], 'orders': [('field1', ['asc', 'desc'])]}]
    }
    search = SuperSearchProperty(cfg=cfg)
    
    Search values that are provided with input will be validated trough SuperSearchProperty().value_format() function.
    Example of search values that are provided in input after processing:
    context.input['search'] = {'kind': '37',
                               'ancestor': 'fjdkahsekuarg4wi784wnvsxiu487',
                               'namespace': 'wjbryj4gr4y57jtgnfj5959',
                               'projection': ['name'],
                               'group_by': ['name'],
                               'options': {'limit': 10000, cursor: '34987hgehevbjeriy3478dsbkjbdskhrsgkugsrkbsg'},
                               'default_options': {'limit': 10000, cursor: '34987hgehevbjeriy3478dsbkjbdskhrsgkugsrkbsg'},
                               'filters': [{'field': 'name', 'operator': '==', 'value': 'Test'}],
                               'orders': [{'field': 'name', 'operator': 'asc'}],
                               'keys': [key1, key2, key3]}
    
    '''
    self._cfg = kwargs.pop('cfg', {})
    super(SuperSearchProperty, self).__init__(*args, **kwargs)
  
  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    dic = super(SuperSearchProperty, self).get_meta()
    dic['cfg'] = self._cfg
    return dic
  
  def _clean_format(self, values):
    allowed_arguments = ['kind', 'ancestor', 'projection',
                         'group_by', 'options', 'default_options',
                         'filters', 'orders', 'keys', 'query_string']
    for value_key, value in values.items():
      if value_key not in allowed_arguments:
        del values[value_key]
  
  def _kind_format(self, values):
    kind = values.get('kind')
    model = Model._kind_map.get(kind)
    if not model:
      raise FormatError('invalid_model_kind')
  
  def _ancestor_format(self, values):
    ancestor = values.get('ancestor')
    if ancestor is not None:
      ancestor_kind = self._cfg.get('ancestor_kind')
      if ancestor_kind is not None:
        # sometimes the parent is not stored in database, so just shallow validation should suffice
        values['ancestor'] = SuperVirtualKeyProperty(kind=ancestor_kind, required=True).value_format(ancestor)
      else:
        del values['ancestor']
  
  def _keys_format(self, values):
    keys = values.get('keys')
    ancestor = values.get('ancestor')
    if keys is not None:
      if self._cfg.get('search_by_keys'):
        values['keys'] = SuperKeyProperty(kind=values['kind'], repeated=True).value_format(keys)
      else:
        del values['keys']
  
  def _projection_group_by_format(self, values):
    def list_format(list_values):
      if not isinstance(list_values, (tuple, list)):
        raise FormatError('not_list')
      remove_list_values = []
      for value in list_values:
        if not isinstance(value, str):
          remove_list_values.append(value)
      for value in remove_list_values:
        list_values.remove(value)
    
    projection = values.get('projection')
    if projection is not None:
      list_format(projection)
    group_by = values.get('group_by')
    if group_by is not None:
      list_format(group_by)
  
  def _filters_orders_format(self, values):
    ''''filters': [{'field': 'name', 'operator': '==', 'value': 'Test'}]
       'orders': [{'field': 'name', 'operator': 'asc'}]
    
    '''
    def _validate(cfg_values, input_values, method):
      # cfg_filters = [('name', ['==', '!=']), ('age', ['>=', '<=']), ('sex', ['=='])]
      # input_filters = [{'field': 'name', 'operator': '==', 'value': 'Mia'}]
      # cfg_orders = [('name', ['asc'])]
      # input_orders = [{'field': 'name', 'operator': 'asc'}]
      if len(cfg_values) != len(input_values):
        raise FormatError('%s_values_mismatch' % method)  # @todo Write this error correctly!
      for i, input_value in enumerate(input_values):  # @todo If input_values length is 0, and above validation passes, than there should not be any errors!?
        cfg_value = cfg_values[i]
        if input_value['field'] != cfg_value[0]:
          raise FormatError('expected_%s_field_%s_at_%s' % (method, cfg_value[0], i))
        if input_value['operator'] not in cfg_value[1]:
          raise FormatError('expected_%s_operator_%s_at_%s' % (method, cfg_value[1], i))
    
    if self._cfg.get('search_by_keys') and 'keys' in values:
      return values
    defaults = self._default
    # if defaults are defined then load them if the user did not supply them
    if not defaults:
      defaults = {}
    ancestor = values.get('ancestor')
    if 'filters' not in values:
      values['filters'] = defaults.get('filters', [])
    if 'orders' not in values:
      values['orders'] = defaults.get('orders', [])
    filters = values.get('filters')
    orders = values.get('orders')
    cfg_filters = self._cfg.get('filters', {})
    cfg_indexes = self._cfg['indexes']
    success = False
    e = 'unknown'
    for cfg_index in cfg_indexes:
      try:
        cfg_index_ancestor = cfg_index.get('ancestor')
        cfg_index_filters = cfg_index.get('filters', [])
        cfg_index_orders = cfg_index.get('orders', [])
        if ancestor is not None:
          if not cfg_index_ancestor:  # @todo Not sure if we have to enforce ancestor if index_cfg.get('ancestor') is True!?
            raise FormatError('ancestor_not_allowed')
        _validate(cfg_index_filters, filters, 'filter')
        _validate(cfg_index_orders, orders, 'order')
        for input_filter in filters:
          input_field = input_filter['field']
          input_value = input_filter['value']
          cfg_field = cfg_filters[input_field]
          input_filter['value'] = cfg_field.value_format(input_value)
        success = True
        break
      except Exception as e:
        pass
    if success is not True:
      if isinstance(e, Exception):
        e = e.message
      raise FormatError(e)
  
  def _datastore_query_options_format(self, values):
    def options_format(options_values):
      for value_key, value in options_values.items():
        if value_key in ['keys_only', 'produce_cursors']:
          if not isinstance(value, bool):
            del options_values[value_key]
        elif value_key == 'limit':
          if not isinstance(value, (int, long)):
            raise FormatError('limit_value_incorrect')
          if value == 0:
            del options_values[value_key]
        elif value_key in ['batch_size', 'prefetch_size', 'deadline']:
          if not isinstance(value, (int, long)):
            del options_values[value_key]
        elif value_key in ['start_cursor', 'end_cursor']:
          try:
            options_values[value_key] = Cursor(urlsafe=value)
          except:
            del options_values[value_key]
        elif value_key == 'read_policy':
          if not isinstance(value, EVENTUAL_CONSISTENCY):  # @todo Not sure if this is ok!? -- @reply i need to check this
            del options_values[value_key]
        else:
          del options_values[value_key]
    
    default_options = values.get('default_options')
    if default_options is not None:
      options_format(default_options)
    options = values.get('options', {})
    if 'limit' not in options.keys():
      raise FormatError('limit_value_missing')
    options_format(options)
  
  def _search_query_orders_format(self, values):
    orders = values.get('orders')
    cfg_orders = self._cfg.get('orders', {})
    if orders is not None:
      for _order in orders:
        cfg_order = cfg_orders.get(_order['field'], {})
        _order['default_value'] = cfg_order.get('default_value', {})
  
  def _search_query_options_format(self, values):
    options = values.get('options', {})
    if 'limit' not in options.keys():
      raise FormatError('limit_value_missing')
    for value_key, value in options.items():
      if value_key == 'limit':
        if not isinstance(value, (int, long)):
          raise FormatError('limit_value_incorrect')
      elif value_key in ['cursor']:
        try:
          options[value_key] = search.Cursor(web_safe_string=value)
        except:
          del options[value_key]
      else:
        del options[value_key]
  
  def value_format(self, values):
    values = super(SuperSearchProperty, self).value_format(values)
    override = self._cfg.get('search_arguments', {})
    util.override_dict(values, override)
    self._clean_format(values)
    self._kind_format(values)
    self._ancestor_format(values)
    self._keys_format(values)
    self._projection_group_by_format(values)
    self._filters_orders_format(values)
    if self._cfg.get('use_search_engine', False):
      self._search_query_orders_format(values)
      self._search_query_options_format(values)
    else:
      self._datastore_query_options_format(values)
    values['property'] = self
    return values
  
  def build_datastore_query_filters(self, value):
    _filters = value.get('filters')
    filters = []
    model = Model._kind_map.get(value.get('kind'))
    if _filters is None:
      return filters
    for _filter in _filters:
      field = util.get_attr(model, _filter['field'])
      op = _filter['operator']
      value = _filter['value']
      # here we could use
      # field._comparison(op, value)
      # https://code.google.com/p/appengine-ndb-experiment/source/browse/ndb/model.py?r=6b3f88b663a82831e9ecee8adbad014ff774c365#831
      if op == '==': # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this also needs improvements
        filters.append(field == value)
      elif op == '!=':
        filters.append(field != value)
      elif op == '>':
        filters.append(field > value)
      elif op == '<':
        filters.append(field < value)
      elif op == '>=':
        filters.append(field >= value)
      elif op == 'IN':
        filters.append(field.IN(value))
      elif op == 'ALL_IN':
        for v in value:
          filters.append(field == v)
      elif op == 'contains':
        letters = list(string.printable)
        try:
          last = letters[letters.index(value[-1].lower()) + 1]
          filters.append(field >= value)
          filters.append(field < last)
        except ValueError as e:  # Value not in the letter scope, šččđčžćč for example.
          filters.append(field == value)
    return filters
  
  def build_datastore_query_orders(self, value):
    _orders = value.get('orders')
    orders = []
    model = Model._kind_map.get(value.get('kind'))
    if _orders is None:
      return orders
    for _order in _orders:
      field = getattr(model, _order['field'])
      op = _order['operator']
      if op == 'asc':
        orders.append(field)
      else:
        orders.append(-field)
    return orders
  
  def build_datastore_query_options(self, value):
    options = value.get('options', {})
    return QueryOptions(**options)
  
  def build_datastore_query_default_options(self, value):
    default_options = value.get('default_options', {})
    return QueryOptions(**default_options)
  
  def build_datastore_query(self, value):
    filters = self.build_datastore_query_filters(value)
    orders = self.build_datastore_query_orders(value)
    default_options = self.build_datastore_query_default_options(value)
    return Query(kind=value.get('kind'), ancestor=value.get('ancestor'),
                 namespace=value.get('namespace'), projection=value.get('projection'),
                 group_by=value.get('group_by'), default_options=default_options).filter(*filters).order(*orders)
  
  def build_search_query_string(self, value):
    query_string = value.get('query_string', '')
    if query_string:
      return query_string
    _filters = value.get('filters')
    filters = []
    kind = value.get('kind')
    if kind:
      filters.append('(kind=' + kind + ')')
    ancestor = value.get('ancestor')
    if ancestor:
      filters.append('(ancestor=' + ancestor + ')')
    for _filter in _filters:
      field = _filter['field']
      op = _filter['operator']
      value = _filter['value']
      if field == 'query_string':
        filters.append(value)
        break
      if op == '==': # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this also needs improvements
        filters.append('(' + field + '=' + value + ')')
      elif op == '!=':
        filters.append('(NOT ' + field + '=' + value + ')')
      elif op == '>':
        filters.append('(' + field + '>' + value + ')')
      elif op == '<':
        filters.append('(' + field + '<' + value + ')')
      elif op == '>=':
        filters.append('(' + field + '>=' + value + ')')
      elif op == '<=':
        filters.append('(' + field + '<=' + value + ')')
      elif op == 'IN':
        filters.append('(' + ' OR '.join(['(' + field + '=' + v + ')' for v in value]) + ')')
    return ' AND '.join(filters)
  
  def build_search_query_sort_options(self, value):
    _orders = value.get('orders')
    options = value.get('options', {})
    direction = {'asc': search.SortExpression.ASCENDING, 'desc': search.SortExpression.DESCENDING}
    orders = []
    for _order in _orders:
      field = _order['field']
      op = _order['operator']
      default_value = _order['default_value']
      orders.append(search.SortExpression(expression=field, direction=direction.get(op),
                                          default_value=default_value.get(op)))
    return search.SortOptions(expressions=orders, limit=options.get('limit'))
  
  def build_search_query_options(self, value):
    sort_options = self.build_search_query_sort_options(value)
    options = value.get('options', {})
    return search.QueryOptions(limit=options.get('limit'),
                               returned_fields=value.get('projection'),
                               sort_options=sort_options, cursor=options.get('cursor'))
  
  def build_search_query(self, value):
    query_string = self.build_search_query_string(value)
    query_options = self.build_search_query_options(value)
    return search.Query(query_string=query_string, options=query_options)


class SuperReferenceProperty(SuperKeyProperty):
  '''This property can be used to read stuff in async mode upon reading entity from protobuff.
  However, this can be also used for storing keys, behaving like SuperKeyProperty.
  Setter value should always be a key, however it can be an entire entity instance from which it will use its .key
  The property will have no substructure permissions. If you want those, use SuperReferenceStructuredProperty
  >>> entity.user = user_key
  Getter usually retrieves entire entity instance,
  or something else can be returned based on the _format_callback option.
  >>> entity.user.email
  Beware with usage of this property. It will automatically start RPC calls in async mode as soon as the
  from_pb and _post_get callback are executed unless autoload is set to False.
  Main difference between SuperReferenceProperty and SuperReferenceStructuredProperty is that
  it does not have structured field permissions, ergo only permissions it has is on itself and
  it will load when _from_pb, _post_get_hook are executed, so its best usage is seen when retrieving multiple entities
  from datastore.
  Plainly said, it serves as automatic custom getter from the database that
  can retreive whatever it wants and how it wants. @see class Record for reference.
  '''
  _value_class = ReferencePropertyValue
  _async = True

  can_be_copied = False
  
  def __init__(self, *args, **kwargs):
    self._callback = kwargs.pop('callback', None)
    self._format_callback = kwargs.pop('format_callback', None)
    self._target_field = kwargs.pop('target_field', None)
    self._autoload = kwargs.pop('autoload', True)
    self._store_key = kwargs.pop('store_key', False)
    if self._callback != None and not callable(self._callback):
      raise ValueError('callback must be a callable, got %s' % self._callback)
    super(SuperReferenceProperty, self).__init__(*args, **kwargs)
  
  def _set_value(self, entity, value):
    # __set__
    value_instance = self._get_value(entity, internal=True)
    value_instance.set(value)
    if not isinstance(value, Key) and hasattr(value, 'key'):
      value = value.key
    if self._store_key:
      super(SuperReferenceProperty, self)._set_value(entity, value)
  
  def _delete_value(self, entity):
    # __delete__
    value_instance = self._get_value(entity, internal=True)
    value_instance.delete()
    if self._store_key:
      return super(SuperReferenceProperty, self)._delete_value(entity)
  
  def _get_value(self, entity, internal=None):
    # __get__
    value_name = '%s_value' % self._name
    if value_name in entity._values:
      value_instance = entity._values[value_name]
    else:
      value_instance = self._value_class(property_instance=self, entity=entity)
      entity._values[value_name] = value_instance
    if internal:
      return value_instance
    return value_instance.read()
  
  def get_output(self):
    dic = super(SuperReferenceProperty, self).get_meta()
    other = ['_target_field', '_store_key']
    for o in other:
      dic[o[1:]] = getattr(self, o)
    return dic

  def value_format(self, value, path=None):
    return util.Nonexistent


class SuperRecordProperty(SuperRemoteStructuredProperty):
  '''Usage: '_records': SuperRecordProperty(Domain or '6')
  '''

  can_be_copied = False

  def __init__(self, *args, **kwargs):
    args = list(args)
    self._modelclass2 = args[0]
    args[0] = '0'
    self._repeated = True
    search = kwargs.get('search', {})
    if 'default' not in search:
      search['default'] = {'filters': [], 'orders': [{'field': 'logged', 'operator': 'desc'}]}
    if 'cfg' not in search:
      search['cfg'] = {
          'indexes': [{
            'ancestor': True,
            'filters': [],
            'orders': [('logged', ['desc'])]
          }],
        }
    kwargs['search'] = search
    super(SuperRecordProperty, self).__init__(*args, **kwargs)
    # Implicitly state that entities cannot be updated or deleted.
    self._updateable = False
    self._deleteable = False
    self._duplicable = False
  
  def get_model_fields(self, **kwargs):
    parent = super(SuperRecordProperty, self).get_model_fields(**kwargs)
    parent.update(self._modelclass2.get_fields())
    return parent
  
  def initialize(self):
    super(SuperRecordProperty, self).initialize()
    if isinstance(self._modelclass2, basestring):
      set_modelclass2 = Model._kind_map.get(self._modelclass2)
      if set_modelclass2 is None:
        raise ValueError('Could not locate model with kind %s' % self._modelclass2)
      else:
        self._modelclass2 = set_modelclass2


class SuperPropertyStorageProperty(SuperPickleProperty):
  '''This property is used to store instances of properties to the datastore pickled.
  Incoming data should be formatted exactly as properties get_output function e.g.
  {
      "searchable": null,
      "repeated": false,
      "code_name": "serving_url",
      "search_document_field_name": null,
      "max_size": null,
      "name": "serving_url", # note the friendly name used, this is intentional since all the names will be user-supplied
      "default": null,
      "type": "SuperStringProperty",
      "required": true,
      "is_structured": false,
      "choices": null,
      "verbose_name": null
  }
  the config should be a list of property instances like so:
  JOURNAL_FIELDS = ((orm.SuperStringProperty(default_keyword_here=True, default_keyword2=False...),
                          (... list of kwargs that cannot be set by user...),
                               (... kwargs that are implicitly required -- by default
                                 all kwargs found in property are required.)),  ... ))
  
  '''
  def __init__(self, *args, **kwargs):
    self._cfg = kwargs.pop('cfg', None)
    super(SuperPropertyStorageProperty, self).__init__(*args, **kwargs)
  
  def get_meta(self):
    dic = super(SuperPropertyStorageProperty, self).get_meta()
    dic['cfg'] = self._cfg
    return dic
  
  def value_format(self, value):
    bogus_kwds = ('type', 'is_structured', 'code_name')  # List of kwds which exist, but can not be set as in __init__.
    value = super(SuperPropertyStorageProperty, self).value_format(value)
    if value is util.Nonexistent:
      return value
    out = collections.OrderedDict()
    def gets(c, i, d=None):
      try:
        return c[i]
      except IndexError:
        return d
    parsed = {}
    for name, kwds in value.iteritems():
      field_type = kwds.get('type')
      field = None
      skip_kwargs = None
      required_kwargs = None
      for cfg in self._cfg:
        the_field = cfg[0]
        skip_kwargs = gets(cfg, 1, ())
        required_kwargs = gets(cfg, 2, None)
        if the_field.__class__.__name__ == field_type: # we compare with __name__ since type in get output is always Class.__name___
          field = the_field
          break
      if field is None:
        raise FormatError('invalid_field_type_provided')
      possible_kwargs = tuple(field.get_meta().keys())
      if required_kwargs is None:
        required_kwargs = possible_kwargs
      for name in required_kwargs:
        if name not in kwds and name not in bogus_kwds:
          raise FormatError('missing_keyword_%s' % name)
      for name in kwds.iterkeys():
        if name not in possible_kwargs:
          raise FormatError('unexpected_keyword_%s' % name)
      kwds['name'] = kwds.get('name') # @todo prefix for name
      if kwds['name'] in parsed:
        raise FormatError('duplicate_property_name_%s' % kwds['name'])
      parsed[kwds['name']] = 1
      field.property_keywords_format(kwds, skip_kwargs)
      for bogus in bogus_kwds:
        kwds.pop(bogus, None)
      out[kwds['name']] = field.__class__(**kwds)
    del parsed
    return out


class SuperPluginStorageProperty(SuperPickleProperty):
  
  _kinds = None
  
  def __init__(self, *args, **kwargs):
    args = list(args)
    if isinstance(args[0], (tuple, list)):
      self._kinds = args[0]
    if isinstance(args[0], basestring):
      self._kinds = (args[0],)
    args = args[1:]
    super(SuperPluginStorageProperty, self).__init__(*args, **kwargs)
    
  def _get_value(self, entity):
    values = super(SuperPluginStorageProperty, self)._get_value(entity)
    if values:
      sequence = len(values)
      for val in values:
        val.read()
        sequence -= 1
        val._sequence = sequence
    return values
  
  def _set_value(self, entity, value):
    # __set__
    # plugin storage needs just to generate key if its non existant, it cannot behave like local struct and remote struct
    # because generally its not in its nature to behave like that
    # its just pickling of data with validation.
    for val in value[:]:
      if val._state == 'deleted':
        value.remove(val)
        continue
      if not val.key:
        val.generate_unique_key()
      for field_key, field in val.get_fields().iteritems():
        if hasattr(field, 'is_structured') and field.is_structured:
          structured = getattr(val, field_key)
          structured.pre_update()
    return super(SuperPluginStorageProperty, self)._set_value(entity, value)
  
  def value_format(self, value, path=None):
    if path is None:
      path = self._code_name
    value = self._property_value_format(value)
    if value is util.Nonexistent:
      return value
    out = []
    if not isinstance(value, list):
      raise FormatError('expected_list')
    for v in value:
      out.append(self._structured_property_format(v, path))
    return out
  
  def _structured_property_field_format(self, fields, values, path):
    _state = allowed_state(values.get('_state'))
    _sequence = values.get('_sequence')
    key = values.get('key')
    for value_key, value in values.items():
      field = fields.get(value_key)
      if field:
        if hasattr(field, 'value_format'):
          new_path = '%s.%s' % (path, field._code_name)
          try:
            if hasattr(field, '_structured_property_field_format'):
              val = field.value_format(value, new_path)
            else:
              val = field.value_format(value)
          except FormatError as e:
            if isinstance(e.message, dict):
              for k, v in e.message.iteritems():
                if k not in errors:
                  errors[k] = []
                if isinstance(v, (list, tuple)):
                  errors[k].extend(v)
                else:
                  errors[k].append(v)
            else:
              if e.message not in errors:
                errors[e.message] = []
              errors[e.message].append(new_path)
            continue
          if val is util.Nonexistent:
            del values[value_key]
          else:
            values[value_key] = val
        else:
          del values[value_key]
      else:
        del values[value_key]
    if key:
      values['key'] = Key(urlsafe=key)
    values['_state'] = _state  # Always keep track of _state for rule engine!
    if _sequence is not None:
      values['_sequence'] = _sequence
  
  def _structured_property_format(self, entity_as_dict, path):
    provided_kind_id = entity_as_dict.get('kind')
    fields = self.get_model_fields(kind=provided_kind_id)
    entity_as_dict.pop('class_', None)  # Never allow class_ or any read-only property to be set for that matter.
    try:
      self._structured_property_field_format(fields, entity_as_dict, path)
    except FormatError as e:
      raise FormatError(e.message)
    modelclass = self.get_modelclass(kind=provided_kind_id)
    return modelclass(**entity_as_dict)
  
  def get_modelclass(self, kind):
    if self._kinds and kind:
      if kind:
        _kinds = []
        for other in self._kinds:
          if isinstance(other, Model):
            _the_kind = other.get_kind()
          else:
            _the_kind = other
          _kinds.append(_the_kind)
        if kind not in _kinds:
          raise ValueError('Expected Kind to be one of %s, got %s' % (kind, _kinds))
        model = Model._kind_map.get(kind)
        return model
  
  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()
  
  def get_meta(self):
    out = super(SuperPluginStorageProperty, self).get_meta()
    out['kinds'] = self._kinds
    return out
  
  def property_keywords_format(self, kwds, skip_kwds):
    super(SuperPluginStorageProperty, self).property_keywords_format(kwds, skip_kwds)
    if 'kinds' not in skip_kwds:
      kwds['kinds'] = map(lambda x: unicode(x), kwds['kinds'])
