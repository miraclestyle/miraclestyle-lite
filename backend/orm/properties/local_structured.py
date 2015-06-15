# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from google.appengine.ext.ndb.model import _BaseValue

from .base import *
from .base import _BaseStructuredProperty, _BaseImageProperty
from .values import *

__all__ = ['SuperLocalStructuredProperty', 'SuperStructuredProperty',
           'SuperMultiLocalStructuredProperty', 'SuperImageLocalStructuredProperty',
           'SuperImageStructuredProperty']


class SuperLocalStructuredProperty(_BaseStructuredProperty, LocalStructuredProperty):

  _value_class = LocalStructuredPropertyValue
  _autoload = True  # always automatically load structured props since they dont take any io

  def __init__(self, *args, **kwargs):
    super(SuperLocalStructuredProperty, self).__init__(*args, **kwargs)
    self._keep_keys = True  # all keys must be stored by default


class SuperStructuredProperty(_BaseStructuredProperty, StructuredProperty):

  _value_class = LocalStructuredPropertyValue
  _autoload = True  # always automatically load structured props since they dont take any io

  def _serialize(self, entity, pb, prefix='', parent_repeated=False, projection=None):
    '''Internal helper to serialize this property to a protocol buffer.
    Subclasses may override this method.
    Args:
      entity: The entity, a Model (subclass) instance.
      pb: The protocol buffer, an EntityProto instance.
      prefix: Optional name prefix used for StructuredProperty
        (if present, must end in '.').
      parent_repeated: True if the parent (or an earlier ancestor)
        is a repeated Property.
      projection: A list or tuple of strings representing the projection for
        the model instance, or None if the instance is not a projection.
    '''
    values = self._get_base_value_unwrapped_as_list(entity)
    for value in values:
      if value is not None:
        name = prefix + self._name + '.' + 'stored_key'
        p = pb.add_raw_property()
        p.set_name(name)
        p.set_multiple(self._repeated or parent_repeated)
        v = p.mutable_value()
        ref = value.key.reference()
        rv = v.mutable_referencevalue()  # A Reference
        rv.set_app(ref.app())
        if ref.has_name_space():
          rv.set_name_space(ref.name_space())
        for elem in ref.path().element_list():
          rv.add_pathelement().CopyFrom(elem)
    return super(SuperStructuredProperty, self)._serialize(
        entity, pb, prefix=prefix, parent_repeated=parent_repeated,
        projection=projection)

  def _deserialize(self, entity, p, depth=1):
    stored_key = 'stored_key'
    super(SuperStructuredProperty, self)._deserialize(entity, p, depth)
    basevalues = self._retrieve_value(entity)
    if not self._repeated:
      basevalues = [basevalues]
    for basevalue in basevalues:
      if isinstance(basevalue, _BaseValue):
        # NOTE: It may not be a _BaseValue when we're deserializing a
        # repeated structured property.
        subentity = basevalue.b_val
      if hasattr(subentity, stored_key):
        subentity.key = subentity.store_key
        delattr(subentity, stored_key)
      elif stored_key in subentity._properties:
        subentity.key = subentity._properties[stored_key]._get_value(subentity)
        del subentity._properties[stored_key]


class SuperMultiLocalStructuredProperty(_BaseStructuredProperty, LocalStructuredProperty):

  _kinds = None
  _value_class = LocalStructuredPropertyValue

  def __init__(self, *args, **kwargs):
    '''So basically:
    argument: SuperMultiLocalStructuredProperty(('3' or ModelItself, '21' or ModelItself))
    will allow instancing of both 51 and 21 that is provided from the input.
    This property should not be used for datastore. Its specifically used for arguments.
    Currently we do not have the code that would allow this to be saved in datastore:
    Entity.images
    => Image
    => OtherTypeOfEntity
    => OtherTypeOfEntityA

    In order to support different instances in the repeated list we would also need to store KIND and implement
    additional logic that will load proper model based on protobuff.
    '''
    args = list(args)
    if isinstance(args[0], (tuple, list)):
      self._kinds = args[0]
      set_model1 = Model._kind_map.get(args[0][0])  # by default just pass the first one
      if set_model1 is not None:
        args[0] = set_model1
    if isinstance(args[0], basestring):
      set_model1 = Model._kind_map.get(args[0])  # by default just pass the first one
      if set_model1 is not None:  # do not set it if it wasnt scanned yet
        args[0] = set_model1
    super(SuperMultiLocalStructuredProperty, self).__init__(*args, **kwargs)

  def get_modelclass(self, kind=None, **kwds):
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
          raise ValueError('Expected Kind to be one of %s, got %s' % (_kinds, kind))
        model = Model._kind_map.get(kind)
        return model
    return super(SuperMultiLocalStructuredProperty, self).get_modelclass()

  def get_meta(self):
    out = super(SuperMultiLocalStructuredProperty, self).get_meta()
    out['kinds'] = self._kinds
    return out

  def property_keywords_format(self, kwds, skip_kwds):
    super(SuperMultiLocalStructuredProperty, self).property_keywords_format(kwds, skip_kwds)
    if 'kinds' not in skip_kwds:
      kwds['kinds'] = map(lambda x: unicode(x), kwds['kinds'])


class SuperImageLocalStructuredProperty(_BaseImageProperty, SuperLocalStructuredProperty):

  _value_class = LocalStructuredImagePropertyValue


class SuperImageStructuredProperty(_BaseImageProperty, SuperStructuredProperty):

  _value_class = LocalStructuredImagePropertyValue
