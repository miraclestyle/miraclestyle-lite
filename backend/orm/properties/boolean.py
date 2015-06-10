# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from .base import *
from .base import _BaseProperty

__all__ = ['SuperBooleanProperty']

class SuperBooleanProperty(_BaseProperty, BooleanProperty):
  
  def value_format(self, value):
    value = self._property_value_format(value)
    if value is tools.Nonexistent:
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