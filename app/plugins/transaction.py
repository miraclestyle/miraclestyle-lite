# -*- coding: utf-8 -*-
'''
Created on Jun 2, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import collections

from app import ndb, util


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


class JournalRead(ndb.BaseModel):
  
  def run(self, context):
    context.entities[context.model.get_kind()]._code = context.entities[context.model.get_kind()].key_id_str[3:]


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
    context.entities[context.model.get_kind()].name = context.input.get('name')
    context.entities[context.model.get_kind()].entry_fields = entry_fields
    context.entities[context.model.get_kind()].line_fields = line_fields


class JournalReadActions(ndb.BaseModel):
  
  page_size = ndb.SuperIntegerProperty('1', indexed=False, required=True, default=10)
  read_all = ndb.SuperBooleanProperty('2', indexed=False, default=False)
  
  def run(self, context):
    Action = context.models['56']
    ancestor = context.entities[context.model.get_kind()].key
    cursor = Cursor(urlsafe=context.input.get('actions_cursor'))
    if self.read_all:
      __actions = []
      more = True
      offset = 0
      limit = 1000
      while more:
        entities = Action.query(ancestor=ancestor).fetch(limit=limit, offset=offset)
        if len(entities):
          __actions.extend(entities)
          offset = offset + limit
        else:
          more = False
    else:
      __actions, cursor, more = Action.query(ancestor=ancestor).fetch_page(self.page_size, start_cursor=cursor)
    if cursor:
      cursor = cursor.urlsafe()
      context.tmp['actions_cursor'] = cursor
    if __actions:
      context.entities[context.model.get_kind()].__actions = __actions
    else:
      context.entities[context.model.get_kind()].__actions = []
    context.tmp['actions_more'] = more


class EntryActionArguments(ndb.BaseModel):
  
  def run(self, context):
    context.tmp['available_arguments'] = __JOURNAL_FIELDS.keys()  # @todo Perhaps have another dict for action arguments?


class EntryActionRead(ndb.BaseModel):
  
  def run(self, context):
    context.entities['100']._code = context.entities['100'].key_id_str[4:]  # @todo Slice depends on the actual kind length (currently kind is 3 characters long)!


class EntryActionUpdateRead(ndb.BaseModel):
  
  def run(self, context):
    '''key.id() = prefix_<user supplied value>
    key.id() defines constraint of unique action code (<user supplied value> part of the key.id) per journal.
    It also ensures that code can not be changed for action once it has been defined! Max code length is entirely
    up to us!
    
    '''
    code = '100_%s' % context.input.get('_code')  # @todo Not sure if we need to salt key id here?
    entity_key = ndb.Key('100', code, parent=context.input.get('parent'))
    entity = entity_key.get()
    if entity is None:
      entity = context.model(key=entity_key)
    context.entities['100'] = entity


class EntryActionSet(ndb.BaseModel):
  
  def run(self, context):
    
    def build_field(model, field):
      return model(name=field.get('name'),
                   verbose_name=field.get('verbose_name'),
                   required=field.get('required'),
                   repeated=field.get('repeated'),
                   indexed=field.get('indexed'),
                   default=field.get('default'),
                   choices=field.get('choices'))
    
    input_arguments = context.input.get('arguments')
    arguments = []
    for field in input_arguments:
      model = __JOURNAL_FIELDS.get(field.get('type'))
      arguments.append(build_field(model, field))
    context.entities['100'].name = context.input.get('name')
    context.entities['100'].arguments = arguments
    context.entities['100'].active = context.input.get('active')


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


class CategoryRead(ndb.BaseModel):
  
  def run(self, context):
    context.entities[context.model.get_kind()]._code = context.entities[context.model.get_kind()].key_id_str[3:]


class CategorySet(ndb.BaseModel):
  
  def run(self, context):
    context.entities[context.model.get_kind()].parent_record = context.input.get('parent_record')
    context.entities[context.model.get_kind()].name = context.input.get('name')
    context.entities[context.model.get_kind()].active = context.input.get('active')
    context.entities[context.model.get_kind()].description = context.input.get('description')
    complete_name = ndb.make_complete_name(context.entities[context.model.get_kind()], 'name', parent_property='parent_record')
    context.entities[context.model.get_kind()].complete_name = complete_name


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