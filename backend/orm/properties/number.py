# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import decimal

from .base import *
from .base import _BaseProperty
from .text import SuperStringProperty

__all__ = ['SuperDecimalProperty', 'SuperFloatProperty', 'SuperIntegerProperty']


class SuperFloatProperty(_BaseProperty, FloatProperty):

  def _convert_value(self, value):
    if self._repeated:
      return [float(v) for v in value]
    else:
      return float(value)

  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      return search.NumberField(name=self.search_document_field_name, value=value)


class SuperIntegerProperty(_BaseProperty, IntegerProperty):

  def _convert_value(self, value):
    if self._repeated:
      return [long(v) for v in value]
    else:
      return long(value)

  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: str(v), value))
      return search.TextField(name=self.search_document_field_name, value=value)
    else:
      return search.NumberField(name=self.search_document_field_name, value=value)


class SuperDecimalProperty(SuperStringProperty):

  '''Decimal property that accepts only decimal.Decimal.'''

  def _convert_value(self, value):
    if self._repeated:
      i = 0
      try:
        out = []
        for i, v in enumerate(value):
          out.append(decimal.Decimal(v))
      except:
        raise FormatError('invalid_number_on_sequence_%s' % i)
    else:
      try:
        out = decimal.Decimal(value)
      except:
        raise FormatError('invalid_number')
    if out is None:
      raise FormatError('invalid_number')
    return out

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
