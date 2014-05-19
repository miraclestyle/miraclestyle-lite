# -*- coding: utf-8 -*-
'''
Created on May 19, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from decimal import Decimal, ROUND_HALF_EVEN


def convert_value(value, value_uom, conversion_uom):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(value_uom, 'measurement'):
    raise Exception('no_measurement_in_value_uom')
  if not hasattr(conversion_uom, 'measurement'):
    raise Exception('no_measurement_in_conversion_uom')
  if not hasattr(value_uom, 'rate') or not isinstance(value_uom.rate, Decimal):
    raise Exception('no_rate_in_value_uom')
  if not hasattr(conversion_uom, 'rate') or not isinstance(conversion_uom.rate, Decimal):
    raise Exception('no_rate_in_conversion_uom')
  if (value_uom.measurement == conversion_uom.measurement):
    return (value / value_uom.rate) * conversion_uom.rate
  else:
    raise Exception('incompatible_units')

def round_value(value, uom, rounding=ROUND_HALF_EVEN):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(uom, 'rounding') or not isinstance(uom.rounding, Decimal):
    raise Exception('no_rounding_in_uom')
  return (value / uom.rounding).quantize(Decimal('1.'), rounding=rounding) * uom.rounding

def format_value(value, uom, rounding=ROUND_HALF_EVEN):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(uom, 'digits') or not isinstance(uom.digits, (int, long)):
    raise Exception('no_digits_in_uom')
  places = Decimal(10) ** -uom.digits
  return (value).quantize(places, rounding=rounding)
