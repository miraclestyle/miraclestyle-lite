# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json
import copy
import string
import collections

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api import taskqueue
from google.appengine.api import search

from app import ndb, util
from app.tools.attribute_manipulator import set_attr, get_attr, get_meta
from app.tools.blob_manipulator import create_upload_url, parse, alter_image
from app.tools.rule_manipulator import prepare, read, write, _is_structured_field


class Context(ndb.BaseModel):  # @todo Not migrated!
  
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
    if not hasattr(context, 'values'):
      context.values = {}
    if not hasattr(context, 'callbacks'):
      context.callbacks = []
    if not hasattr(context, 'records'):
      context.records = []
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


class Set(ndb.BaseModel):  # @todo Not migrated!
  
  static_values = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  dynamic_values = ndb.SuperJsonProperty('2', indexed=False, required=True, default={})
  
  def run(self, context):
    for key, value in self.static_values.items():
      set_attr(context, key, value)
    for key, value in self.dynamic_values.items():
      set_attr(context, key, get_attr(context, value))


class Prepare(ndb.BaseModel):  # @todo Not migrated!
  
  kind_id = ndb.SuperStringProperty('1', indexed=False)
  namespace_path = ndb.SuperStringProperty('2', indexed=False)
  parent_path = ndb.SuperStringProperty('3', indexed=False)
  
  def run(self, context):
    parent = None
    if self.kind_id != None:
      kind_id = self.kind_id
    else:
      kind_id = context.model.get_kind()
    if self.namespace_path != None:
      namespace = get_attr(context, self.namespace_path)
    else:
      namespace = context.namespace
    if self.parent_path != None:
      parent = get_attr(context, self.parent_path)
    context.entities[kind_id] = context.models[kind_id](parent=parent, namespace=namespace)
    context.values[kind_id] = context.models[kind_id](parent=parent, namespace=namespace)


class Read(ndb.BaseModel):  # @todo Not migrated!
  
  read_entities = ndb.SuperJsonProperty('1', indexed=False, default={})
  
  def run(self, context):
    keys = []
    values = []
    if len(self.read_entities):
      for key, value in self.read_entities.items():
        keys.append(key)
        values.append(get_attr(context, value))
    else:
      keys.append(context.model.get_kind())
      values.append(get_attr(context, 'input.key'))
    entities = ndb.get_multi(values)
    for i, key in enumerate(keys):
      context.entities[key] = entities[i]
      context.values[key] = copy.deepcopy(context.entities[key])


class Write(ndb.BaseModel):  # @todo Not migrated!
  
  write_entities = ndb.SuperStringProperty('1', indexed=False, repeated=True)
  
  def run(self, context):
    entities = []
    if len(self.write_entities):
      for kind_id in self.write_entities:
        if kind_id in context.entities:
          entities.append(context.entities[kind_id])
    else:
      entities.append(context.entities[context.model.get_kind()])
    ndb.put_multi(entities)


class Delete(ndb.BaseModel):  # @todo Not migrated!
  
  delete_entities = ndb.SuperStringProperty('1', indexed=False, repeated=True)
  
  def run(self, context):
    keys = []
    if len(self.delete_entities):
      for kind_id in self.delete_entities:
        if kind_id in context.entities:
          keys.append(context.entities[kind_id].key)
    else:
      keys.append(context.entities[context.model.get_kind()].key)
    ndb.delete_multi(keys)


class Search(ndb.BaseModel):  # @todo Not migrated!
  
  kind_id = ndb.SuperStringProperty('1', indexed=False)
  page_size = ndb.SuperIntegerProperty('2', indexed=False, required=True, default=10)
  
  def run(self, context):
    namespace = None
    if self.kind_id != None:
      kind_id = self.kind_id
    else:
      kind_id = context.model.get_kind()
    model = context.models[kind_id]
    if context.entities[kind_id].key:
      namespace = context.entities[kind_id].key_namespace
    value = None
    search_argument = context.input.get('search')
    if search_argument:
      args = []
      kwds = {}
      filters = search_argument.get('filters')
      order_by = search_argument.get('order_by')
      for _filter in filters:
        if _filter['field'] == 'ancestor':
          kwds['ancestor'] = _filter['value']
          continue
        field = getattr(model, _filter['field'])
        op = _filter['operator']
        value = _filter['value']
        if op == '==': # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this also needs improvements
          args.append(field == value)
        elif op == '!=':
          args.append(field != value)
        elif op == '>':
          args.append(field > value)
        elif op == '<':
          args.append(field < value)
        elif op == '>=':
          args.append(field >= value)
        elif op == 'IN':
          args.append(field.IN(value))
        elif op == 'contains':
          letters = list(string.printable)
          try:
            last = letters[letters.index(value[-1].lower()) + 1]
            args.append(field >= value)
            args.append(field < last)
          except ValueError as e:  # Value not in the letter scope, šččđčžćč for example.
            args.append(field == value)
      query = model.query(namespace=namespace, **kwds)
      query = query.filter(*args)
      if order_by:
        order_by_field = getattr(model, order_by['field'])
        if order_by['operator'] == 'asc':
          query = query.order(order_by_field)
        else:
          query = query.order(-order_by_field)
    cursor = Cursor(urlsafe=context.input.get('search_cursor'))
    def value_is_key(value):
      if isinstance(value, list) and len(value):
        for v in value:
          if not isinstance(v, ndb.Key):
            return False
        return True
      elif isinstance(value, ndb.Key):
        return True
      else:
        return False
    if value_is_key(value):
      # this has to be done like this because there is no way to order the fetched items
      # in the order the keys were provided, the MultiQuery disallowes that http://stackoverflow.com/questions/12449197/badargumenterror-multiquery-with-cursors-requires-key-order-in-ndb
      keys = value
      if not isinstance(keys, list):
        keys = [value]
      entities = ndb.get_multi(keys)
      cursor = None
      more = False
    else:
      if self.page_size != None and self.page_size > 0:
        entities, cursor, more = query.fetch_page(self.page_size, start_cursor=cursor)
        if cursor:
          cursor = cursor.urlsafe()
      else:
        entities = query.fetch()
        cursor = None
        more = False
    context.entities = entities
    context.search_cursor = cursor
    context.search_more = more


class RecordRead(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    entity_path = self.config.get('path', 'entities.' + str(context.model.get_kind()))
    page_size = self.config.get('page', 10)
    entity = get_attr(context, entity_path)
    if entity and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
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
      
      cursor = Cursor(urlsafe=context.input.get('records_cursor'))
      model = context.models['5']
      query = model.query(ancestor=entity.key).order(-model.logged)
      entities, cursor, more = query.fetch_page(page_size, start_cursor=cursor)
      if cursor:
        cursor = cursor.urlsafe()
      entities = helper(entities)
      entities = [entity for entity in entities.get_result()]
      set_attr(context, entity_path + '._records', entities)
      context.records_cursor = cursor
      context.records_more = more


class RecordWrite(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    model = context.models['5']
    records = []
    write_arguments = {}
    records_paths = self.config.get('records', [])
    static_arguments = self.config.get('static', {})
    dynamic_arguments = self.config.get('dynamic', {})
    for records_path in records_paths:
      result = get_attr(context, records_path)
      if isinstance(result, dict):
        context.records.extend([record for key, record in result.items()])
      if isinstance(result, list):
        context.records.extend(result)
      else:
        context.records.append(result)
    write_arguments.update(static_arguments)
    for key, value in dynamic_arguments.items():
      write_arguments[key] = get_attr(context, value)
    if len(context.records):
      for config in context.records:
        arguments = {}
        kwargs = {}
        entity = config[0]
        try:
          entity_arguments = config[1]
        except:
          entity_arguments = {}
        arguments.update(write_arguments)
        arguments.update(entity_arguments)
        log_entity = arguments.pop('log_entity', True)
        if len(arguments):
          for key, value in arguments.items():
            if entity._field_permissions['_records'][key]['writable']:
              kwargs[key] = value
        record = model(parent=entity.key, agent=context.user.key, action=context.action.key, **kwargs)
        if log_entity is True:
          log_entity = entity
        if log_entity:
          record.log_entity(log_entity)
        records.append(record)
    if len(records):
      recorded = ndb.put_multi(records)
    context.records = []


class CallbackNotify(ndb.BaseModel):  # @todo Not migrated!
  
  dynamic_data = ndb.SuperJsonProperty('1', required=True, indexed=False, default={})
  
  def run(self, context):
    if not isinstance(self.dynamic_data, dict):
      self.dynamic_data = {}
    static_data = {}
    static_data.update({'action_id': 'initiate', 'action_model': '61'})
    static_data['caller_entity'] = context.entities[context.model.get_kind()].key_urlsafe
    context.callbacks.append(('notify', static_data, self.dynamic_data))


class CallbackExec(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.config, list):
      self.config = []
    queues = {}
    url = '/task/io_engine_run'
    context.callbacks.extend(self.config)
    if ndb.in_transaction():
      context.callbacks = context.callbacks[:5]
    if len(context.callbacks):
      for callback in context.callbacks:
        data = {}
        queue_name, static_data, dynamic_data = callback
        data.update(static_data)
        for key, value in dynamic_data.items():
          data[key] = get_attr(context, value)
        if data.get('caller_user') == None:
          data['caller_user'] = get_attr(context, 'user.key_urlsafe')
        if data.get('caller_action') == None:
          data['caller_action'] = get_attr(context, 'action.key_urlsafe')
        if queue_name not in queues:
          queues[queue_name] = []
        queues[queue_name].append(taskqueue.Task(url=url, payload=json.dumps(data)))
    if len(queues):
      for queue_name, tasks in queues.items():
        queue = taskqueue.Queue(name=queue_name)
        queue.add(tasks, transactional=ndb.in_transaction())
    context.callbacks = []


class BlobURL(ndb.BaseModel):  # @todo Not migrated!
  
  gs_bucket_name = ndb.SuperStringProperty('1', indexed=False, required=True)
  
  def run(self, context):
    upload_url = context.input.get('upload_url')
    if upload_url:
      context.output['upload_url'] = create_upload_url(upload_url, self.gs_bucket_name)
      raise event.TerminateAction()


class BlobUpdate(ndb.BaseModel):  # @todo Not migrated!
  
  blob_delete = ndb.SuperStringProperty('1', indexed=False)
  blob_write = ndb.SuperStringProperty('2', indexed=False)
  
  def run(self, context):
    if self.blob_delete:
      blob_delete = get_attr(context, self.blob_delete)
    else:
      blob_delete = context.blob_delete
    if blob_delete:
      context.blob_unused.extend(parse(blob_delete))
    if self.blob_write:
      blob_write = get_attr(context, self.blob_write)
    else:
      blob_write = context.blob_write
    if blob_write:
      blob_write = parse(blob_write)
      for blob_key in blob_write:
        if blob_key in context.blob_unused:
          context.blob_unused.remove(blob_key)


class BlobAlterImage(ndb.BaseModel):  # @todo Not migrated!
  
  source = ndb.SuperStringProperty('1', indexed=False)
  destination = ndb.SuperStringProperty('2', indexed=False)
  config = ndb.SuperJsonProperty('3', indexed=False, required=True, default={})
  
  def run(self, context):
    if self.source:
      original_image = get_attr(context, self.source)
    else:
      original_image = context.blob_transform
    if original_image:
      results = alter_image(original_image, **self.config)
      if results.get('blob_delete'):
        context.blob_delete.append(results['blob_delete'])
      if results.get('new_image'):
        set_attr(context, self.destination, results['new_image'])


class BlobAlterImages(ndb.BaseModel):  # @todo Not migrated!
  
  source = ndb.SuperStringProperty('1', indexed=False)
  destination = ndb.SuperStringProperty('2', indexed=False)
  config = ndb.SuperJsonProperty('3', indexed=False, required=True, default={})
  
  def run(self, context):
    @ndb.tasklet
    def alter_image_async(source, destination):
      @ndb.tasklet
      def generate():
        original_image = get_attr(context, source)
        results = alter_image(original_image, **self.config)
        if results.get('blob_delete'):
          context.blob_delete.append(results['blob_delete'])
        if results.get('new_image'):
          set_attr(context, destination, results['new_image'])
        raise ndb.Return(True)
      yield generate()
      raise ndb.Return(True)
    
    futures = []
    images = get_attr(context, self.source)
    for i, image in enumerate(images):
      source = '%s.%s' % (self.source, i)
      destination = '%s.%s' % (self.destination, i)
      future = alter_image_async(source, destination)
      futures.append(future)
    return ndb.Future.wait_all(futures)


class ActionDenied(Exception):
  
  def __init__(self, context):
    self.message = {'action_denied': context.action}


class RulePrepare(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    values_path = self.config.get('values', 'values.' + str(context.model.get_kind()))
    entity_path = self.config.get('entity', 'entities.' + str(context.model.get_kind()))
    values = get_attr(context, values_path)
    entities = get_attr(context, entity_path)
    if isinstance(entities, dict):
      for key, entity in entities.items():
        context.entity = entities.get('key')
        context.value = values.get('key')
        prepare(context, self.config.get('skip_user_roles', False), self.config.get('strict', False))  # @todo Not sure if we should rename 'skip_user_roles' to 'skip'?
    elif isinstance(entities, list):
      for entity in entities:
        context.entity = entity
        context.value = None
        prepare(context, self.config.get('skip_user_roles', False), self.config.get('strict', False))
    else:
      context.entity = entities
      context.value = values
      prepare(context, self.config.get('skip_user_roles', False), self.config.get('strict', False))


class RuleRead(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    entity_path = self.config.get('path', 'entities.' + str(context.model.get_kind()))
    entities = get_attr(context, entity_path)
    if isinstance(entities, dict):
      for key, entity in entities.items():
        read(entity)
    elif isinstance(entities, list):
      for entity in entities:
        read(entity)
    else:
      read(entities)


class RuleWrite(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    values_path = self.config.get('values', 'values.' + str(context.model.get_kind()))
    entity_path = self.config.get('entity', 'entities.' + str(context.model.get_kind()))
    values = get_attr(context, values_path)
    entity = get_attr(context, entity_path)
    if values and entity:
      write(entity, values)


class RuleExec(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    entity_path = self.config.get('path', 'entities.' + str(context.model.get_kind()))
    entity = get_attr(context, entity_path)
    if entity and hasattr(entity, '_action_permissions'):
      if not entity._action_permissions[context.action.key.urlsafe()]['executable']:
        raise ActionDenied(context)
    else:
      raise ActionDenied(context)


__SEARCH_FIELDS = {'SuperKeyProperty': search.AtomField,
                   'SuperImageKeyProperty': search.AtomField,
                   'SuperBlobKeyProperty': search.AtomField,
                   'SuperBooleanProperty': search.AtomField,
                   'SuperStringProperty': search.TextField,
                   'SuperJsonProperty': search.TextField,
                   'SuperTextProperty': search.HtmlField,
                   'SuperFloatProperty': search.NumberField,
                   'SuperIntegerProperty': search.NumberField,
                   'SuperDecimalProperty': search.NumberField,
                   'SuperDateTimeProperty': search.DateField,
                   'geo': search.GeoField}


def get_search_field(field_type):
  global __SEARCH_FIELDS
  return __SEARCH_FIELDS.get(field_type)


class DocumentWrite(ndb.BaseModel):  # @todo This plugin can be improved to deal with multiple entities at the time!
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    entity_path = self.config.get('path', 'entities.' + str(context.model.get_kind()))
    entity = get_attr(context, entity_path)
    if entity and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
      doc_id = entity.key_urlsafe
      if entity.key_namespace != None:
        index_name = self.config.get('index_name', str(entity.key_namespace) + '-' + str(entity.get_kind()))
      else:
        index_name = self.config.get('index_name', str(entity.get_kind()))
      fields = []
      fields.append(search.AtomField(name='key', value=entity.key_urlsafe))
      fields.append(search.AtomField(name='kind', value=entity.get_kind()))
      fields.append(search.AtomField(name='id', value=entity.key_id_str))
      if entity.key_namespace != None:
        fields.append(search.AtomField(name='namespace', value=entity.key_namespace))
      if entity.key_parent != None:
        fields.append(search.AtomField(name='ancestor', value=entity.key_parent.urlsafe()))
      for field_name in self.config.get('fields', [])
        field_meta = get_meta(entity, field_name)
        field_value = get_attr(entity, field_name)
        field = None
        if field_meta._repeated:
          if field_meta.__class__.__name__ in ['SuperKeyProperty']:
            field_value = ' '.join(map(lambda x: x.urlsafe(), field_value))
            field = get_search_field('SuperStringProperty')
          elif field_meta.__class__.__name__ in ['SuperImageKeyProperty', 'SuperBlobKeyProperty', 'SuperBooleanProperty']:
            field_value = ' '.join(map(lambda x: str(x), field_value))
            field = get_search_field('SuperStringProperty')
          elif field_meta.__class__.__name__ in ['SuperStringProperty', 'SuperFloatProperty', 'SuperIntegerProperty', 'SuperDecimalProperty', 'SuperDateTimeProperty']:
            field_value = ' '.join(field_value)
            field = get_search_field('SuperStringProperty')
          elif field_meta.__class__.__name__ in ['SuperTextProperty']:
            field_value = ' '.join(field_value)
            field = get_search_field('SuperTextProperty')
        else:
          if field_meta.__class__.__name__ in ['SuperKeyProperty']:
            field_value = field_value.urlsafe()
          elif field_meta.__class__.__name__ in ['SuperImageKeyProperty', 'SuperBlobKeyProperty', 'SuperBooleanProperty', 'SuperJsonProperty']:
            field_value = str(field_value)
          field = get_search_field(field_meta.__class__.__name__)
        if field != None:
          fields.append(field(name=field_name, value=field_value))
      if doc_id != None and len(fields):
        try:
          index = search.Index(name=index_name)
          index.put(search.Document(doc_id=doc_id, fields=fields))  # Batching puts is more efficient than adding documents one at a time.
        except:
          pass


class DocumentDelete(ndb.BaseModel):  # @todo This plugin can be improved to deal with multiple entities at the time!
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    entity_path = self.config.get('path', 'entities.' + str(context.model.get_kind()))
    entity = get_attr(context, entity_path)
    if entity and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
      doc_id = entity.key_urlsafe
      if entity.key_namespace != None:
        index_name = self.config.get('index_name', str(entity.key_namespace) + '-' + str(entity.get_kind()))
      else:
        index_name = self.config.get('index_name', str(entity.get_kind()))
      if doc_id != None:
        try:
          index = search.Index(name=index_name)
          index.delete(doc_id)  # Batching deletes is more efficient than handling them one at a time.
        except:
          pass


class DocumentSearch(ndb.BaseModel):  # @todo Not migrated!
  
  kind_id = ndb.SuperStringProperty('1', indexed=False)
  index_name = ndb.SuperStringProperty('2', indexed=False)
  fields = ndb.SuperStringProperty('3', indexed=False, repeated=True)
  page_size = ndb.SuperIntegerProperty('4', indexed=False, required=True, default=10)
  
  def run(self, context):
    if self.kind_id != None:
      kind_id = self.kind_id
    else:
      kind_id = context.model.get_kind()
    namespace = context.entities[kind_id].key_namespace
    if self.index_name != None:
      index_name = self.index_name
    elif namespace != None:
      index_name = namespace + '-' + kind_id
    else:
      index_name = kind_id
    index = search.Index(name=index_name)
    # Query String implementation start!
    query_string = ''
    sort_options = None
    search_argument = context.input.get('search')
    if search_argument:
      filters = search_argument.get('filters')
      args = []
      for _filter in filters:
        field = _filter['field']
        op = _filter['operator']
        value = _filter['value']
        if field == 'query_string':
          args.append(value)
          break
        if field == 'ancestor':
          args.append('(' + field + '=' + value + ')')
          continue
        if op == '==': # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this also needs improvements
          args.append('(' + field + '=' + value + ')')
        elif op == '!=':
          args.append('(NOT ' + field + '=' + value + ')')
        elif op == '>':
          args.append('(' + field + '>' + value + ')')
        elif op == '<':
          args.append('(' + field + '<' + value + ')')
        elif op == '>=':
          args.append('(' + field + '>=' + value + ')')
        elif op == '<=':
          args.append('(' + field + '<=' + value + ')')
        elif op == 'IN':
          args.append('(' + ' OR '.join(['(' + field + '=' + v + ')' for v in value]) + ')')
      query_string = ' AND '.join(args)
      # Query String implementation start!
      order_by = search_argument.get('order_by')
      property_config = search_argument.get('property')
      if order_by['operator'] == 'asc':
        default_value=property_config._order_by[order_by['field']]['default_value']['asc']
        direction = search.SortExpression.ASCENDING
      else:
        default_value=property_config._order_by[order_by['field']]['default_value']['desc']
        direction = search.SortExpression.DESCENDING
      order = search.SortExpression(expression=order_by['field'], direction=direction, default_value=default_value)
      sort_options = search.SortOptions(expressions=[order], limit=self.page_size)
    cursor = context.input.get('search_cursor')
    if cursor:
      cursor = search.Cursor(web_safe_string=cursor)
    options = search.QueryOptions(limit=self.page_size, returned_fields=self.fields, sort_options=sort_options, cursor=cursor)
    query = search.Query(query_string=query_string, options=options)
    context.search_documents = []
    context.search_cursor = None
    context.search_more = False
    try:
      result = index.search(query)
      context.search_documents_total_matches = result.number_found
      if len(result.results):
        context.search_documents_count = len(result.results)
        context.search_documents = result.results
      if result.cursor != None:
        context.search_cursor = result.cursor.web_safe_string
        context.search_more = True
      else:
        context.search_cursor = None
        context.search_more = False
    except:
      raise


class DocumentDictConverter(ndb.BaseModel):
  
  def run(self, context):
    entities = []
    if len(context.search_documents):
      for document in context.search_documents:
        dic = {}
        dic['doc_id'] = document.doc_id
        dic['language'] = document.language
        dic['rank'] = document.rank
        fields = document.fields
        for field in fields:
          dic[field.name] = field.value
        entities.append(dic)
    context.entities = entities


class DocumentEntityConverter(ndb.BaseModel):
  
  def run(self, context):
    if len(context.search_documents):
      context.entities = ndb.get_multi([document.doc_id for document in context.search_documents])
