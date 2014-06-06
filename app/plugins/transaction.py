# -*- coding: utf-8 -*-
'''
Created on Jun 2, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import collections

from app import ndb, memcache, util
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


class JournalFields(ndb.BaseModel):
  
  def run(self, context):
    context.tmp['available_fields'] = __JOURNAL_FIELDS.keys()


class JournalUpdateRead(ndb.BaseModel):
  
  def run(self, context):
    '''key.id() = prefix_<user supplied value>
    key.id() defines constraint of unique journal code (<user supplied value> part of the key.id) per domain.
    It also ensures that code can not be changed for journal once it has been defined! In OpenERP however,
    journal codes can be changed all the time, as long as they are unique per company. Another observation
    regarding OpenERP journals is that the initial journal code is used for defining journal entry
    sequencing pattern, and the pattern doesn't change on subseqent code changes however,
    it can be changed with user intervention in sequence configuration.
    In OpenERP, journals can have up to 5 characters of code length.
    
    '''
    code = '49_%s' % context.input.get('_code')  # @todo Not sure if we need to salt key id here?
    entity_key = context.model.build_key(code, namespace=context.namespace)
    entity = entity_key.get()
    if entity is None:
      entity = context.model(key=entity_key)
    context.entities[context.model.get_kind()] = entity
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])


class JournalRead(ndb.BaseModel):
  
  def run(self, context):
    context.entities[context.model.get_kind()]._code = context.entities[context.model.get_kind()].key_id_str[3:]
    context.values[context.model.get_kind()]._code = copy.deepcopy(context.entities[context.model.get_kind()]._code)


class JournalSet(ndb.BaseModel):
  
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


class CategoryUpdateRead(ndb.BaseModel):
  
  def run(self, context):
    '''key.id() = prefix_<user supplied value>
    key.id() defines constraint of unique categoty code (<user supplied value> part of the key.id) per domain.
    It also ensures that code can not be changed for category once it has been defined! In OpenERP however,
    account codes can be changed as long as they were not used for recording journal entries and are unique per company.
    In OpenERP, accounts can have up to 64 characters of code length.
    
    '''
    code = '47_%s' % context.input.get('_code')  # @todo Not sure if we need to salt key id here?
    entity_key = context.model.build_key(code, namespace=context.namespace)
    entity = entity_key.get()
    if entity is None:
      entity = context.model(key=entity_key)
    context.entities[context.model.get_kind()] = entity
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])


class CategoryRead(ndb.BaseModel):
  
  def run(self, context):
    context.entities[context.model.get_kind()]._code = context.entities[context.model.get_kind()].key_id_str[3:]
    context.values[context.model.get_kind()]._code = copy.deepcopy(context.entities[context.model.get_kind()]._code)


class CategorySet(ndb.BaseModel):
  
  def run(self, context):
    context.values[context.model.get_kind()].parent_record = context.input.get('parent_record')
    context.values[context.model.get_kind()].name = context.input.get('name')
    context.values[context.model.get_kind()].active = context.input.get('active')
    context.values[context.model.get_kind()].description = context.input.get('description')
    complete_name = ndb.make_complete_name(context.values[context.model.get_kind()], 'name', parent_property='parent_record')
    context.values[context.model.get_kind()].complete_name = complete_name


'''
class Write(ndb.BaseModel):
  
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