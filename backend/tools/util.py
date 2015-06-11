# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import sys
import logging
import string
import random
import dis
import pdb

from decimal import Decimal, ROUND_HALF_EVEN

import settings
import errors

# @todo __all__ is needed for everything that gets wildcard imported

__all__ = ['UnitConversionError', 'UnitRoundingError', 'UnitFormatError', 'SafeEvalError', 'Nonexistent',
           'remove_value', 'prepare_attr', 'set_attr', 'del_attr', 'get_attr', 'get_meta', 'normalize',
           'sort_by_list', 'merge_dicts', 'override_dict', 'make_complete_name', 'safe_eval', 'random_chars',
           'partition_list', 'noop', 'debug', 'convert_value', 'log', 'round_value', 'format_value']


class UnitConversionError(errors.BaseKeyValueError):

  KEY = 'unit_convert_value'


class UnitRoundingError(errors.BaseKeyValueError):

  KEY = 'unit_round_value'


class UnitFormatError(errors.BaseKeyValueError):

  KEY = 'unit_format_value'


class SafeEvalError(errors.BaseKeyValueError):

  LOG = True

  KEY = 'safe_eval_error'


class Meaning(object):

  '''Class used to provide meaning for variables. E.g.:
  Nonexistent = Meaning('Represents something that does not exist in list, dict or whatever')
  if value is Nonexistent:
    do stuff

  '''

  def __init__(self, docstring=None):
    self.__doc__ = docstring

  def __repr__(self):
    return '<Meaning() => %s>' % self.__doc__


Nonexistent = Meaning(
    'Represents something that does not exist when built-in None cannot be used.')
# e.g. If not Nonexistent expression is always true.
Nonexistent.__nonzero__ = lambda self: False


def remove_value(values, target=None):
  '''By default it will remove None. This function will never return new list, it will always mutate it.

  '''
  delete_values = []
  if isinstance(values, list):
    for value in values:
      delete = False
      if callable(target):
        if value == target(value):
          delete = True
      else:
        if value == target:
          delete = True
      if delete:
        delete_values.append(value)
    for delete_value in delete_values:
      values.remove(delete_value)
  elif isinstance(values, dict):
    for key in values:
      delete = False
      value = values.get(key)
      if callable(target):
        if value == target(value):
          delete = True
      else:
        if value == target:
          delete = True
      if delete:
        delete_values.append(key)
    for delete_key in delete_values:
      del values[delete_key]


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
          return Nonexistent
      elif isinstance(entity, list):
        try:
          entity = entity[int(field)]
        except IndexError as e:
          return Nonexistent
      else:
        try:
          entity = getattr(entity, field)
        except ValueError as e:
          return Nonexistent
  return (entity, last_field)


def set_attr(entity, field_path, value):
  result = prepare_attr(entity, field_path)
  if result == Nonexistent:
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


def del_attr(entity, field_path):
  result = prepare_attr(entity, field_path)
  if result == Nonexistent:
    return None
  entity, last_field = result
  if isinstance(entity, dict):
    del entity[last_field]
  elif isinstance(entity, list):
    try:
      del entity[int(last_field)]
    except:
      return None
  else:
    delattr(entity, last_field)


def get_attr(entity, field_path, default_value=None):
  result = prepare_attr(entity, field_path)
  if result == Nonexistent:
    return default_value
  entity, last_field = result
  if isinstance(entity, dict):
    return entity.get(last_field, default_value)
  elif isinstance(entity, list):
    try:
      return entity[int(last_field)]
    except:
      return default_value
  else:
    return getattr(entity, last_field, default_value)


def get_meta(entity, field_path):
  result = prepare_attr(entity, field_path)
  if result == Nonexistent:
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
    return [item for key, item in source.iteritems()]
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


def merge_dicts(a, b):
  '''
   Merges dict b into a maintaining values of a intact.
    >>> stuff = {'1' : 'yes'}
    >>> stuff2 = {'1' : 'no', 'other' : 1}
    >>> merge_dicts(stuff, stuff2)
    >>> {'1': 'yes', 'other': 1}
  '''
  current_a = a
  current_b = b
  next_args = []
  while True:
    if current_b is None:
      try:
        current_a, current_b = next_args.pop()
        continue
      except IndexError as e:
        break
    for key in current_b:
      if key in current_a:
        if isinstance(current_a[key], dict) and isinstance(current_b[key], dict):
          next_args.append((current_a[key], current_b[key]))
        elif current_a[key] == current_b[key]:
          pass
        else:
          # in this segment we encounter that a[key] is not equal to
          # b[key] which we do not want
          pass
      else:
        current_a[key] = current_b[key]
    current_a = None
    current_b = None
  return a


def override_dict(a, b):
  current_a = a
  current_b = b
  next_args = []
  while True:
    if current_b is None:
      try:
        current_a, current_b = next_args.pop()
        continue
      except IndexError as e:
        break
    for key in current_b:
      if key in current_a:
        if isinstance(current_a[key], dict) and isinstance(current_b[key], dict):
          next_args.append((current_a[key], current_b[key]))
        elif current_a[key] == current_b[key]:
          pass
        else:
          # in this segment we encounter that a[key] is not equal to
          # b[key] which we do not want, roll it back
          current_a[key] = current_b[key]
      else:
        current_a[key] = current_b[key]
    current_a = None
    current_b = None
  return a


def make_complete_name(entity, name_property, parent_property=None, separator=None):
  '''Returns a string build by joining individual string values,
  extracted from the same property traced in a chain of interrelated entities.

  '''
  if separator is None:
    separator = unicode(' / ')
  path = entity
  names = []
  while True:
    parent = None
    if parent_property is None:
      parent_key = path.key.parent()
      parent = parent_key.get()
    else:
      parent_key = getattr(path, parent_property)
      if parent_key:
        parent = parent_key.get()
    if not parent:
      names.append(getattr(path, name_property))
      break
    else:
      names.append(getattr(path, name_property))
      path = parent
  names.reverse()
  return separator.join(names)


_CODES = ['POP_TOP', 'ROT_TWO', 'ROT_THREE', 'ROT_FOUR', 'DUP_TOP', 'BUILD_LIST',
          'BUILD_MAP', 'BUILD_TUPLE', 'LOAD_CONST', 'RETURN_VALUE',
          'STORE_SUBSCR', 'UNARY_POSITIVE', 'UNARY_NEGATIVE', 'UNARY_NOT',
          'UNARY_INVERT', 'BINARY_POWER', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
          'BINARY_FLOOR_DIVIDE', 'BINARY_TRUE_DIVIDE', 'BINARY_MODULO',
          'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_LSHIFT', 'BINARY_RSHIFT',
          'BINARY_AND', 'BINARY_XOR', 'BINARY_OR', 'STORE_MAP', 'LOAD_NAME',
          'COMPARE_OP', 'LOAD_ATTR', 'STORE_NAME', 'GET_ITER',
          'FOR_ITER', 'LIST_APPEND', 'JUMP_ABSOLUTE', 'DELETE_NAME',
          'JUMP_IF_TRUE', 'JUMP_IF_FALSE', 'JUMP_IF_FALSE_OR_POP',
          'JUMP_IF_TRUE_OR_POP', 'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
          'BINARY_SUBSCR', 'JUMP_FORWARD']


_ALLOWED_CODES = set(dis.opmap[x] for x in _CODES if x in dis.opmap)


def _compile_source(source):
  comp = compile(source, '', 'eval')
  codes = []
  co_code = comp.co_code
  i = 0
  while i < len(co_code):
    code = ord(co_code[i])
    codes.append(code)
    if code >= dis.HAVE_ARGUMENT:
      i += 3
    else:
      i += 1
  for code in codes:
    if code not in _ALLOWED_CODES:
      raise ValueError('opcode %s not allowed' % dis.opname[code])
  return comp


def safe_eval(source, data=None):
  if '__subclasses__' in source:
    raise SafeEvalError('__subclasses__ not allowed')
  comp = _compile_source(source)
  try:
    return eval(comp, {'__builtins__': {'True': True, 'False': False, 'str': str,
                                        'globals': locals, 'locals': locals, 'bool': bool,
                                        'dict': dict, 'round': round, 'Decimal': Decimal}}, data)
  except Exception as e:
    raise SafeEvalError(
        'Failed to process code: "%s" ---- error was: %s' % (source, e))


def random_chars(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
  return ''.join(random.choice(chars) for x in xrange(size))


def partition_list(complete_list, partition_length):
  '''Returns iterator of provided list in chunks of length by n.
  E.g.
  >>>items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
  >>>list(partition_list(items, 5))
  >>>[[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11]]

  '''
  for i in xrange(0, len(complete_list), partition_length):
    yield complete_list[i:i + partition_length]


def noop(*args, **kwargs):
  pass


class LoggingWrapper(object):

  def __getattr__(self, name, default=None):
    if name and name.startswith('_'):
      return super(LoggingWrapper, self).__getattr__(self, name, default)
    if settings.DO_LOGS:
      logger = getattr(logging, name)
      if name == 'exception':
        def decide(exc):
          if hasattr(exc, 'LOG'):
            if exc.LOG:
              return logger
            else:
              return noop
          # always log exceptions that do not have `LOG` constant
          return logger
        return decide
      return logger
    else:
      return noop

log = LoggingWrapper()


def debug():
  """ Enter pdb in App Engine

  Renable system streams for it.
  """
  pdb.Pdb(stdin=getattr(sys, '__stdin__'), stdout=getattr(
      sys, '__stderr__')).set_trace(sys._getframe().f_back)


########## Unit manipulation functions! ##########


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


def round_value(value, uom, rounding=ROUND_HALF_EVEN):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(uom, 'rounding') or not isinstance(uom.rounding, Decimal):
    raise UnitRoundingError('no_rounding_in_uom')
  return (value / uom.rounding).quantize(Decimal('1.'), rounding=rounding) * uom.rounding


def format_value(value, uom, rounding=ROUND_HALF_EVEN):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(uom, 'digits') or not isinstance(uom.digits, (int, long)):
    raise UnitFormatError('no_digits_in_uom, got %s' % uom)
  places = Decimal(10) ** -uom.digits
  return value.quantize(places, rounding=rounding)
