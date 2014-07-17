# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy

from app import orm, util
from app.tools.base import *
from app.tools.manipulator import set_attr, get_attr, normalize


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
    for key, value in static_values.items():
      set_attr(context, key, value)
    for key, value in dynamic_values.items():
      set_attr(context, key, get_attr(context, value))


class Read(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    source_path = self.cfg.get('source', 'input.key')
    model_path = self.cfg.get('model', 'model')
    parent_path = self.cfg.get('parent', None)
    namespace_path = self.cfg.get('namespace', 'namespace')
    save_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    source = get_attr(context, source_path)
    model = get_attr(context, model_path)
    parent = get_attr(context, parent_path)
    namespace = get_attr(context, namespace_path)
    if parent is not None:
      namespace = None
    if source and isinstance(source, orm.Key):
      entity = source.get()
      entity.read(context.input.get('read_arguments', {}))
    elif hasattr(model, 'prepare_key'):
      model_key = model.prepare_key(context.input, parent=parent, namespace=namespace)
      entity = model_key.get()
      if entity is None:
        entity = model()
        entity.set_key(model_key)
      else:
        entity.read(context.input.get('read_arguments', {}))
    else:
      entity = model()
      entity.set_key(parent=parent, namespace=namespace)
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
      for key, value in dynamic_record_arguments.items():
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
      for key, value in dynamic_record_arguments.items():
        record_arguments[key] = get_attr(context, value)
      entity.delete(record_arguments)


class Duplicate(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    save_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    entity = get_attr(context, entity_path)
    if entity and isinstance(entity, orm.Model):
      duplicate_entity = entity.duplicate()
      set_attr(context, save_path, duplicate_entity)


class UploadImages(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  upload_cfg = orm.SuperJsonProperty('2', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    if not isinstance(self.upload_cfg, dict):
      self.upload_cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    entity = get_attr(context, entity_path)
    if entity and isinstance(entity, orm.Model):
      for field_key, input_key in self.upload_cfg.items():
        value = getattr(entity, field_key, None)
        if value is not None:
          value.upload(context.input.get(input_key))


class ProcessImages(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    entity = get_attr(context, entity_path)
    if entity and isinstance(entity, orm.Model):
      for field_key, field in entity.get_fields().items():
        if field.is_structured:
          value = getattr(self, field_key)
          if hasattr(value, 'process') and callable(value.process):
            value.process()


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
    for key, value in dynamic_kwargs.items():
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
    index_name = self.cfg.get('index', None)
    limit = self.cfg.get('page', 10)
    fields = self.cfg.get('fields', None)
    search_document = self.cfg.get('document', False)
    argument = context.input.get('search')
    urlsafe_cursor = context.input.get('search_cursor')
    namespace = context.namespace
    if index_name == None:
      index_name = context.model.get_kind()
    else:
      namespace = None
    if search_document:
      result = document_search(index_name, namespace, argument, limit, urlsafe_cursor, fields)
      context._documents = result[0]
      context._cursor = result[1]
      context._more = result[2]
      context._documents_count = result[3]
      context._total_matches = result[4]
    else:
      result = context.model.search(argument, namespace, limit, urlsafe_cursor)
      entities = []
      if isinstance(result, tuple):
        context._entities = result[0]
        context._cursor = result[1]
        context._more = result[2]
      elif isinstance(result, list):
        context._entities = result
        context._cursor = None
        context._more = False


class CallbackNotify(orm.BaseModel):
  
  def run(self, context):
    static_data = {}
    static_data.update({'action_id': 'initiate', 'action_model': '61'})
    entity = get_attr(context, '_' + context.model.__name__.lower())
    static_data['caller_entity'] = entity.key_urlsafe
    context._callbacks.append(('notify', static_data))


class CallbackExec(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.cfg, list):
      self.cfg = []
    queues = {}
    for config in self.cfg:
      queue_name, static_data, dynamic_data = config
      for key, value in dynamic_data.items():
        static_data[key] = get_attr(context, value)
      context._callbacks.append((queue_name, static_data))
    callback_exec('/task/io_engine_run', context._callbacks, context.user.key_urlsafe, context.action.key_urlsafe)
    context._callbacks = []


class BlobURL(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    gs_bucket_name = self.cfg.get('bucket', None)
    upload_url = context.input.get('upload_url')
    if upload_url:
      context._blob_url = blob_create_upload_url(upload_url, gs_bucket_name)
      #raise orm.TerminateAction()


class DocumentWrite(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    fields = self.cfg.get('fields', {})
    documents_per_index = self.cfg.get('max_doc', 200)
    entities = get_attr(context, entity_path)
    documents = document_from_entity(entities, fields)
    document_write(documents, documents_per_index=documents_per_index)


class DocumentDelete(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    documents_per_index = self.cfg.get('max_doc', 200)
    entities = get_attr(context, entity_path)
    document_delete(entities, documents_per_index=documents_per_index)


class DocumentDictConverter(orm.BaseModel):
  
  def run(self, context):
    if len(context._documents):
      context._entities = document_to_dict(context._documents)


class DocumentEntityConverter(orm.BaseModel):
  
  def run(self, context):
    if len(context._documents):
      context._entities = orm.get_multi([document.doc_id for document in context._documents])
