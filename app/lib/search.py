# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import string

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api import search

from app import ndb, util


def ndb_search(model, argument, page_size=10, urlsafe_cursor=None, namespace=None):
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
      entities = query.fetch()
      cursor = None
      more = False
  return (entities, cursor, more)


def document_search(index_name, argument, page_size=10, urlsafe_cursor=None, fields=None):
  index = search.Index(name=index_name)
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
    return (documents, documents_count, total_matches, search_cursor, search_more)
