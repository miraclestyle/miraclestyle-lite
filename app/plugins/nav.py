# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, memcache, util
from app.lib.attribute_manipulator import set_attr, get_attr


class Set(ndb.BaseModel):
  
  def run(self, context):
    Filter = context.models['65']
    filters = []
    input_filters = context.input.get('filters')
    for input_filter in input_filters:
      filters.append(Filter(**input_filter))
    context.values['62'].name = context.input.get('name')
    context.values['62'].sequence = context.input.get('sequence')
    context.values['62'].active = context.input.get('active')
    context.values['62'].role = context.input.get('role')
    context.values['62'].search_form = context.input.get('search_form')
    context.values['62'].filters = filters


class BuildMenu(ndb.BaseModel):
  
  def run(self, context):
    model = context.model
    domain_user_key = ndb.Key('8', context.user.key_id_str, namespace=context.namespace)
    domain_user = domain_user_key.get()
    if domain_user:
      widgets = model.query(model.active == True,
                            model.role.IN(domain_user.roles),
                            namespace=context.namespace).order(model.sequence).fetch()
      context.tmp['widgets'] = widgets
