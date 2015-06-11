# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import json

from .base import *
from .base import _BaseProperty

__all__ = ['SuperPickleProperty', 'SuperJsonProperty', 'SuperSearchProperty', 'SuperPluginStorageProperty']


class SuperPickleProperty(_BaseProperty, PickleProperty):

  def value_format(self, value):
    value = self._property_value_format(value)
    if value is tools.Nonexistent:
      return value
    return value


class SuperJsonProperty(_BaseProperty, JsonProperty):

  def value_format(self, value):
    value = self._property_value_format(value)
    if value is tools.Nonexistent:
      return value
    if isinstance(value, basestring):
      return json.loads(value)
    else:
      return value

  def get_search_document_field(self, value):
    if self._repeated:
      value = ' '.join(map(lambda v: json.dumps(v), value))
    else:
      value = json.dumps(value)
    return search.TextField(name=self.search_document_field_name, value=value)


class SuperSearchProperty(SuperJsonProperty):

  def __init__(self, *args, **kwargs):
    '''Filters work like this:
    First you configure SuperSearchProperty with search_arguments, filters and indexes parameters.
    This configuration takes place at the property definition place.
    cfg = {
      'use_search_engine': True,
      'search_arguments': {'kind': '35'...},
      'ancestor_kind': '35',
      'filters': {'field1': SuperStringProperty(required=True)}},  # With this config you define expected filter value property.
      'orders': {'created': {'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}}},  # This parameter is used for search engine default values!
      'indexes': [{'ancestor': True, 'filters': [('field1', [op1, op2]), ('field2', [op1]), ('field3', [op2])], 'orders': [('field1', ['asc', 'desc'])]},
                  {'ancestor': False, 'filters': [('field1', [op1]), ('field2', [op1])], 'orders': [('field1', ['asc', 'desc'])]}]
    }
    search = SuperSearchProperty(cfg=cfg)

    Search values that are provided with input will be validated trough SuperSearchProperty().value_format() function.
    Example of search values that are provided in input after processing:
    context.input['search'] = {'kind': '37',
                               'ancestor': 'fjdkahsekuarg4wi784wnvsxiu487',
                               'namespace': 'wjbryj4gr4y57jtgnfj5959',
                               'projection': ['name'],
                               'group_by': ['name'],
                               'options': {'limit': 10000, cursor: '34987hgehevbjeriy3478dsbkjbdskhrsgkugsrkbsg'},
                               'default_options': {'limit': 10000, cursor: '34987hgehevbjeriy3478dsbkjbdskhrsgkugsrkbsg'},
                               'filters': [{'field': 'name', 'operator': '==', 'value': 'Test'}],
                               'orders': [{'field': 'name', 'operator': 'asc'}],
                               'keys': [key1, key2, key3]}

    '''
    self._cfg = kwargs.pop('cfg', {})
    super(SuperSearchProperty, self).__init__(*args, **kwargs)

  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).

    '''
    dic = super(SuperSearchProperty, self).get_meta()
    dic['cfg'] = self._cfg
    return dic

  def _clean_format(self, values):
    allowed_arguments = ['kind', 'ancestor', 'projection',
                         'group_by', 'options', 'default_options',
                         'filters', 'orders', 'keys', 'query_string']
    for value_key, value in values.items():
      if value_key not in allowed_arguments:
        del values[value_key]

  def _kind_format(self, values):
    kind = values.get('kind')
    model = Model._kind_map.get(kind)
    if not model:
      raise FormatError('invalid_model_kind')

  def _ancestor_format(self, values):
    ancestor = values.get('ancestor')
    if ancestor is not None:
      ancestor_kind = self._cfg.get('ancestor_kind')
      if ancestor_kind is not None:
        # sometimes the parent is not stored in database, so just shallow validation should suffice
        values['ancestor'] = BaseVirtualKeyProperty(kind=ancestor_kind, required=True).value_format(ancestor)
      else:
        del values['ancestor']

  def _keys_format(self, values):
    keys = values.get('keys')
    ancestor = values.get('ancestor')
    if keys is not None:
      if self._cfg.get('search_by_keys'):
        values['keys'] = BaseKeyProperty(kind=values['kind'], repeated=True).value_format(keys)
      else:
        del values['keys']

  def _projection_group_by_format(self, values):
    def list_format(list_values):
      if not isinstance(list_values, (tuple, list)):
        raise FormatError('not_list')
      remove_list_values = []
      for value in list_values:
        if not isinstance(value, str):
          remove_list_values.append(value)
      for value in remove_list_values:
        list_values.remove(value)

    projection = values.get('projection')
    if projection is not None:
      list_format(projection)
    group_by = values.get('group_by')
    if group_by is not None:
      list_format(group_by)

  def _filters_orders_format(self, values):
    ''''filters': [{'field': 'name', 'operator': '==', 'value': 'Test'}]
       'orders': [{'field': 'name', 'operator': 'asc'}]

    '''
    def _validate(cfg_values, input_values, method):
      # cfg_filters = [('name', ['==', '!=']), ('age', ['>=', '<=']), ('sex', ['=='])]
      # input_filters = [{'field': 'name', 'operator': '==', 'value': 'Mia'}]
      # cfg_orders = [('name', ['asc'])]
      # input_orders = [{'field': 'name', 'operator': 'asc'}]
      if len(cfg_values) != len(input_values):
        raise FormatError('%s_values_mismatch' % method)  # @todo Write this error correctly!
      for i, input_value in enumerate(input_values):  # @todo If input_values length is 0, and above validation passes, than there should not be any errors!?
        cfg_value = cfg_values[i]
        if input_value['field'] != cfg_value[0]:
          raise FormatError('expected_%s_field_%s_at_%s' % (method, cfg_value[0], i))
        if input_value['operator'] not in cfg_value[1]:
          raise FormatError('expected_%s_operator_%s_at_%s' % (method, cfg_value[1], i))

    if self._cfg.get('search_by_keys') and 'keys' in values:
      return values
    defaults = self._default
    # if defaults are defined then load them if the user did not supply them
    if not defaults:
      defaults = {}
    ancestor = values.get('ancestor')
    if 'filters' not in values:
      values['filters'] = defaults.get('filters', [])
    if 'orders' not in values:
      values['orders'] = defaults.get('orders', [])
    filters = values.get('filters')
    orders = values.get('orders')
    cfg_filters = self._cfg.get('filters', {})
    cfg_indexes = self._cfg['indexes']
    success = False
    e = 'unknown'
    for cfg_index in cfg_indexes:
      try:
        cfg_index_ancestor = cfg_index.get('ancestor')
        cfg_index_filters = cfg_index.get('filters', [])
        cfg_index_orders = cfg_index.get('orders', [])
        if ancestor is not None:
          if not cfg_index_ancestor:  # @todo Not sure if we have to enforce ancestor if index_cfg.get('ancestor') is True!?
            raise FormatError('ancestor_not_allowed')
        _validate(cfg_index_filters, filters, 'filter')
        _validate(cfg_index_orders, orders, 'order')
        for input_filter in filters:
          input_field = input_filter['field']
          input_value = input_filter['value']
          cfg_field = cfg_filters[input_field]
          input_filter['value'] = cfg_field.value_format(input_value)
        success = True
        break
      except Exception as e:
        pass
    if success is not True:
      if isinstance(e, Exception):
        e = e.message
      raise FormatError(e)

  def _datastore_query_options_format(self, values):
    def options_format(options_values):
      for value_key, value in options_values.items():
        if value_key in ['keys_only', 'produce_cursors']:
          if not isinstance(value, bool):
            del options_values[value_key]
        elif value_key == 'limit':
          if not isinstance(value, (int, long)):
            raise FormatError('limit_value_incorrect')
          if value == 0:
            del options_values[value_key]
        elif value_key in ['batch_size', 'prefetch_size', 'deadline']:
          if not isinstance(value, (int, long)):
            del options_values[value_key]
        elif value_key in ['start_cursor', 'end_cursor']:
          try:
            options_values[value_key] = Cursor(urlsafe=value)
          except:
            del options_values[value_key]
        elif value_key == 'read_policy':
          if not isinstance(value, EVENTUAL_CONSISTENCY):  # @todo Not sure if this is ok!? -- @reply i need to check this
            del options_values[value_key]
        else:
          del options_values[value_key]

    default_options = values.get('default_options')
    if default_options is not None:
      options_format(default_options)
    options = values.get('options', {})
    if 'limit' not in options.keys():
      raise FormatError('limit_value_missing')
    options_format(options)

  def _search_query_orders_format(self, values):
    orders = values.get('orders')
    cfg_orders = self._cfg.get('orders', {})
    if orders is not None:
      for _order in orders:
        cfg_order = cfg_orders.get(_order['field'], {})
        _order['default_value'] = cfg_order.get('default_value', {})

  def _search_query_options_format(self, values):
    options = values.get('options', {})
    if 'limit' not in options.keys():
      raise FormatError('limit_value_missing')
    for value_key, value in options.items():
      if value_key == 'limit':
        if not isinstance(value, (int, long)):
          raise FormatError('limit_value_incorrect')
      elif value_key in ['cursor']:
        try:
          options[value_key] = search.Cursor(web_safe_string=value)
        except:
          del options[value_key]
      else:
        del options[value_key]

  def value_format(self, values):
    values = super(SuperSearchProperty, self).value_format(values)
    override = self._cfg.get('search_arguments', {})
    tools.override_dict(values, override)
    self._clean_format(values)
    self._kind_format(values)
    self._ancestor_format(values)
    self._keys_format(values)
    self._projection_group_by_format(values)
    self._filters_orders_format(values)
    if self._cfg.get('use_search_engine', False):
      self._search_query_orders_format(values)
      self._search_query_options_format(values)
    else:
      self._datastore_query_options_format(values)
    values['property'] = self
    return values

  def build_datastore_query_filters(self, value):
    _filters = value.get('filters')
    filters = []
    model = Model._kind_map.get(value.get('kind'))
    if _filters is None:
      return filters
    for _filter in _filters:
      field = tools.get_attr(model, _filter['field'])
      op = _filter['operator']
      value = _filter['value']
      # here we could use
      # field._comparison(op, value)
      # https://code.google.com/p/appengine-ndb-experiment/source/browse/ndb/model.py?r=6b3f88b663a82831e9ecee8adbad014ff774c365#831
      if op == '==':  # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this also needs improvements
        filters.append(field == value)
      elif op == '!=':
        filters.append(field != value)
      elif op == '>':
        filters.append(field > value)
      elif op == '<':
        filters.append(field < value)
      elif op == '>=':
        filters.append(field >= value)
      elif op == 'IN':
        filters.append(field.IN(value))
      elif op == 'ALL_IN':
        for v in value:
          filters.append(field == v)
      elif op == 'contains':
        letters = list(string.printable)
        try:
          last = letters[letters.index(value[-1].lower()) + 1]
          filters.append(field >= value)
          filters.append(field < last)
        except ValueError as e:  # Value not in the letter scope, šččđčžćč for example.
          filters.append(field == value)
    return filters

  def build_datastore_query_orders(self, value):
    _orders = value.get('orders')
    orders = []
    model = Model._kind_map.get(value.get('kind'))
    if _orders is None:
      return orders
    for _order in _orders:
      field = getattr(model, _order['field'])
      op = _order['operator']
      if op == 'asc':
        orders.append(field)
      else:
        orders.append(-field)
    return orders

  def build_datastore_query_options(self, value):
    options = value.get('options', {})
    return QueryOptions(**options)

  def build_datastore_query_default_options(self, value):
    default_options = value.get('default_options', {})
    return QueryOptions(**default_options)

  def build_datastore_query(self, value):
    filters = self.build_datastore_query_filters(value)
    orders = self.build_datastore_query_orders(value)
    default_options = self.build_datastore_query_default_options(value)
    return Query(kind=value.get('kind'), ancestor=value.get('ancestor'),
                 namespace=value.get('namespace'), projection=value.get('projection'),
                 group_by=value.get('group_by'), default_options=default_options).filter(*filters).order(*orders)

  def build_search_query_string(self, value):
    query_string = value.get('query_string', '')
    if query_string:
      return query_string
    _filters = value.get('filters')
    filters = []
    kind = value.get('kind')
    if kind:
      filters.append('(kind=' + kind + ')')
    ancestor = value.get('ancestor')
    if ancestor:
      filters.append('(ancestor=' + ancestor + ')')
    for _filter in _filters:
      field = _filter['field']
      op = _filter['operator']
      value = _filter['value']
      if field == 'query_string':
        filters.append(value)
        break
      if op == '==':  # here we need more ifs for >=, <=, <, >, !=, IN ... OR ... ? this also needs improvements
        filters.append('(' + field + '=' + value + ')')
      elif op == '!=':
        filters.append('(NOT ' + field + '=' + value + ')')
      elif op == '>':
        filters.append('(' + field + '>' + value + ')')
      elif op == '<':
        filters.append('(' + field + '<' + value + ')')
      elif op == '>=':
        filters.append('(' + field + '>=' + value + ')')
      elif op == '<=':
        filters.append('(' + field + '<=' + value + ')')
      elif op == 'IN':
        filters.append('(' + ' OR '.join(['(' + field + '=' + v + ')' for v in value]) + ')')
    return ' AND '.join(filters)

  def build_search_query_sort_options(self, value):
    _orders = value.get('orders')
    options = value.get('options', {})
    direction = {'asc': search.SortExpression.ASCENDING, 'desc': search.SortExpression.DESCENDING}
    orders = []
    for _order in _orders:
      field = _order['field']
      op = _order['operator']
      default_value = _order['default_value']
      orders.append(search.SortExpression(expression=field, direction=direction.get(op),
                                          default_value=default_value.get(op)))
    return search.SortOptions(expressions=orders, limit=options.get('limit'))

  def build_search_query_options(self, value):
    sort_options = self.build_search_query_sort_options(value)
    options = value.get('options', {})
    return search.QueryOptions(limit=options.get('limit'),
                               returned_fields=value.get('projection'),
                               sort_options=sort_options, cursor=options.get('cursor'))

  def build_search_query(self, value):
    query_string = self.build_search_query_string(value)
    query_options = self.build_search_query_options(value)
    return search.Query(query_string=query_string, options=query_options)


class SuperPluginStorageProperty(SuperPickleProperty):

  _kinds = None

  def __init__(self, *args, **kwargs):
    args = list(args)
    if isinstance(args[0], (tuple, list)):
      self._kinds = args[0]
    if isinstance(args[0], basestring):
      self._kinds = (args[0],)
    args = args[1:]
    super(SuperPluginStorageProperty, self).__init__(*args, **kwargs)

  def _get_value(self, entity):
    values = super(SuperPluginStorageProperty, self)._get_value(entity)
    if values:
      sequence = len(values)
      for val in values:
        val.read()
        sequence -= 1
        val._sequence = sequence
    return values

  def _set_value(self, entity, value):
    # __set__
    # plugin storage needs just to generate key if its non existant, it cannot behave like local struct and remote struct
    # because generally its not in its nature to behave like that
    # its just pickling of data with validation.
    for val in value[:]:
      if val._state == 'deleted':
        value.remove(val)
        continue
      if not val.key:
        val.generate_unique_key()
      for field_key, field in val.get_fields().iteritems():
        if hasattr(field, 'is_structured') and field.is_structured:
          structured = getattr(val, field_key)
          structured.pre_update()
    return super(SuperPluginStorageProperty, self)._set_value(entity, value)

  def value_format(self, value, path=None):
    if path is None:
      path = self._code_name
    value = self._property_value_format(value)
    if value is tools.Nonexistent:
      return value
    out = []
    if not isinstance(value, list):
      raise FormatError('expected_list')
    for v in value:
      out.append(self._structured_property_format(v, path))
    return out

  def _structured_property_field_format(self, fields, values, path):
    _state = allowed_state(values.get('_state'))
    _sequence = values.get('_sequence')
    key = values.get('key')
    for value_key, value in values.items():
      field = fields.get(value_key)
      if field:
        if hasattr(field, 'value_format'):
          new_path = '%s.%s' % (path, field._code_name)
          try:
            if hasattr(field, '_structured_property_field_format'):
              val = field.value_format(value, new_path)
            else:
              val = field.value_format(value)
          except FormatError as e:
            if isinstance(e.message, dict):
              for k, v in e.message.iteritems():
                if k not in errors:
                  errors[k] = []
                if isinstance(v, (list, tuple)):
                  errors[k].extend(v)
                else:
                  errors[k].append(v)
            else:
              if e.message not in errors:
                errors[e.message] = []
              errors[e.message].append(new_path)
            continue
          if val is tools.Nonexistent:
            del values[value_key]
          else:
            values[value_key] = val
        else:
          del values[value_key]
      else:
        del values[value_key]
    if key:
      values['key'] = Key(urlsafe=key)
    values['_state'] = _state  # Always keep track of _state for rule engine!
    if _sequence is not None:
      values['_sequence'] = _sequence

  def _structured_property_format(self, entity_as_dict, path):
    provided_kind_id = entity_as_dict.get('kind')
    fields = self.get_model_fields(kind=provided_kind_id)
    entity_as_dict.pop('class_', None)  # Never allow class_ or any read-only property to be set for that matter.
    try:
      self._structured_property_field_format(fields, entity_as_dict, path)
    except FormatError as e:
      raise FormatError(e.message)
    modelclass = self.get_modelclass(kind=provided_kind_id)
    return modelclass(**entity_as_dict)

  def get_modelclass(self, kind):
    if self._kinds and kind:
      if kind:
        _kinds = []
        for other in self._kinds:
          if isinstance(other, Model):
            _the_kind = other.get_kind()
          else:
            _the_kind = other
          _kinds.append(_the_kind)
        if kind not in _kinds:
          raise ValueError('Expected Kind to be one of %s, got %s' % (kind, _kinds))
        model = Model._kind_map.get(kind)
        return model

  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()

  def get_meta(self):
    out = super(SuperPluginStorageProperty, self).get_meta()
    out['kinds'] = self._kinds
    return out

  def property_keywords_format(self, kwds, skip_kwds):
    super(SuperPluginStorageProperty, self).property_keywords_format(kwds, skip_kwds)
    if 'kinds' not in skip_kwds:
      kwds['kinds'] = map(lambda x: unicode(x), kwds['kinds'])
