# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm
from app.tools.base import *
from app.util import *


class Context(orm.BaseModel):
  
  def run(self, context):
    # @todo Following lines are temporary, until we decide where and how to distribute them!
    context.user = context.models['0'].current_user()
    caller_user_key = context.input.get('caller_user')
    if context.user._is_taskqueue:
      if caller_user_key:
        caller_user = caller_user_key.get()
        if caller_user:
          context.user = caller_user
      else:
        context.user = context.models['0'].get_system_user()
    context.namespace = None
    context.domain = None
    domain_key = context.input.get('domain')
    if domain_key:
      context.domain = domain_key.get()
      context.namespace = context.domain.key_namespace
    context._callbacks = []  # @todo For now this stays here!


class Set(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    static_values = self.cfg.get('s', {})
    dynamic_values = self.cfg.get('d', {})
    remove_values = self.cfg.get('rm', [])
    for key, value in static_values.iteritems():
      set_attr(context, key, value)
    for key, value in dynamic_values.iteritems():
      set_value = get_attr(context, value, Nonexistent)
      if set_value is not Nonexistent:
        set_attr(context, key, set_value)
    for key in remove_values:
      del_attr(context, key)


class Read(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    source_path = self.cfg.get('source', 'input.key')
    model_path = self.cfg.get('model', 'model')
    parent_path = self.cfg.get('parent', None)
    namespace_path = self.cfg.get('namespace', 'namespace')
    read_arguments_path = self.cfg.get('read', 'input.read_arguments')
    save_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    source = get_attr(context, source_path, None)
    model = get_attr(context, model_path)
    parent = get_attr(context, parent_path)
    namespace = get_attr(context, namespace_path)
    read_arguments = get_attr(context, read_arguments_path, {})
    if parent is not None:
      namespace = None
    if source and isinstance(source, orm.Key):
      entity = source.get()
      entity.read(read_arguments)
    elif hasattr(model, 'prepare_key'):
      model_key = model.prepare_key(context.input, parent=parent, namespace=namespace)  # @todo Perhaps, all context system wide variables should be passed to prepare_key (input, output, action, model, models, domain, namespace...)
      if model_key.id() is not None:
        entity = model_key.get()
        if entity is None:
          entity = model(key=model_key)
        else:
          entity.read(read_arguments)
      else:
        entity = model(key=model_key)
    else:
      entity = model()
      entity.set_key(None, parent=parent, namespace=namespace)
    entity.make_original()
    set_attr(context, save_path, entity)


class Write(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    static_record_arguments = self.cfg.get('sra', {})
    dynamic_record_arguments = self.cfg.get('dra', {})
    entity = get_attr(context, entity_path)
    if entity and isinstance(entity, orm.Model):
      record_arguments = {'agent': context.user.key, 'action': context.action.key}
      record_arguments.update(static_record_arguments)
      for key, value in dynamic_record_arguments.iteritems():
        record_arguments[key] = get_attr(context, value)
      entity.write(record_arguments)


class Delete(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    static_record_arguments = self.cfg.get('sra', {})
    dynamic_record_arguments = self.cfg.get('dra', {})
    entity = get_attr(context, entity_path)
    if entity and isinstance(entity, orm.Model):
      record_arguments = {'agent': context.user.key, 'action': context.action.key}
      record_arguments.update(static_record_arguments)
      for key, value in dynamic_record_arguments.iteritems():
        record_arguments[key] = get_attr(context, value)
      entity.delete(record_arguments)


class Duplicate(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('source', '_' + context.model.__name__.lower())
    save_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    child_entity_path = self.cfg.get('copy_path')
    entity = get_attr(context, entity_path)
    if child_entity_path:
      child_entity = get_attr(entity, child_entity_path)
      parent_entity_path = ".".join(child_entity_path.split('.')[:-1])
      parent_entity = get_attr(entity, parent_entity_path)
      parent_entity.append(child_entity.duplicate())
      duplicate_entity = entity
    else:
      if entity and isinstance(entity, orm.Model):
        duplicate_entity = entity.duplicate()
    set_attr(context, save_path, duplicate_entity)


class UploadImages(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    images_path = self.cfg.get('images_path')
    manager = get_attr(context, entity_path)
    if manager is not None and hasattr(manager, 'add') and callable(manager.add):
      manager.add(get_attr(context, images_path))


class RulePrepare(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    skip_user_roles = self.cfg.get('skip_user_roles', False)
    strict = self.cfg.get('strict', False)
    static_kwargs = self.cfg.get('s', {})
    dynamic_kwargs = self.cfg.get('d', {})
    kwargs = {'user': context.user, 'action': context.action}
    kwargs.update(static_kwargs)
    for key, value in dynamic_kwargs.iteritems():
      kwargs[key] = get_attr(context, value)
    entities = get_attr(context, entity_path)
    rule_prepare(entities, skip_user_roles, strict, **kwargs)


class RuleExec(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    action_path = self.cfg.get('action', 'action')
    entity = get_attr(context, entity_path)
    action = get_attr(context, action_path)
    rule_exec(entity, action)


class Search(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    search_arguments = context.input.get('search')
    search_arguments['namespace'] = context.namespace
    result = context.model.search(search_arguments)
    if search_arguments.get('keys'):
      context._entities = result
      context._cursor = None
      context._more = False
    elif context.model._use_search_engine:
      context._total_matches = result.number_found
      context._entities_count = len(result.results)
      context._entities = map(context.model.search_document_to_entity, result.results)
      more = False
      cursor = result.cursor
      if cursor is not None:
        cursor = cursor.web_safe_string
        more = True
      context._cursor = cursor
      context._more = more
    else:
      context._entities_count = len(result[0])
      context._entities = result[0]
      cursor = result[1]
      if cursor is not None:
        cursor = cursor.urlsafe()
      context._cursor = cursor
      context._more = result[2]


class CallbackNotify(orm.BaseModel):
  
  def run(self, context):
    static_data = {}
    entity = get_attr(context, '_' + context.model.__name__.lower())
    static_data.update({'caller_entity': entity.key_urlsafe,
                        'action_id': 'initiate',
                        'action_model': '61'})
    context._callbacks.append(('notify', static_data))


class CallbackExec(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.cfg, list):
      self.cfg = []
    queues = {}
    for config in self.cfg:
      queue_name, static_data, dynamic_data = config
      for key, value in dynamic_data.iteritems():
        static_data[key] = get_attr(context, value)
      context._callbacks.append((queue_name, static_data))
    for callback in context._callbacks:
      if callback[1].get('caller_user') is None:
        callback[1]['caller_user'] = context.user.key_urlsafe
      if callback[1].get('caller_action') is None:
        callback[1]['caller_action'] = context.action.key_urlsafe
    callback_exec('/task/io_engine_run', context._callbacks)
    context._callbacks = []


class BlobURL(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    gs_bucket = self.cfg.get('bucket', None)
    sufix = self.cfg.get('sufix', '/' + context.model.__name__.lower())
    upload_url = context.input.get('upload_url')
    if upload_url and gs_bucket:
      gs_bucket_name = gs_bucket + sufix
      context._blob_url = blob_create_upload_url(upload_url, gs_bucket_name)
      #raise orm.TerminateAction()

