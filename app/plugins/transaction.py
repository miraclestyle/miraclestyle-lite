# -*- coding: utf-8 -*-
'''
Created on Jun 2, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import collections

from app import orm
from app.util import *


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
class CategoryUpdateSet(orm.BaseModel):
  
  def run(self, context):
    context._category.parent_record = context.input.get('parent_record')
    context._category.name = context.input.get('name')
    context._category.active = context.input.get('active')
    context._category.description = context.input.get('description')
    # @todo make complete name could be replaced by custom property
    complete_name = orm.make_complete_name(context.entities[context.model.get_kind()], 'name', parent_property='parent_record')
    context._category.complete_name = complete_name
