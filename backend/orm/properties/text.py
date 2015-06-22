# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from .base import *
from .base import _BaseProperty

__all__ = ['SuperTextProperty', 'SuperStringProperty']


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
