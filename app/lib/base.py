# -*- coding: utf-8 -*-
'''
Created on Jun 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import string
import math
import json

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api import search
from google.appengine.api import taskqueue

from app import ndb, util


def record(model, records, agent_key, action_key, global_arguments={}):
  if len(records):
    for config in records:
      if config and isinstance(config, (list, tuple)) and config[0] and isinstance(config[0], ndb.Model):
        arguments = {}
        kwargs = {}
        entity = config[0]
        try:
          entity_arguments = config[1]
        except:
          entity_arguments = {}
        arguments.update(global_arguments)
        arguments.update(entity_arguments)
        log_entity = arguments.pop('log_entity', True)
        if len(arguments):
          for key, value in arguments.items():
            if entity._field_permissions['_records'][key]['writable']:
              kwargs[key] = value
        record = model(parent=entity.key, agent=agent_key, action=action_key, **kwargs)
        if log_entity is True:
          if entity:
            record.log_entity(entity)
        records.append(record)
  if len(records):
    recorded = ndb.put_multi(records)
    return recorded
  return


def callback(url, callbacks, agent_key_urlsafe=None, action_key_urlsafe=None):
  queues = {}
  if ndb.in_transaction():
    callbacks = callbacks[:5]
  if len(callbacks):
    for callback in callbacks:
      if isinstance(callback, (list, tuple)):
        if len(callback) == 2:
        queue_name, data = callback
        if data.get('caller_user') == None:
          data['caller_user'] = agent_key_urlsafe
        if data.get('caller_action') == None:
          data['caller_action'] = action_key_urlsafe
        if queue_name not in queues:
          queues[queue_name] = []
        queues[queue_name].append(taskqueue.Task(url=url, payload=json.dumps(data)))
  if len(queues):
    for queue_name, tasks in queues.items():
      queue = taskqueue.Queue(name=queue_name)
      queue.add(tasks, transactional=ndb.in_transaction())


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


def ndb_search(model, argument, page_size=None, urlsafe_cursor=None, namespace=None, fetch_all=True, offset=0, limit=1000):
  keys = None
  args = []
  kwds = {}
  filters = argument.get('filters')
  order_by = argument.get('order_by')
  for _filter in filters:
    if _filter['field'] == 'ancestor':
      kwds['ancestor'] = _filter['value']
      continue
    if _filter['field'] == 'key':
      keys = _filter['value']
      break
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
  cursor = Cursor(urlsafe=urlsafe_cursor)
  if keys != None:
    if not isinstance(keys, list):
      keys = [value]
    entities = ndb.get_multi(keys)
    cursor = None
    more = False
  else:
    if page_size != None and page_size > 0:
      entities, cursor, more = query.fetch_page(page_size, start_cursor=cursor)
      if cursor:
        cursor = cursor.urlsafe()
    else:
      if fetch_all:
        offset = 0
        limit = 1000
      entities = []
      more = True
      while more:
        _entities = query.fetch(limit=limit, offset=offset)
        if len(_entities):
          entities.extend(_entities)
          offset = offset + limit
          if not fetch_all:
            more = False
        else:
          more = False
      cursor = None
      more = False
  return {'entities': entities, 'search_cursor': cursor, 'search_more': more}


def document_search(index_name, argument, page_size=10, urlsafe_cursor=None, namespace=None, fields=None):
  index = search.Index(name=index_name, namespace=namespace)
  # Query String implementation start!
  query_string = ''
  sort_options = None
  filters = argument.get('filters')
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
  order_by = argument.get('order_by')
  property_config = argument.get('property')
  if order_by['operator'] == 'asc':
    default_value=property_config._order_by[order_by['field']]['default_value']['asc']
    direction = search.SortExpression.ASCENDING
  else:
    default_value=property_config._order_by[order_by['field']]['default_value']['desc']
    direction = search.SortExpression.DESCENDING
  order = search.SortExpression(expression=order_by['field'], direction=direction, default_value=default_value)
  sort_options = search.SortOptions(expressions=[order], limit=page_size)
  if urlsafe_cursor:
    cursor = search.Cursor(web_safe_string=urlsafe_cursor)
  options = search.QueryOptions(limit=page_size, returned_fields=fields, sort_options=sort_options, cursor=cursor)
  query = search.Query(query_string=query_string, options=options)
  total_matches = 0
  documents_count = 0
  documents = []
  search_cursor = None
  search_more = False
  try:
    result = index.search(query)
    total_matches = result.number_found
    if len(result.results):
      documents_count = len(result.results)
      documents = result.results
    if result.cursor != None:
      search_cursor = result.cursor.web_safe_string
      search_more = True
    else:
      search_cursor = None
      search_more = False
  except:
    raise
  finally:
    return {'documents': documents,
            'documents_count': documents_count,
            'total_matches': total_matches,
            'search_cursor': search_cursor,
            'search_more': search_more}


def document_from_entity(entity, fields={}):
  if entity and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
    doc_id = entity.key_urlsafe
    doc_fields = []
    doc_fields.append(search.AtomField(name='key', value=entity.key_urlsafe))
    doc_fields.append(search.AtomField(name='kind', value=entity.get_kind()))
    doc_fields.append(search.AtomField(name='id', value=entity.key_id_str))
    if entity.key_namespace != None:
      doc_fields.append(search.AtomField(name='namespace', value=entity.key_namespace))
    if entity.key_parent != None:
      doc_fields.append(search.AtomField(name='ancestor', value=entity.key_parent.urlsafe()))
    for field_name, field_path in fields.items():
      field_meta = get_meta(entity, field_path)
      field_value = get_attr(entity, field_path)
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
        doc_fields.append(field(name=field_name, value=field_value))
    if doc_id != None and len(doc_fields):
      return search.Document(doc_id=doc_id, fields=doc_fields)


def documents_to_indexes(documents, index_name=None):
  indexes = {}
  for document in documents:
    namespace = 'global'
    if index_name != None:
      name = index_name
    else:
      fields = document.fields
      for field in fields:
        if field.name == 'namespace':
          namespace = field.value
        if field.name == 'kind':
          name = field.value
    if namespace not in indexes:
      indexes[namespace] = {}
    if name not in indexes[namespace]:
      indexes[namespace][name] = []
    indexes[namespace][name].append(document)
  return indexes


def entities_to_indexes(entities, index_name=None):
  indexes = {}
  for entity in entities:
    namespace = 'global'
    if index_name != None:
      name = index_name
    else:
      if entity.key_namespace != None:
        namespace = entity.key_namespace
      name = entity.get_kind()
    if namespace not in indexes:
      indexes[namespace] = {}
    if name not in indexes[namespace]:
      indexes[namespace][name] = []
    indexes[namespace][name].append(entity.key_urlsafe)
  return indexes


def documents_write(indexes, documents_per_index=200):
  for namespace, names in indexes.items():
    for name, documents in names.items():
      if len(documents):
        cycles = int(math.ceil(len(documents) / documents_per_index))
        for i in range(0, cycles + 1):
          documents_partition = documents[documents_per_index*i:documents_per_index*(i+1)]
          if len(documents_partition):
            try:
              if namespace == 'global':
                index = search.Index(name=name, namespace=None)
              else:
                index = search.Index(name=name, namespace=namespace)
              index.put(documents_partition)  # Batching puts is more efficient than adding documents one at a time.
            except Exception as e:
              util.logger('INDEX FAILED! ERROR: %s' % e)
              pass


def documents_delete(indexes, documents_per_index=200):
  for namespace, names in indexes.items():
    for name, documents in names.items():
      if len(documents):
        cycles = int(math.ceil(len(documents) / documents_per_index))
        for i in range(0, cycles + 1):
          documents_partition = documents[documents_per_index*i:documents_per_index*(i+1)]
          if len(documents_partition):
            try:
              if namespace == 'global':
                index = search.Index(name=name, namespace=None)
              else:
                index = search.Index(name=name, namespace=namespace)
              index.delete(documents_partition)  # Batching puts is more efficient than adding documents one at a time.
            except Exception as e:
              util.logger('INDEX FAILED! ERROR: %s' % e)
              pass
