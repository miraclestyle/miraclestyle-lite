# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import cgi
import copy

import cloudstorage
from google.appengine.ext import blobstore
from google.appengine.api import images, urlfetch

from ..base import *
import tools
import settings


class FormatError(Exception):
  pass


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
  def can_be_none(self):  # checks if the property can be set to None
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

  def _property_value_validate(self, value):
    if value is None and self._required:
      raise FormatError('required')
    if self._max_size and value is not None:
      if len(value) > self._max_size:
        raise FormatError('max_size_exceeded')
    if hasattr(self, '_choices') and self._choices:
      if value not in self._choices:
        raise FormatError('not_in_specified_choices')

  def _property_value_filter(self, value):
    if self._value_filters:
      value_filters = self._value_filters
      if not isinstance(value_filters, (list, tuple)):
        value_filters = [value_filters]
      for value_filter in value_filters:
        value = value_filter(self, value)
    return value

  def _property_value_format(self, value):
    if value is tools.Nonexistent:
      if self._default is not None:
        value = copy.deepcopy(self._default)
      elif self._required:
        raise FormatError('required')
      else:
        return value  # Returns tools.Nonexistent
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

  def _convert_value(self, value, **kwargs):
    return value

  def value_format(self, value, **kwargs):
    value = self._property_value_format(value)
    if value is tools.Nonexistent:
      return value
    if value is None:
      return value
    return self._convert_value(value, **kwargs)

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
  _value_class = None

  def __init__(self, *args, **kwargs):
    args = list(args)
    self._readable = kwargs.pop('readable', self._readable)
    self._updateable = kwargs.pop('updateable', self._updateable)
    self._deleteable = kwargs.pop('deleteable', self._deleteable)
    self._autoload = kwargs.pop('autoload', self._autoload)
    self._addable = kwargs.pop('addable', self._addable)
    self._format_callback = kwargs.pop(
        'format_callback', self._format_callback)
    self._read_arguments = kwargs.pop('read_arguments', {})
    self._duplicable = kwargs.pop('duplicable', self._duplicable)
    # this is because storage structured property does not need the logic below
    if not kwargs.pop('generic', None):
      if isinstance(args[0], basestring):
        set_arg = Model._kind_map.get(args[0])
        # if model is not scanned yet, do not set it to none
        if set_arg is not None:
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
      self._modelclass = Model._lookup_model(self._modelclass)
    return self._modelclass

  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    '''
    dic = super(_BaseStructuredProperty, self).get_meta()
    dic['modelclass'] = self.get_modelclass().get_fields()
    dic['modelclass_kind'] = self.get_modelclass().get_kind()
    dic['value_class'] = self._value_class.__name__
    dic['autoload'] = self._autoload
    dic['readable'] = self._readable
    dic['updateable'] = self._updateable
    dic['deleteable'] = self._deleteable
    dic['read_arguments'] = self._read_arguments
    return dic

  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()

  def _convert_value(self, value, path=None):
    if path is None:
      path = self._code_name
    current_value = value
    out = []
    if not self._repeated:
      if not isinstance(value, dict) and not self._required:
        return tools.Nonexistent
      value = [value]
    elif current_value is None:
      return tools.Nonexistent
    for v in value:
      entity = self._structured_property_format(v, path)
      out.append(entity)
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
    property_value = self._get_value(entity)
    if self._repeated:
      if property_value.has_value():
        if property_value.value:
          current_value = property_value.value
        else:
          current_value = []
        if value:
          for v in value:
            generate = True
            if v.key:
              for current_v in current_value:
                if current_v.key == v.key:
                  current_v.populate_from(v)
                  generate = False
                  break
            if generate:
              if not v.key:
                v.generate_unique_key()
                if v._state is None:
                  v._state = 'created'
              current_value.append(v)
          current_value.sort(key=lambda x: x._sequence, reverse=True)
      else:
        current_value = value
        if current_value is None:
          current_value = []
        else:
          for current_v in current_value:
            if not current_v.key:
              current_v.generate_unique_key()
              if current_v._state is None:
                current_v._state = 'created'
    else:
      if value is not None:
        current_value = property_value.value
        if current_value is not None:
          current_value.populate_from(value)
        else:
          current_value = value
          if not current_value.key:
            current_value.generate_unique_key()
      else:
        current_value = value
    property_value.set(current_value)
    return super(_BaseStructuredProperty, self)._set_value(entity, current_value)

  def _delete_value(self, entity):
    # __delete__
    property_value = self._get_value(entity)
    property_value.delete()

  def _get_value(self, entity):
    # __get__
    super(_BaseStructuredProperty, self)._get_value(entity)
    value_name = '%s_value' % self._name
    if value_name in entity._values:
      property_value = entity._values[value_name]
    else:
      property_value = self._value_class(property_instance=self, entity=entity)
      entity._values[value_name] = property_value
    return property_value

  def _structured_property_field_format(self, fields, values, path):
    _state = allowed_state(values.get('_state'))
    _sequence = values.get('_sequence')
    key = values.get('key')
    kind = values.get('kind')
    errors = {}
    for current_value_key, current_value in values.items():
      field = fields.get(current_value_key)
      if field:
        if hasattr(field, 'value_format'):
          new_path = '%s.%s' % (path, field._code_name)
          try:
            if hasattr(field, '_structured_property_field_format'):
              value = field.value_format(current_value, path=new_path)
            else:
              value = field.value_format(current_value)
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
          if value is tools.Nonexistent:
            del values[current_value_key]
          else:
            values[current_value_key] = value
        else:
          del values[current_value_key]
      else:
        del values[current_value_key]
    if len(errors):
      raise FormatError(errors)
    if key:
      values['key'] = BaseVirtualKeyProperty(kind=kind, required=True).value_format(key)
    values['_state'] = _state  # Always keep track of _state for rule engine!
    if _sequence is not None:
      values['_sequence'] = _sequence

  def _structured_property_format(self, values, path):
    kind = values.get('kind')
    fields = self.get_model_fields(kind=kind)
    # Never allow class_ or any read-only property to be set for that matter.
    values.pop('class_', None)
    try:
      self._structured_property_field_format(fields, values, path)
    except FormatError as e:
      raise FormatError(e.message)
    modelclass = self.get_modelclass(kind=kind)
    return modelclass(**values)

  @property
  def is_structured(self):
    return True

  def initialize(self):
    # Enforce premature loading of lazy-set model logic to prevent errors.
    self.get_modelclass()

  def _prepare_for_put(self, entity):
    property_value = self._get_value(entity)  # For its side effects.
    if property_value.value is None and self._repeated:
      property_value.set([])
    super(_BaseStructuredProperty, self)._prepare_for_put(entity)


class BaseProperty(_BaseProperty, Property):

  '''Base property class for all properties capable of having _max_size option.'''


class BaseKeyProperty(_BaseProperty, KeyProperty):

  '''This property is used on models to reference ndb.Key property.
  Its format function will convert urlsafe string into a ndb.Key and check if the key
  exists in the datastore. If the key does not exist, it will throw an error.
  If key existence feature isn't required, SuperVirtualKeyProperty() can be used in exchange.

  '''

  def value_format(self, value, skip_get=False):
    try:
      value = self._property_value_format(value)
      if value is tools.Nonexistent:
        return value
      if not self._repeated and not self._required and (value is None or len(value) < 1):
        # if key is not required, and value is either none or length is not
        # larger than 1, its considered as none
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
        for entity in entities:
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
        raise FormatError('not_found')  # if its not found, its not found
      # Failed to build from urlsafe, proceed with KeyFromPath.
      value = self._property_value_format(value)
      if value is tools.Nonexistent:
        return value
      out = []
      if self._repeated:
        for v in value:
          kwds = {}
          try:
            kwds = v[1]
          except IndexError:
            pass
          key = Key(*v[0], **kwds)
          if self._kind and key.kind() != self._kind:
            raise FormatError('invalid_kind')
          out.append(key)
        if not skip_get:
          entities = get_multi(out)
          for entity in entities:
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
    return super(BaseKeyProperty, self).resolve_search_document_field(value)

  def get_meta(self):
    dic = super(BaseKeyProperty, self).get_meta()
    dic['kind'] = self._kind
    return dic


class BaseVirtualKeyProperty(BaseKeyProperty):

  '''This property is exact as SuperKeyProperty, except its format function is not making any calls
  to the datastore to check the existence of the provided urlsafe key. It will simply format the
  provided urlsafe key into a ndb.Key.

  '''

  def value_format(self, value):
    return super(BaseVirtualKeyProperty, self).value_format(value, skip_get=True)


class BaseBlobKeyProperty(_BaseProperty, BlobKeyProperty):

  def _convert_value(self, value):
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


class _BaseBlobProperty(object):

  '''Base helper class for blob-key-like orm properties.
  This property should be used in conjunction with orm Property baseclass, like so:
  class PDF(BaseBlobKeyInterface, Property):
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
    blobs = tools.mem_temp_get(settings.BLOBKEYMANAGER_KEY, None)
    if blobs is None:
      tools.mem_temp_set(settings.BLOBKEYMANAGER_KEY, {'delete': []})
    blobs = tools.mem_temp_get(settings.BLOBKEYMANAGER_KEY)
    return blobs

  @classmethod
  def _update_blobs(cls, update_blobs, state=None, delete=True):
    update_blobs = tools.normalize(update_blobs)
    blobs = cls.get_blobs()
    for blob in update_blobs:
      if state not in blobs:
        blobs[state] = []
      if blob not in blobs[state]:
        blobs[state].append(blob)
    if state is not None and not state.startswith('delete') and delete is True:
      # If state is said to be delete_* or delete then there is no need to
      # store them in delete queue.
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
    cls._update_blobs(blobs, 'save', delete)

  @classmethod
  def save_blobs_on_error(cls, blobs, delete=True):
    # Marks blobs to be preserved upon application error.
    cls._update_blobs(blobs, 'save_error', delete)

  @classmethod
  def save_blobs_on_success(cls, blobs, delete=True):
    # Marks blobs to be preserved upon success.
    cls._update_blobs(blobs, 'save_success', delete)


class _BaseImageProperty(_BaseBlobProperty):

  '''Base helper class for image-like properties.
  This class should work in conjunction with Property, because it does not implement anything of
  Example:
  class NewImageProperty(_BaseImageProperty, Property):
  ...
  '''

  def __init__(self, *args, **kwargs):
    self._process_config = kwargs.pop('process_config', {})
    self._upload = kwargs.pop('upload', False)
    super(_BaseImageProperty, self).__init__(*args, **kwargs)

  def generate_serving_urls(self, values):
    @tasklet
    def generate(value):
      if value.serving_url is None:
        value.serving_url = yield images.get_serving_url_async(value.image)
      raise Return(True)

    @tasklet
    def mapper(values):
      yield map(generate, values)
      raise Return(True)

    mapper(values).get_result()

  def generate_measurements(self, values):
    ctx = get_context()

    @tasklet
    def measure(value):
      if value.proportion is None:
        pause = 0.5
        for i in xrange(4):
          try:
            # http://stackoverflow.com/q/14944317/376238
            fetched_image = yield ctx.urlfetch('%s=s100' % value.serving_url)
            break
          except Exception as e:
            time.sleep(pause)
            pause = pause * 2
        image = images.Image(image_data=fetched_image.content)
        value.proportion = float(image.width) / float(image.height)
        raise Return(True)

    @tasklet
    def mapper(values):
      yield map(measure, values)
      raise Return(True)

    mapper(values).get_result()

  def process(self, values):
    ''' @note
    This method is primarily used for images' transformation and copying.
    '''
    @tasklet
    def process_image(value, i, values):
      config = self._process_config
      new_value = value
      gs_object_name = new_value.gs_object_name
      new_gs_object_name = new_value.gs_object_name
      if config.get('copy'):
        new_value = copy.deepcopy(value)
        new_gs_object_name = '%s_%s' % (
            new_value.gs_object_name, config.get('copy_name'))
      blob_key = None
      # @note No try block is implemented here. This code is no longer forgiving.
      # If any of the images fail to process, everything is lost/reverted, because one or more images:
      # - are no longer existant in the cloudstorage / .read();
      # - are not valid / not image exception;
      # - failed to resize / resize could not be done;
      # - failed to create gs key / blobstore failed for some reason;
      # - failed to create get_serving_url / serving url service failed for some reason;
      # - failed to write to cloudstorage / cloudstorage failed for some reason.
      if settings.DEVELOPMENT_SERVER:
        blob = urlfetch.fetch(
            '%s/_ah/gcs%s' % (settings.HOST_URL, gs_object_name[3:]))
        blob = blob.content
      else:
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
      writable_blob = cloudstorage.open(
          new_gs_object_name[3:], 'w', content_type=new_value.content_type)
      writable_blob.write(blob)
      writable_blob.close()
      if gs_object_name != new_gs_object_name:
        new_value.gs_object_name = new_gs_object_name
        blob_key = yield blobstore.create_gs_key_async(new_gs_object_name)
        new_value.image = blobstore.BlobKey(blob_key)
        new_value.serving_url = None
      values[i] = new_value
      raise Return(True)

    @tasklet
    def mapper(values):
      for i, v in enumerate(values):
        yield process_image(v, i, values)
      raise Return(True)

    single = False
    if not isinstance(values, list):
      values = [values]
      single = True
    mapper(values).get_result()
    self.generate_serving_urls(values)
    if single:
      values = values[0]
    return values

  def _convert_value(self, value, path=None):
    if path is None:
      path = self._code_name
    if not self._repeated:
      value = [value]
    out = []
    total = len(value) - 1
    for i, v in enumerate(value):
      if not self._upload:
        if not isinstance(v, dict) and not self._required:
          continue
        out.append(self._structured_property_format(v, path))
      else:
        if not isinstance(v, cgi.FieldStorage):
          if self._required:
            raise FormatError('invalid_input')
          else:
            continue
        # These will throw errors if the 'v' is not cgi.FileStorage and it does
        # not have compatible blob-key.
        file_info = blobstore.parse_file_info(v)
        blob_info = blobstore.parse_blob_info(v)
        # We only accept jpg/png. This list can be and should be customizable
        # on the property option itself?
        if file_info.content_type not in ('image/jpeg', 'image/jpg', 'image/png'):
          # First line of validation based on meta data from client.
          raise FormatError('invalid_image_type')
        new_image = self.get_modelclass()(**{'size': file_info.size,
                                             'content_type': file_info.content_type,
                                             'gs_object_name': file_info.gs_object_name,
                                             'image': blob_info.key(),
                                             '_sequence': total - i})
        out.append(new_image)
    if not out:
      # if field is not required, and there isnt any processed return non
      # existent
      if not self._required:
        return tools.Nonexistent
      else:
        raise FormatError('required')  # otherwise required
    if self._upload:
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
