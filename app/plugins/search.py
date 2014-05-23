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


__SEARCH_FIELDS = {'SuperStringProperty': search.TextField,
                   'SuperJsonProperty': search.TextField,
                   'SuperTextProperty': search.HtmlField,
                   'SuperKeyProperty': search.AtomField,
                   'SuperImageKeyProperty': search.AtomField,
                   'SuperBlobKeyProperty': search.AtomField,
                   'SuperBooleanProperty': search.AtomField,
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
    for field_name in self.fields:
      field_value = get_attr(context.entities[kind_id], field_name)
      field_meta = get_meta(context.entities[kind_id], field_name)
      field = get_search_field(field_meta.__class__.__name__)
      if field_meta._repeated:
        if field_meta.__class__.__name__ in ['SuperKeyProperty']:
          field_value = ' '.join(field_value.urlsafe())
        else:
          field_value = ' '.join(field_value)
        field = get_search_field('SuperStringProperty')
      if field_meta.__class__.__name__ in ['SuperJsonProperty', 'SuperSearchProperty']:
        field_value = str(field_value)
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
    
    # @todo Query String has to be implemented here, in order for this to work!
    query_string = ''
    sort_options = None
    search = context.input.get('search')
    if search:
      filters = search.get('filters')
      args = []
      for _filter in filters:
        field = _filter['field']
        op = _filter['operator']
        value = _filter['value']
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
      order_by = search.get('order_by')
      if order_by['operator'] == 'asc':
        direction = search.SortExpression.ASCENDING
      else:
        direction = search.SortExpression.DESCENDING
      order = search.SortExpression(expression=order_by['field'], direction=direction)
      sort_options = search.SortOptions(expressions=[order], limit=self.page_size)
    cursor = search.Cursor(web_safe_string=context.input.get('search_cursor'))
    options = search.QueryOptions(limit=self.page_size, returned_fields=self.fields, sort_options=sort_options, cursor=cursor)
    query = search.Query(query_string=query_string, options=options)
    context.documents = []
    try:
      result = index.search(query)
      context.total_matches = result.number_found
      if len(result.results):
        context.documents_count = len(result.results)
        context.documents = result.results
      if result.cursor != None:
        context.search_cursor = result.cursor.web_safe_string
        context.search_more = True
      else:
        context.search_cursor = None
        context.search_more = False
    except:
      pass

class Entities(event.Plugin):
  
  def run(self, context):
    if len(context.documents):
      context.entities = ndb.get_multi([document.doc_id for document in context.documents])
