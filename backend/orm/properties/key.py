# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from .base import *
from .values import *

__all__ = ['SuperKeyProperty', 'SuperVirtualKeyProperty', 'SuperBlobKeyProperty', 'SuperReferenceProperty']


class SuperKeyProperty(BaseKeyProperty):
  pass


class SuperVirtualKeyProperty(BaseVirtualKeyProperty):
  pass


class SuperBlobKeyProperty(BaseBlobKeyProperty):
  pass


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
    if self._callback is not None and not callable(self._callback):
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
    return tools.Nonexistent
