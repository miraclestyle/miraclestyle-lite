# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import copy
import time

import orm
import tools

class Context(orm.BaseModel):
  
  _kind = 86
  
  def run(self, context):
    # @todo Following lines are temporary, until we decide where and how to distribute them!
    context.account = context.models['11'].current_account()
    caller_account_key = context.input.get('caller_account')
    if context.account._is_taskqueue:
      if caller_account_key:
        caller_account = caller_account_key.get()
        if caller_account:
          context.account = caller_account
      else:
        context.account = context.models['11'].get_system_account()
    context._callbacks = []  # @todo For now this stays here!


class Set(orm.BaseModel):
  
  _kind = 87
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    static_values = self.cfg.get('s', {})
    dynamic_values = self.cfg.get('d', {})
    remove_values = self.cfg.get('rm', [])
    remove_structured_values = self.cfg.get('rms', [])
    for key, value in static_values.iteritems():
      tools.set_attr(context, key, value)
    for key, value in dynamic_values.iteritems():
      set_value = tools.get_attr(context, value, tools.Nonexistent)
      if set_value is not tools.Nonexistent:
        tools.set_attr(context, key, set_value)
    for key in remove_values:
      tools.del_attr(context, key)
    for key in remove_structured_values:
      items = tools.get_attr(key)
      if isinstance(items, list):
        for item in items:
          item._state = 'removed'
        else:
          items._state = 'removed'

          
class Read(orm.BaseModel):
  
  _kind = 88
  
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
    source = tools.get_attr(context, source_path, None)
    model = tools.get_attr(context, model_path)
    parent = tools.get_attr(context, parent_path)
    namespace = tools.get_attr(context, namespace_path)
    if isinstance(read_arguments_path, dict):
      read_arguments = copy.deepcopy(read_arguments_path)
    else:
      read_arguments = tools.get_attr(context, read_arguments_path, {})
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
      entity = model(parent=parent, namespace=namespace)
    entity.make_original()
    tools.set_attr(context, save_path, entity)


class Write(orm.BaseModel):
  
  _kind = 89
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    static_record_arguments = self.cfg.get('sra', {})
    dynamic_record_arguments = self.cfg.get('dra', {})
    entity = tools.get_attr(context, entity_path)
    if entity and isinstance(entity, orm.Model):
      record_arguments = {'agent': context.account.key, 'action': context.action.key}
      record_arguments.update(static_record_arguments)
      for key, value in dynamic_record_arguments.iteritems():
        record_arguments[key] = tools.get_attr(context, value)
      entity.write(record_arguments)


class Delete(orm.BaseModel):
  
  _kind = 90
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    static_record_arguments = self.cfg.get('sra', {})
    dynamic_record_arguments = self.cfg.get('dra', {})
    entity = tools.get_attr(context, entity_path)
    if entity and isinstance(entity, orm.Model):
      record_arguments = {'agent': context.account.key, 'action': context.action.key}
      record_arguments.update(static_record_arguments)
      for key, value in dynamic_record_arguments.iteritems():
        record_arguments[key] = tools.get_attr(context, value)
      entity.delete(record_arguments)


class Duplicate(orm.BaseModel):
  
  _kind = 91
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('source', '_' + context.model.__name__.lower())
    save_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    child_entity_path = self.cfg.get('duplicate_path')
    entity = tools.get_attr(context, entity_path)
    if child_entity_path:
      # state _images.value.0.pricetags.value.0
      splited = child_entity_path.split('.')
      child_entity = tools.get_attr(entity, child_entity_path)
      duplicated_child_entity = child_entity.duplicate()
      duplicate_entity = entity
      # gets _images.value.0.pricetags
      middle_entity_path = ".".join(splited[:-2])
      # sets entity._images.value.0.pricetags => [duplicated_child_entity]
      try:
        int(splited[-1]) # this is a case of repeated property, put the duplicated child into list
        duplicated_child_entity = [duplicated_child_entity]
      except ValueError:
        pass
      tools.set_attr(entity, middle_entity_path, duplicated_child_entity)
    else:
      if entity and isinstance(entity, orm.Model):
        duplicate_entity = entity.duplicate()
    tools.set_attr(context, save_path, duplicate_entity)


class UploadImages(orm.BaseModel):
  
  _kind = 92
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    images_path = self.cfg.get('images_path')
    manager = tools.get_attr(context, entity_path)
    if manager is not None and hasattr(manager, 'add') and callable(manager.add):
      manager.add(tools.get_attr(context, images_path))


class RulePrepare(orm.BaseModel):
  
  _kind = 93
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    static_kwargs = self.cfg.get('s', {})
    dynamic_kwargs = self.cfg.get('d', {})
    kwargs = {'account': context.account, 'action': context.action, 'input': context.input}
    kwargs.update(static_kwargs)
    for key, value in dynamic_kwargs.iteritems():
      kwargs[key] = tools.get_attr(context, value)
    entities = tools.get_attr(context, entity_path)
    tools.rule_prepare(entities, **kwargs)


class RuleExec(orm.BaseModel):
  
  _kind = 94
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    action_path = self.cfg.get('action', 'action')
    entity = tools.get_attr(context, entity_path)
    action = tools.get_attr(context, action_path)
    tools.rule_exec(entity, action)


class Search(orm.BaseModel):
  
  _kind = 95
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    static_arguments = self.cfg.get('s', {})
    dynamic_arguments = self.cfg.get('d', {})
    search_arguments = context.input.get('search')
    overide_arguments = {}
    overide_arguments.update(static_arguments)
    for key, value in dynamic_arguments.iteritems():
      overide_arguments[key] = tools.get_attr(context, value)
    tools.override_dict(search_arguments, overide_arguments)
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
    # if we dont call .read() it wont load any properties that depend on it. e.g. localstructured ones.
    map(lambda ent: ent.read(), context._entities)


class CallbackExec(orm.BaseModel):
  
  _kind = 97
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.cfg, list):
      self.cfg = []
    queues = {}
    for config in self.cfg:
      queue_name, static_data, dynamic_data = config
      for key, value in dynamic_data.iteritems():
        static_data[key] = tools.get_attr(context, value)
      context._callbacks.append((queue_name, static_data))
    for callback in context._callbacks:
      if callback[1].get('caller_account') is None:
        callback[1]['caller_account'] = context.account.key_urlsafe
      if callback[1].get('caller_action') is None:
        callback[1]['caller_action'] = context.action.key_urlsafe
    tools.callback_exec('/api/task/io_engine_run', context._callbacks)
    context._callbacks = []


class BlobURL(orm.BaseModel):
  
  _kind = 98
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    gs_bucket = self.cfg.get('bucket', None)
    sufix = self.cfg.get('sufix', '/' + context.account.key_urlsafe)
    upload_url = context.input.get('upload_url')
    if upload_url and gs_bucket:
      gs_bucket_name = gs_bucket + sufix
      context._blob_url = tools.blob_create_upload_url(upload_url, gs_bucket_name)


class CreateChannel(orm.BaseModel):

  _kind = 128

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    token = 'channel_%s' % context.account.key_urlsafe
    existing = tools.mem_get(token)
    if existing and existing[1] > time.time():
      context._token = existing[0]
    else:
      context._token = tools.channel_create(token)
      tools.mem_set(token, [context._token, time.time() + 6000], 9600)


class Notify(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    method = self.cfg.get('method', ['mail'])
    if not isinstance(method, (list, tuple)):
      method = [method]
    condition = self.cfg.get('condition', 'True')
    static_values = self.cfg.get('s', {})
    dynamic_values = self.cfg.get('d', {})
    entity = tools.get_attr(context, '_' + context.model.__name__.lower())
    values = {'account': context.account, 'input': context.input, 'action': context.action, 'entity': entity}
    values.update(static_values)
    for key, value in dynamic_values.iteritems():
      values[key] = tools.get_attr(context, value)
    if tools.safe_eval(condition, values):
      if 'mail' in method:
        tools.mail_send(values)
      if 'http' in method:
        tools.http_send(values)
      if 'channel' in method:
        tools.channel_send(values)
