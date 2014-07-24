# -*- coding: utf-8 -*-
'''
Created on Jun 2, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import collections

from app import orm
from app.util import *


class JournalFields(orm.BaseModel):
  
  def run(self, context):
    journal_fields = collections.OrderedDict([('String', orm.SuperStringProperty),
                                              ('Integer', orm.SuperIntegerProperty),
                                              ('Decimal', orm.SuperDecimalProperty),
                                              ('Float', orm.SuperFloatProperty),
                                              ('DateTime', orm.SuperDateTimeProperty),
                                              ('Boolean', orm.SuperBooleanProperty),
                                              ('Reference', orm.SuperKeyProperty),
                                              ('Text', orm.SuperTextProperty),
                                              ('JSON', orm.SuperJsonProperty)])
    context._available_fields = journal_fields.keys()


'''
There was Specialized Journal Read plugin that can be handeled by base Read plugin.

code = '49_%s' % context.input.get('_code')  # @todo Not sure if we need to salt key id here?
entity_key = context.model.build_key(code, namespace=context.namespace)

key.id() = prefix_<user supplied value>
key.id() defines constraint of unique journal code (<user supplied value> part of the key.id) per domain.
It also ensures that code can not be changed for journal once it has been defined! In OpenERP however,
journal codes can be changed all the time, as long as they are unique per company. Another observation
regarding OpenERP journals is that the initial journal code is used for defining journal entry
sequencing pattern, and the pattern doesn't change on subseqent code changes however,
it can be changed with user intervention in sequence configuration.
In OpenERP, journals can have up to 5 characters of code length.
'''


# @todo This has to be resolved once we solve this input set strategy.
class JournalSet(orm.BaseModel):
  
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
    context._journal.name = context.input.get('name')
    context._journal.entry_fields = entry_fields
    context._journal.line_fields = line_fields


'''
There was Specialized Category Read plugin that can be handeled by base Read plugin.

code = '47_%s' % context.input.get('_code')  # @todo Not sure if we need to salt key id here?
entity_key = context.model.build_key(code, namespace=context.namespace)

key.id() = prefix_<user supplied value>
key.id() defines constraint of unique categoty code (<user supplied value> part of the key.id) per domain.
It also ensures that code can not be changed for category once it has been defined! In OpenERP however,
account codes can be changed as long as they were not used for recording journal entries and are unique per company.
In OpenERP, accounts can have up to 64 characters of code length.
'''


# @todo This has to be resolved once we solve this input set strategy.
class CategorySet(orm.BaseModel):
  
  def run(self, context):
    context._category.parent_record = context.input.get('parent_record')
    context._category.name = context.input.get('name')
    context._category.active = context.input.get('active')
    context._category.description = context.input.get('description')
    complete_name = orm.make_complete_name(context.entities[context.model.get_kind()], 'name', parent_property='parent_record')
    context._category.complete_name = complete_name
