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
    if not hasattr(context, 'entities'):
      context.entities = {}
    if not hasattr(context, 'callbacks'):
      context.callbacks = []  # This variable allways receives tuples of two values! Example: [(a, b), (a, b)]
    if not hasattr(context, 'records'):
      context.records = []  # This variable allways receives tuples of at least one value and maximum of two! Example: [(a, ), (a, b)]
    if not hasattr(context, 'blob_url'):
      context.blob_url = None
    if not hasattr(context, 'blob_delete'):
      context.blob_delete = []
    if not hasattr(context, 'blob_write'):
      context.blob_write = []
    if not hasattr(context, 'blob_transform'):
      context.blob_transform = None
    if not hasattr(context, 'search_documents'):
      context.search_documents = []
    if not hasattr(context, 'search_documents_total_matches'):
      context.search_documents_total_matches = None
    if not hasattr(context, 'search_documents_count'):
      context.search_documents_count = None


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
    if not isinstance(self.cfg, list):
      self.cfg = []
    if not len(self.cfg):
      self.cfg = [{'model': 'models.'  + context.model.get_kind(),
                   'parent': None,
                   'namespace': 'namespace',
                   'path': 'entities.' + context.model.get_kind()}]
    for config in self.cfg:
      model_path = config.get('model')
      model = get_attr(context, model_path)
      parent_path = config.get('parent')
      namespace_path = config.get('namespace', 'namespace')
      parent = get_attr(context, parent_path)
      namespace = get_attr(context, namespace_path)
      if parent != None:
        namespace = None
      save_path = config.get('path')
      set_attr(context, save_path, model(parent=parent, namespace=namespace))


class Read(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    keys = []
    if not isinstance(self.cfg, list):
      self.cfg = []
    if not len(self.cfg):
      self.cfg = [{'source': 'input.key',
                   'path': 'entities.' + context.model.get_kind()}]
    for config in self.cfg:
      source_path = config.get('source')
      source = get_attr(context, source_path)
      if source and isinstance(source, ndb.Key):
        keys.append(source)
    ndb.get_multi(keys)
    for config in self.cfg:
      source_path = config.get('source')
      source = get_attr(context, source_path)
      entity = None
      if source and isinstance(source, ndb.Key):
        entity = source.get()
        save_path = config.get('path')
        set_attr(context, save_path, entity)


class Write(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    write_entities = []
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_paths = self.cfg.get('paths', ['entities.' + context.model.get_kind()])
    parent_path = self.cfg.get('parent', None)
    namespace_path = self.cfg.get('namespace', 'namespace')
    parent = get_attr(context, parent_path)
    namespace = get_attr(context, namespace_path)
    for entity_path in entity_paths:
      entities = get_attr(context, entity_path)
      entities = normalize(entities)
      if len(entities):
        for entity in entities:
          if entity and isinstance(entity, ndb.Model):
            write_entities.append(entity)
    # @todo This parent/namespace block needs improvement!
    if parent != None:
      namespace = None
    for entity in write_entities:
      util.logger('Entity to be written: %s' % entity)
      if not hasattr(entity, 'key'):
        entity.set_key(None, parent=parent, namespace=namespace)
    ndb.put_multi(write_entities)


class Delete(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    delete_keys = []
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_paths = self.cfg.get('paths', ['entities.' + context.model.get_kind()])
    for entity_path in entity_paths:
      entities = get_attr(context, entity_path)
      entities = normalize(entities)
      if len(entities):
        for entity in entities:
          if entity and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
            delete_keys.append(entity.key)
          elif entity and isinstance(entity, ndb.Key):
            delete_keys.append(entity)
    delete_keys = set(delete_keys)
    ndb.delete_multi(delete_keys)


class Search(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    index_name = self.cfg.get('index', None)
    page_size = self.cfg.get('page', 10)
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
      context.search_documents = result['documents']
      context.search_documents_count = result['documents_count']
      context.search_documents_total_matches = result['total_matches']
    else:
      result = ndb_search(model, argument, page_size, urlsafe_cursor, namespace)
      context.entities = result['entities']
    context.search_cursor = result['search_cursor']
    context.search_more = result['search_more']


class RecordRead(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    @ndb.tasklet
    def async(entity):
      if entity.key_namespace and entity.agent.id() != 'system':
        domain_user_key = ndb.Key('8', str(entity.agent.id()), namespace=entity.key_namespace)
        agent = yield domain_user_key.get_async()
        agent = agent.name
      else:
        agent = yield entity.agent.get_async()
        agent = agent._primary_email
      entity._agent = agent
      action_parent = entity.action.parent()
      modelclass = entity._kind_map.get(action_parent.kind())
      action_id = entity.action.id()
      if modelclass and hasattr(modelclass, '_actions'):
        for action in modelclass._actions:
          if entity.action == action.key:
            entity._action = '%s.%s' % (modelclass.__name__, action_id)
            break
      raise ndb.Return(entity)
    
    @ndb.tasklet
    def helper(entities):
      results = yield map(async, entities)
      raise ndb.Return(results)
    
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', 'entities.' + context.model.get_kind())
    page_size = self.cfg.get('page', 10)
    entity = get_attr(context, entity_path)
    if entity and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
      model = context.models['5']
      argument = {'filters': [{'field': 'ancestor', 'operator': '==', 'value': entity.key}],
                  'order_by': {'field': 'logged', 'operator': 'desc'}}
      urlsafe_cursor = context.input.get('search_cursor')
      result = ndb_search(model, argument, page_size, urlsafe_cursor)
      entities = helper(result['entities'])
      entities = [entity for entity in entities.get_result()]
      set_attr(context, entity_path + '._records', entities)
      context.search_cursor = result['search_cursor']
      context.search_more = result['search_more']


class RecordWrite(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    model = context.models['5']
    arguments = {}
    entity_paths = self.cfg.get('paths', [])
    static_arguments = self.cfg.get('s', {})
    dynamic_arguments = self.cfg.get('d', {})
    arguments.update(static_arguments)
    for key, value in dynamic_arguments.items():
      arguments[key] = get_attr(context, value)
    for entity_path in entity_paths:
      entities = get_attr(context, entity_path)
      entities = normalize(entities)
      context.records.extend([(entity, arguments) for entity in entities])
    record_write(context.models['5'], context.records, context.user.key, context.action.key)
    context.records = []


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


class BlobUpdate(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    delete_path = self.cfg.get('delete', 'blob_delete')
    write_path = self.cfg.get('write', 'blob_write')
    blob_delete = get_attr(context, delete_path)
    blob_write = get_attr(context, write_path)
    context.blob_unused = blob_update(context.blob_unused, blob_delete, blob_write)


class BlobAlterImage(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    read_path = self.cfg.get('read', None)
    write_path = self.cfg.get('write', None)
    config = self.cfg.get('config', None)
    entities = get_attr(context, read_path)
    write_entities, blob_delete = blob_alter_image(entities, config)
    context.blob_delete.extend(blob_delete)
    set_attr(context, write_path, write_entities)


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
    rule_prepare(context, entity_path, skip_user_roles, strict)


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
