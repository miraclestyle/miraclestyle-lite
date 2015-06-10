# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from .base import *
from .base import _BaseProperty

__all__ = ['SuperTextProperty', 'SuperStringProperty']

class SuperTextProperty(_BaseProperty, TextProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is tools.Nonexistent:
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
    if value is tools.Nonexistent:
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
