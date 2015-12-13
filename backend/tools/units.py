# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP

import errors

__all__ = ['UnitConversionError', 'UnitRoundingError', 'UnitFormatError',
           'convert_value', 'round_value', 'format_value']


class UnitConversionError(errors.BaseKeyValueError):

  KEY = 'unit_convert_value'


class UnitRoundingError(errors.BaseKeyValueError):

  KEY = 'unit_round_value'


class UnitFormatError(errors.BaseKeyValueError):

  KEY = 'unit_format_value'


def convert_value(value, value_uom, conversion_uom):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(value_uom, 'measurement'):
    raise UnitConversionError('no_measurement_in_value_uom')
  if not hasattr(conversion_uom, 'measurement'):
    raise UnitConversionError('no_measurement_in_conversion_uom')
  if not hasattr(value_uom, 'rate') or not isinstance(value_uom.rate, Decimal):
    raise UnitConversionError('no_rate_in_value_uom')
  if not hasattr(conversion_uom, 'rate') or not isinstance(conversion_uom.rate, Decimal):
    raise UnitConversionError('no_rate_in_conversion_uom')
  if (value_uom.measurement == conversion_uom.measurement):
    return (value / value_uom.rate) * conversion_uom.rate
  else:
    raise UnitConversionError('incompatible_units')


def round_value(value, uom, rounding=ROUND_UP):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(uom, 'rounding') or not isinstance(uom.rounding, Decimal):
    raise UnitRoundingError('no_rounding_in_uom')
  return (value / uom.rounding).quantize(Decimal('1.'), rounding=rounding) * uom.rounding


def format_value(value, uom, rounding=ROUND_UP):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(uom, 'digits') or not isinstance(uom.digits, (int, long)):
    raise UnitFormatError('no_digits_in_uom, got %s' % uom)
  places = Decimal(10) ** -uom.digits
  return value.quantize(places, rounding=rounding)
