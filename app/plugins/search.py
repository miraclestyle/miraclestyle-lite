# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import string

from google.appengine.api import search

from app import ndb, settings
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr, get_meta


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


def _is_structured_field(field):
  '''Checks if the provided field is instance of one of the structured properties,
  and if the '_modelclass' is set.
  
  '''
  return isinstance(field, (ndb.SuperStructuredProperty, ndb.SuperLocalStructuredProperty)) and field._modelclass


class Write(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  index_name = ndb.SuperStringProperty('6', indexed=False)
  fields = ndb.SuperStringProperty('7', indexed=False, repeated=True)
  
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
    doc_id = context.entities[kind_id].key_urlsafe
    fields = []
    fields.append(search.AtomField(name='key', value=context.entities[kind_id].key_urlsafe))
    fields.append(search.AtomField(name='kind', value=kind_id))
    fields.append(search.AtomField(name='id', value=context.entities[kind_id].key_id_str))
    if context.entities[kind_id].key_namespace != None:
      fields.append(search.AtomField(name='namespace', value=context.entities[kind_id].key_namespace))
    if context.entities[kind_id].key_parent != None:
      fields.append(search.AtomField(name='ancestor', value=context.entities[kind_id].key_parent.urlsafe()))
    for field_name in self.fields:
      field_meta = get_meta(context.entities[kind_id], field_name)
      field_value = get_attr(context.entities[kind_id], field_name)
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


class Delete(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  index_name = ndb.SuperStringProperty('6', indexed=False)
  
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
    doc_id = context.entities[kind_id].key_urlsafe
    if doc_id != None:
      try:
        index = search.Index(name=index_name)
        index.delete(doc_id)  # Batching deletes is more efficient than handling them one at a time.
      except:
        pass


class Search(event.Plugin):
  
  kind_id = ndb.SuperStringProperty('5', indexed=False)
  index_name = ndb.SuperStringProperty('6', indexed=False)
  fields = ndb.SuperStringProperty('7', indexed=False, repeated=True)
  page_size = ndb.SuperIntegerProperty('8', indexed=False, required=True, default=10)
  
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
    search_config = context.input.get('search')
    if search_config:
      filters = search_config.get('filters')
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
      order_by = search_config.get('order_by')
      property_config = search_config.get('property')
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
    
class OutputSearch(event.Plugin):
  
  def run(self, context):
    context.entities = []
    for document in context.search_documents:
      result = {}
      result['doc_id'] = document.doc_id
      result['language'] = document.language
      result['rank'] = document.rank
      fields = document.fields
      for field in fields:
        result[field.name] = field.value
      context.entities.append(result)

class Entities(event.Plugin):
  
  def run(self, context):
    if len(context.search_documents):
      context.entities = ndb.get_multi([document.doc_id for document in context.search_documents])
