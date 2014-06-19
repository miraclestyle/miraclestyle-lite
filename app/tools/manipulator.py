# -*- coding: utf-8 -*-
'''
Created on Apr 24, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from decimal import Decimal, ROUND_HALF_EVEN


def prepare_attr(entity, field_path):
  fields = str(field_path).split('.')
  last_field = fields[-1]
  drill = fields[:-1]
  i = -1
  while not last_field:
    i = i - 1
    last_field = fields[i]
    drill = fields[:i]
  for field in drill:
    if field:
      if isinstance(entity, dict):
        try:
          entity = entity[field]
        except KeyError as e:
          return None
      elif isinstance(entity, list):
        try:
          entity = entity[int(field)]
        except IndexError as e:
          return None
      else:
        try:
          entity = getattr(entity, field)
        except ValueError as e:
          return None
  return (entity, last_field)


def set_attr(entity, field_path, value):
  result = prepare_attr(entity, field_path)
  if result == None:
    return None
  entity, last_field = result
  if isinstance(entity, dict):
    entity[last_field] = value
  elif isinstance(entity, list):
    try:
      entity[int(last_field)] = value
    except:
      return None
  else:
    setattr(entity, last_field, value)


def get_attr(entity, field_path):
  result = prepare_attr(entity, field_path)
  if result == None:
    return None
  entity, last_field = result
  if isinstance(entity, dict):
    return entity.get(last_field, None)
  elif isinstance(entity, list):
    try:
      return entity[int(last_field)]
    except:
      return None
  else:
    return getattr(entity, last_field, None)


def get_meta(entity, field_path):
  result = prepare_attr(entity, field_path)
  if result == None:
    return None
  entity, last_field = result
  if not isinstance(entity, dict) and not isinstance(entity, list):
    return getattr(entity.__class__, last_field)


def normalize(source):
  if isinstance(source, list):
    return source
  if isinstance(source, tuple):
    return list(source)
  if isinstance(source, basestring):
    return [source]
  if isinstance(source, dict):
    return [item for key, item in source.items()]
  try:
    items = iter(source)
    return [item for item in items]
  except ValueError as e:
    pass
  finally:
    return [source]


def sort_by_list(unsorted_list, sorting_list, field):
  total = len(unsorted_list) + 1
  to_delete = []
  def sorting_function(item):
    try:
      ii = sorting_list.index(get_attr(item, field)) + 1
    except ValueError as e:
      to_delete.append(item)
      ii = total
    return ii
  return (sorted(unsorted_list, key=sorting_function), to_delete)


########## Unit manipulation functions! ##########


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
