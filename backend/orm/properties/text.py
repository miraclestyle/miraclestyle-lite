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

  def __init__(self, raw):
    self.encrypted = raw
    self.decrypted = tools.urlsafe_decrypt(self.encrypted)

  def __deepcopy__(self, memo):
    return EncryptedValue(self.encrypted)

  def __str__(self):
    return self.encrypted

  def __unicode__(self):
    return self.encrypted

  def __repr__(self):
    return self.encrypted

  def get_output(self):
    return self.encrypted # always return encrypted values to the public, because setattr of our system overrides all


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

  def _to_base_type(self, value):
    if isinstance(value, EncryptedValue):
      value = value.encrypted # this is to avoid the constant rehashing, encrypt function knows if it should do that
    return tools.urlsafe_encrypt(value)

  def _from_base_type(self, value):
    return EncryptedValue(value)
