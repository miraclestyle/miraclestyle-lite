# -*- coding: utf-8 -*-
'''
Created on Jun 2, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import collections

from app import ndb, settings, memcache, util
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


__JOURNAL_FIELDS = collections.OrderedDict([('String', ndb.SuperStringProperty),
                                            ('Integer', ndb.SuperIntegerProperty),
                                            ('Decimal', ndb.SuperDecimalProperty),
                                            ('Float', ndb.SuperFloatProperty),
                                            ('DateTime', ndb.SuperDateTimeProperty),
                                            ('Boolean', ndb.SuperBooleanProperty),
                                            ('Reference', ndb.SuperKeyProperty),
                                            ('Text', ndb.SuperTextProperty),
                                            ('JSON', ndb.SuperJsonProperty)])


class JournalFields(event.Plugin):
  
  def run(self, context):
    context.tmp['available_fields'] = __JOURNAL_FIELDS.keys()


class JournalRead(event.Plugin):
  
  def run(self, context):
    code = 'j_%s' % context.input.get('code')
    entity_key = context.model.build_key(code, namespace=context.namespace)
    entity = entity_key.get()
    if entity is None:
      entity = context.model(key=entity_key)
    context.entities[context.model.get_kind()] = entity
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])


class JournalSet(event.Plugin):
  
  def run(self, context):
    
    def build_field(model, field):
      return model(name=field.get('name'),
                   verbose_name=field.get('verbose_name'),
                   required=field.get('required'),
                   repeated=field.get('repeated'),
                   indexed=field.get('indexed'),
                   default=field.get('default'),
                   choices=field.get('choices'))
    
    input_entry_fields = context.input.get('entry_fields')
    input_line_fields = context.input.get('line_fields')
    entry_fields = []
    line_fields = []
    for field in input_entry_fields:
      model = __JOURNAL_FIELDS.get(field.get('type'))
      entry_fields.append(build_field(model, field))
    for field in input_line_fields:
      model = __JOURNAL_FIELDS.get(field.get('type'))
      line_fields.append(build_field(model, field))
    context.values[context.model.get_kind()].name = context.input.get('name')
    context.values[context.model.get_kind()].entry_fields = entry_fields
    context.values[context.model.get_kind()].line_fields = line_fields


'''
class Write(event.Plugin):
  
  @ndb.transactional(xg=True)  # @todo Study material. Perhaps 'context.transaction.group' can be context.entity, and 'context.transaction.entities' could be context.entity._entries ??
  def run(self, context):
    group = context.transaction.group
    if not group:
      group = Group(namespace=context.auth.domain.key.urlsafe())  # ??
      group.put()
      group_key = group.key  # Put main key.
      for key, entry in context.transaction.entities.items():
        entry.set_key(parent=group_key)  # parent key for entry
        entry_key = entry.put()
        lines = []
        for i, line in enumerate(entry._lines):
          line.set_key(parent=entry_key, id=i)  # @todo Parent key for line, and if posible, sequence value should be key.id?
          lines.append(line)
          ndb.put_multi(lines)
'''