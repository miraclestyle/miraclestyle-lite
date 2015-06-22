# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import datetime

from .base import *
from .base import _BaseProperty
import settings

__all__ = ['SuperDateTimeProperty']


class SuperDateTimeProperty(_BaseProperty, DateTimeProperty):

  @property
  def can_be_none(self):
    field = self
    if ((field._auto_now or field._auto_now_add) and field._required):
      return False
    return True

  def value_format(self, value):
    value = self._property_value_format(value)
    if value is tools.Nonexistent:
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
