# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from .base import *
from .base import _BaseProperty

__all__ = ['SuperTextProperty', 'SuperStringProperty', 'SuperStringEncryptedProperty']


class SuperTextProperty(_BaseProperty, TextProperty):

  def _convert_value(self, value):
    if self._repeated:
      out = []
      for v in value:
        if v is not None:
          out.append(unicode(v))
    else:
      if value is not None:
        out = unicode(value)
      else:
        out = None
    return out

  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(value)
    return search.HtmlField(name=self.search_document_field_name, value=value)


class SuperStringProperty(_BaseProperty, StringProperty):

  def _convert_value(self, value):
    if self._repeated:
      out = []
      for v in value:
        if v is not None:
          out.append(unicode(v))
    else:
      if value is not None:
        out = unicode(value)
      else:
        out = None
    return out

  def get_search_document_field(self, value):
    if self._repeated:
      value = unicode(' ').join(value)
    return search.TextField(name=self.search_document_field_name, value=unicode(value))


class EncryptedValue():

  def __init__(self, field, raw):
    self.set(raw)
    self.field = field

  def set(self, raw):
    self.encrypted = raw
    self.decrypted = tools.urlsafe_decrypt(self.encrypted)

  def __deepcopy__(self, memo):
    return self.decrypted

  def __str__(self):
    return self.field._placeholder

  def __unicode__(self):
    return self.field._placeholder

  def __repr__(self):
    return self.field._placeholder

  def get_output(self):
    return self.field._placeholder


class SuperStringEncryptedProperty(SuperStringProperty):

  """
    Field for encrypting string values
    class Ent(Model):
       foobar = SuperStringEncryptedProperty()
    entity = Entity(foobar=1, foobar=2)
    entity.foobar => yields EncryptedValue instance that has two properties
    entity.foobar.encrypted => output
    entity.foobar.decrypted => programming interface e.g. Charge.create() whatnot
  """

  def __init__(self, *args, **kwargs):
    self._placeholder = kwargs.pop('placeholder', None)
    if not isinstance(self._placeholder, str):
      raise Exception('Placeholder must be string')
    super(SuperStringEncryptedProperty, self).__init__(*args, **kwargs)

  def _to_base_type(self, value):
    if isinstance(value, EncryptedValue):
      value = value.encrypted # this is to avoid the constant rehashing, encrypt function knows if it should do that
    return tools.urlsafe_encrypt(value)

  def _from_base_type(self, value):
    return EncryptedValue(self, value)

  def _set_value(self, entity, value):
    # __set__
    encrypted_value = tools.urlsafe_encrypt(value)
    property_value = self._get_value(entity)
    property_value.set(encrypted_value)
    super(SuperStringEncryptedProperty, self)._set_value(entity, encrypted_value)

  def _get_value(self, entity):
    # __get__
    get = super(SuperStringEncryptedProperty, self)._get_value(entity)
    value_name = '%s_decrypted_value' % self._name
    if value_name in entity._values:
      property_value = entity._values[value_name]
    else:
      if not isinstance(get, EncryptedValue):
        property_value = EncryptedValue(self, get)
      else:
        property_value = get
      entity._values[value_name] = property_value
    return property_value
