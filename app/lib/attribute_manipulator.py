# -*- coding: utf-8 -*-
'''
Created on Apr 24, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

def prepare_attr(entity, field_path):
  fields = field_path.split('.')
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
        except KeyError as e:
          return None
      else:
        try:
          entity = getattr(entity, field)
        except ValueError as e:
          return None
  return (entity, last_field)

def set_attr(entity, field_path, value):
  entity, last_field = prepare_attr(entity, field_path)
  if isinstance(entity, dict):
    entity[last_field] = value
  elif isinstance(entity, list):
    entity[int(last_field)] = value
  else:
    setattr(entity, last_field, value)

def get_attr(entity, field_path):
  entity, last_field = prepare_attr(entity, field_path)
  if isinstance(entity, dict):
    return entity.get(last_field)
  elif isinstance(entity, list):
    return entity[int(last_field)]
  else:
    return getattr(entity, last_field)

def get_meta(entity, field_path):
  entity, last_field = prepare_attr(entity, field_path)
  if not isinstance(entity, dict) and not isinstance(entity, list):
    return getattr(entity.__class__, last_field)
