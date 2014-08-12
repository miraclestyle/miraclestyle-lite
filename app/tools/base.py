# -*- coding: utf-8 -*-
'''
Created on Jun 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import taskqueue
from google.appengine.ext import blobstore

from app import orm
from app.util import *


def rule_prepare(entities, skip_user_roles, strict, **kwargs):
  entities = normalize(entities)
  callbacks = []
  for entity in entities:
    if entity and isinstance(entity, orm.Model):
      global_permissions = []
      local_permissions = []
      if hasattr(entity, '_global_role') and entity._global_role.get_kind() == '67':
        global_permissions = entity._global_role.permissions
      if not skip_user_roles:
        user = kwargs.get('user')
        if user and not user._is_guest:
          domain_user_key = orm.Key('8', user.key_id_str, namespace=entity.key_namespace)
          domain_user = domain_user_key.get()
          clean_roles = False
          if domain_user and domain_user.state == 'accepted':
            roles = orm.get_multi(domain_user.roles)
            for role in roles:
              if role is None:
                clean_roles = True
              elif role.active:
                local_permissions.extend(role.permissions)
            if clean_roles:
              data = {'action_model': '8',
                      'action_key': 'clean_roles',
                      'key': domain_user.key.urlsafe()}
              callbacks.append(('callback', data))
      entity.rule_prepare(global_permissions, local_permissions, strict, **kwargs)
  callbacks = list(set(callbacks))
  for callback in callbacks:
    callback[1]['caller_user'] = kwargs.get('user').key_urlsafe
    callback[1]['caller_action'] = kwargs.get('action').key_urlsafe
  callback_exec('/task/io_engine_run', callbacks)  # @todo This has to be optimized!


def rule_exec(entity, action):
  if entity and hasattr(entity, '_action_permissions'):
    if not entity._action_permissions[action.key_urlsafe]['executable']:
      raise orm.ActionDenied(action)
  else:
    raise orm.ActionDenied(action)


def callback_exec(url, callbacks):
  callbacks = normalize(callbacks)
  queues = {}
  if orm.in_transaction():
    callbacks = callbacks[:5]
  if len(callbacks):
    for callback in callbacks:
      if callback and isinstance(callback, (list, tuple)) and len(callback) == 2:
        queue_name, data = callback
        if data:
          if queue_name not in queues:
            queues[queue_name] = []
          queues[queue_name].append(taskqueue.Task(url=url, payload=json.dumps(data)))
  if len(queues):
    for queue_name, tasks in queues.iteritems():
      queue = taskqueue.Queue(name=queue_name)
      queue.add(tasks, transactional=orm.in_transaction())


def blob_create_upload_url(upload_url, gs_bucket_name):
  return blobstore.create_upload_url(upload_url, gs_bucket_name=gs_bucket_name)


def entity_by_path(entity, target_field_path, key=None, found_at=None):
  target_field_paths = target_field_path.split('.')
  last_i = len(target_field_paths)-1
  do_entity = entity
  entities = []
  found = []
  def start(entity, target, last_i, i, entities, found):
    if isinstance(entity, list):
      out = []
      for ent in entity:
        out.append(start(ent, target, last_i, i, entities, found))
      return out
    else:
      root_entity = entity
      entity = getattr(entity, target)
      if isinstance(entity, orm.SuperPropertyManager):
        entity = entity.value
      if last_i == i:
        if isinstance(entity, list):
          for ent in entity:
            if (key == None or (ent.key == key)):
              entities.append(ent)
          found.append(entity)
        else:
          if (key == None or (entity.key == key)):
            entities.append(entity)
          found.append(root_entity)
      else:
        return entity
  for i,target in enumerate(target_field_paths):
    do_entity = start(do_entity, target, last_i, i, entities, found)
  entity = entities[0]
  if found_at:
    return (entity, found[0])
  return entity
