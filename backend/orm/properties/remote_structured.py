# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from .base import *
from .base import _BaseStructuredProperty, _BaseImageProperty
from .data import SuperSearchProperty
from .values import *

__all__ = ['SuperRecordProperty', 'SuperRemoteStructuredProperty', 'SuperReferenceStructuredProperty',
           'SuperImageRemoteStructuredProperty']


class SuperRemoteStructuredProperty(_BaseStructuredProperty, Property):

  '''This property is not meant to be used as property storage. It should be always defined as virtual property.
  E.g. the property that never gets saved to the datastore.
  '''
  _indexed = False
  _repeated = False
  _readable = True
  _updateable = True
  _deleteable = True
  _autoload = False
  _value_class = RemoteStructuredPropertyValue
  search = None

  def __init__(self, modelclass, name=None, compressed=False, keep_keys=True, **kwds):
    if isinstance(modelclass, basestring):
      model = Model._kind_map.get(modelclass)
      if model is not None:
        modelclass = model
    kwds['generic'] = True
    self.search = kwds.pop('search', None)
    if self.search is None:
      self.search = {'cfg': {
          'filters': {},
          'indexes': [{'ancestor': True, 'filters': [], 'orders': []}],
      }}
    super(SuperRemoteStructuredProperty, self).__init__(name, **kwds)
    self._modelclass = modelclass

  def get_model_fields(self, **kwargs):
    return self.get_modelclass(**kwargs).get_fields()

  def _set_value(self, entity, value):
    # __set__
    property_value = self._get_value(entity)
    property_value.set(value)

  def _prepare_for_put(self, entity):
    self._get_value(entity)  # For its side effects.

  def initialize(self):
    super(SuperRemoteStructuredProperty, self).initialize()
    default_cfg = {'cfg': {'search_arguments': {'kind': self._modelclass.get_kind()},
                           'search_by_keys': False,
                           'filters': {},
                           'indexes': [{'ancestor': True, 'filters': [], 'orders': []}]}}
    tools.merge_dicts(self.search, default_cfg)
    self.search = SuperSearchProperty(**self.search)

  def get_meta(self):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    '''
    dic = super(SuperRemoteStructuredProperty, self).get_meta()
    dic['search'] = self.search
    return dic


class SuperReferenceStructuredProperty(SuperRemoteStructuredProperty):

  '''Reference structured is the same as remote, except it uses different default value class and its default flags for
  updating, deleting are always false.

  '''
  _value_class = ReferenceStructuredPropertyValue
  _updateable = False
  _deleteable = False
  _addable = False

  def __init__(self, *args, **kwargs):
    self._callback = kwargs.pop('callback', None)
    self._target_field = kwargs.pop('target_field', None)
    super(SuperReferenceStructuredProperty, self).__init__(*args, **kwargs)
    self._updateable = False
    self._deleteable = False

  def value_format(self, value, path=None):
    # reference type properties can never be updated by the client
    return tools.Nonexistent


class SuperRecordProperty(SuperRemoteStructuredProperty):

  '''Usage: '_records': SuperRecordProperty(Domain or '6')
  '''

  can_be_copied = False

  def __init__(self, *args, **kwargs):
    args = list(args)
    self._modelclass2 = args[0]
    args[0] = '0'
    self._repeated = True
    search = kwargs.get('search', {})
    if 'default' not in search:
      search['default'] = {'filters': [], 'orders': [{'field': 'logged', 'operator': 'desc'}]}
    if 'cfg' not in search:
      search['cfg'] = {
          'indexes': [{
              'ancestor': True,
              'filters': [],
              'orders': [('logged', ['desc'])]
          }],
      }
    kwargs['search'] = search
    super(SuperRecordProperty, self).__init__(*args, **kwargs)
    # Implicitly state that entities cannot be updated or deleted.
    self._updateable = False
    self._deleteable = False
    self._duplicable = False

  def get_model_fields(self, **kwargs):
    fields = super(SuperRecordProperty, self).get_model_fields(**kwargs)
    fields.update(self._modelclass2.get_fields())
    return fields

  def initialize(self):
    super(SuperRecordProperty, self).initialize()
    if isinstance(self._modelclass2, basestring):
      model = Model._kind_map.get(self._modelclass2)
      if model is None:
        raise ValueError('Could not locate model with kind %s' % self._modelclass2)
      else:
        self._modelclass2 = model


class SuperImageRemoteStructuredProperty(_BaseImageProperty, SuperRemoteStructuredProperty):

  _value_class = RemoteStructuredImagePropertyValue
