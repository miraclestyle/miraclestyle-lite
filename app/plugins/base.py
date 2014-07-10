# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy

from app import ndb, util
from app.tools.base import *
from app.tools.manipulator import set_attr, get_attr


class Context(ndb.BaseModel):
  
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


class Set(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    static_values = self.cfg.get('s', {})
    dynamic_values = self.cfg.get('d', {})
    for key, value in static_values.items():
      set_attr(context, key, value)
    for key, value in dynamic_values.items():
      set_attr(context, key, get_attr(context, value))


class Prepare(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    model_path = self.cfg.get('model', 'models.' + context.model.get_kind())
    parent_path = self.cfg.get('parent', None)
    namespace_path = self.cfg.get('namespace', 'namespace')
    model = get_attr(context, model_path)
    save_path = self.cfg.get('path', '_' + model.__class__.__name__.lower())  # @todo Is this ok?
    parent = get_attr(context, parent_path)
    namespace = get_attr(context, namespace_path)
    if parent != None:
      namespace = None
    if hasattr(model, 'prepare_key'):
      model_key = model.prepare_key(context.input, parent=parent, namespace=namespace)
      entity = model_key.get()
      if entity is None:
        entity = model()
        entity.set_key(model_key)
    else:
      entity = model()
      entity.set_key(parent=parent, namespace=namespace)
    set_attr(context, save_path, entity)


class Read(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    source_path = self.cfg.get('source', 'input.key')
    save_path = self.cfg.get('path', '_' + model.__class__.__name__.lower())  # @todo Is this ok?
    source = get_attr(context, source_path)
    if source and isinstance(source, ndb.Key):
      entity = source.get()
      entity.read(context.input)
      set_attr(context, save_path, entity)


class Write(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + model.__class__.__name__.lower())
    static_record_arguments = self.cfg.get('sra', {})
    dynamic_record_arguments = self.cfg.get('dra', {'agent': 'user', 'action': 'action'})
    entity = get_attr(context, entity_path)
    if entity and isinstance(entity, ndb.Model) and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
      entity._record_arguments = static_record_arguments
      for key, value in dynamic_record_arguments.items():
        entity._record_arguments[key] = get_attr(context, value)
      entity.put()


class Delete(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + model.__class__.__name__.lower())
    static_record_arguments = self.cfg.get('sra', {})
    dynamic_record_arguments = self.cfg.get('dra', {'agent': 'user', 'action': 'action'})
    entity = get_attr(context, entity_path)
    if entity and isinstance(entity, ndb.Model) and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
      entity._record_arguments = static_record_arguments
      for key, value in dynamic_record_arguments.items():
        entity._record_arguments[key] = get_attr(context, value)
      entity.key.delete()


class ActionDenied(Exception):
  
  def __init__(self, context):
    self.message = {'action_denied': context.action}


class RulePrepare(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', 'entities.' + context.model.get_kind())
    skip_user_roles = self.cfg.get('skip_user_roles', False)
    strict = self.cfg.get('strict', False)
    kwds = self.cfg.get('kwds', {})
    kwargs = {'user': context.user, 'action': context.action}
    for key, value in kwds.items():
      kwargs[key] = get_attr(context, value)
    rule_prepare(context, entity_path, skip_user_roles, strict, **kwargs)


class RuleExec(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', 'entities.' + context.model.get_kind())
    action_path = self.cfg.get('action', 'action.key_urlsafe')
    entity = get_attr(context, entity_path)
    action = get_attr(context, action_path)
    if entity and hasattr(entity, '_action_permissions'):
      if not entity._action_permissions[action]['executable']:
        raise ActionDenied(context)
    else:
      raise ActionDenied(context)


class Search(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    index_name = self.cfg.get('index', None)
    limit = self.cfg.get('page', 10)
    fields = self.cfg.get('fields', None)
    search_document = self.cfg.get('document', False)
    model =  context.models[context.model.get_kind()]
    argument = context.input.get('search')
    urlsafe_cursor = context.input.get('search_cursor')
    namespace = context.namespace
    if index_name == None:
      index_name = context.model.get_kind()
    else:
      namespace = None
    if search_document:
      result = document_search(index_name, argument, page_size, urlsafe_cursor, namespace, fields)
      context.search_documents = result[0]
      context.search_cursor = result[1]
      context.search_more = result[2]
      context.search_documents_count = result[3]
      context.search_documents_total_matches = result[4]
    else:
      result = model.search(argument, namespace=namespace, fetch_async=False, limit=limit, urlsafe_cursor=urlsafe_cursor)
      entities = []
      if isinstance(result, tuple):
        context.entities = result[0]
        context.search_cursor = result[1]
        context.search_more = result[2]
      elif isinstance(result, list):
        context.entities = result
        context.search_cursor = None
        context.search_more = False


class CallbackNotify(ndb.BaseModel):
  
  def run(self, context):
    static_data = {}
    static_data.update({'action_id': 'initiate', 'action_model': '61'})
    static_data['caller_entity'] = context.entities[context.model.get_kind()].key_urlsafe
    context.callbacks.append(('notify', static_data))


class CallbackExec(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.cfg, list):
      self.cfg = []
    queues = {}
    for config in self.cfg:
      queue_name, static_data, dynamic_data = config
      for key, value in dynamic_data.items():
        static_data[key] = get_attr(context, value)
      context.callbacks.append((queue_name, static_data))
    callback_exec('/task/io_engine_run', context.callbacks, context.user.key_urlsafe, context.action.key_urlsafe)
    context.callbacks = []


class BlobURL(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    gs_bucket_name = self.cfg.get('bucket', None)
    upload_url = context.input.get('upload_url')
    if upload_url:
      context.blob_url = blob_create_upload_url(upload_url, gs_bucket_name)
      #raise ndb.TerminateAction()


class DocumentWrite(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', 'entities.' + context.model.get_kind())
    fields = self.cfg.get('fields', {})
    max_doc = self.cfg.get('max_doc', 200)
    entities = get_attr(context, entity_path)
    entities = normalize(entities)
    documents = document_from_entity(entities, fields)
    document_write(documents, documents_per_index=max_doc)


class DocumentDelete(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    documents = []
    entity_path = self.cfg.get('path', 'entities.' + context.model.get_kind())
    max_doc = self.cfg.get('max_doc', 200)
    entities = get_attr(context, entity_path)
    document_delete(entities, documents_per_index=max_doc)


class DocumentDictConverter(ndb.BaseModel):
  
  def run(self, context):
    if len(context.search_documents):
      context.entities = document_to_dict(context.search_documents)


class DocumentEntityConverter(ndb.BaseModel):
  
  def run(self, context):
    if len(context.search_documents):
      context.entities = ndb.get_multi([document.doc_id for document in context.search_documents])
