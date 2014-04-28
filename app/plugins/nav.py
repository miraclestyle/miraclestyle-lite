# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv import event
from app.srv import rule


class Set(event.Plugin):
  
  def run(self, context):
    role_key = context.input.get('role')
    role = role_key.get()
    if role.key_namespace != context.entities['62'].key_namespace:  # Both, the role and the entity namespace must match. Perhaps, this could be done with rule engine?
      raise rule.ActionDenied(context)
    filters = []
    input_filters = context.input.get('filters')
    for input_filter in input_filters:
      filters.append(Filter(**input_filter))
    context.values['62'].name = context.input.get('name')
    context.values['62'].sequence = context.input.get('sequence')
    context.values['62'].active = context.input.get('active')
    context.values['62'].role = role_key
    context.values['62'].search_form = context.input.get('search_form')
    context.values['62'].filters = filters


class BuildMenu(event.Plugin):
  
  def run(self, context):
    model = context.model
    domain_user_key = ndb.Key('8', context.user.key_id_str, namespace=context.domain.key.urlsafe())
    domain_user = domain_user_key.get()
    if domain_user:
      widgets = model.query(model.active == True,
                            model.role.IN(domain_user.roles),
                            namespace=context.domain.key_namespace).order(model.sequence).fetch()
      context.widgets = widgets


class SelectRoles(event.Plugin):
  
  def run(self, context):
    context.output['roles'] = rule.DomainRole.query(rule.DomainRole.active == True, namespace=context.entities['62'].key_namespace).fetch()