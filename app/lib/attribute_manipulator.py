# -*- coding: utf-8 -*-
'''
Created on Apr 24, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

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
