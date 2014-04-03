# -*- coding: utf-8 -*-
'''
Created on Feb 24, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from app import ndb
from app.srv import rule, event, log, cruds


class Filter(ndb.BaseExpando):
  
  _kind = 65
  
  name = ndb.SuperStringProperty('1', required=True)
  kind = ndb.SuperStringProperty('2', required=True)
  query = ndb.SuperJsonProperty('3', required=True, default={})


class Widget(ndb.BaseExpando):
  
  _kind = 62
  
  name = ndb.SuperStringProperty('1', required=True)
  sequence = ndb.SuperIntegerProperty('2', required=True)
  active = ndb.SuperBooleanProperty('3', required=True, default=True)
  role = ndb.SuperKeyProperty('4', kind='60', required=True)
  search_form = ndb.SuperBooleanProperty('5', required=True, default=True)
  filters = ndb.SuperLocalStructuredProperty(Filter, '6', repeated=True)
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('62', repeated=True)
    }
  
  _global_role = rule.GlobalRole(
    permissions=[
      rule.ActionPermission('62', event.Action.build_key('62-0').urlsafe(), True, "not context.auth.user._is_guest"),
      rule.ActionPermission('62', event.Action.build_key('62-5').urlsafe(), False, "context.rule.entity._is_admin"),
      rule.ActionPermission('62', event.Action.build_key('62-5').urlsafe(), True, "not context.rule.entity._is_admin"),
      rule.ActionPermission('62', event.Action.build_key('62-7').urlsafe(), True, "context.auth.user._root_admin"),
      rule.FieldPermission('62', '_records.note', False, False, 'not context.auth.user._root_admin'),
      rule.FieldPermission('62', '_records.note', True, True, 'context.auth.user._root_admin')
      ]
    )
  
  _actions = {
    'build_menu': event.Action(
      id='62-0',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
    'search': event.Action(
      id='62-1',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "sequence", "operator": "asc"}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'role' : {'operators' : ['==', '!='], 'type' : ndb.SuperKeyProperty(kind='60'),},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty()}
          },
          indexes=[
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['role'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
                    
            {'filter': ['name', 'active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['role', 'active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},    
                      
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']},
            'sequence' : {'operators': ['asc', 'desc']},
            }
          ),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    'create': event.Action(
      id='62-2',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'sequence': ndb.SuperIntegerProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True),
        'role': ndb.SuperKeyProperty(kind='60', required=True),
        'search_form': ndb.SuperBooleanProperty(default=True),
        'filters': ndb.SuperJsonProperty()
        }
      ),
    'read': event.Action(id='62-3', arguments={'key': ndb.SuperKeyProperty(kind='62', required=True)}),
    'update': event.Action(
      id='62-4',
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'sequence': ndb.SuperIntegerProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True),
        'role': ndb.SuperKeyProperty(kind='60', required=True),
        'search_form': ndb.SuperBooleanProperty(default=True),
        'filters': ndb.SuperJsonProperty()
        }
      ),
    'delete': event.Action(id='62-5', arguments={'key': ndb.SuperKeyProperty(kind='62', required=True)}),
    'prepare': event.Action(
      id='62-6',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
    'read_records': event.Action(
      id='62-7',
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    }
  
  @property
  def _is_admin(self):
    return self.key_id_str.startswith('admin_')
  
  @classmethod
  def complete_save(cls, entity, context):
    role_key = context.input.get('role')
    role = role_key.get()
    if role.key_namespace != entity.key_namespace:  # Both, the role and the entity namespace must match. Perhaps, this could be done with rule engine?
      raise rule.ActionDenied(context)
    filters = []
    input_filters = context.input.get('filters')
    for input_filter in input_filters:
      filters.append(Filter(**input_filter))
    return {'name': context.input.get('name'),
            'sequence': context.input.get('sequence'),
            'active': context.input.get('active'),
            'role': role_key,
            'search_form': context.input.get('search_form'),
            'filters': filters}
  
  @classmethod
  def create(cls, context):
    domain_key = context.input.get('domain')
    entity = cls(namespace=domain_key.urlsafe())
    values = cls.complete_save(entity, context)
    context.cruds.domain_key = domain_key
    context.cruds.model = cls
    context.cruds.values = values
    cruds.Engine.create(context)
  
  @classmethod
  def update(cls, context):
    entity_key = context.input.get('entity_key')
    entity = entity_key.get()
    values = cls.complete_save(entity, context)
    context.cruds.model = cls
    context.cruds.values = values
    cruds.Engine.update(context)
  
  @classmethod
  def prepare(cls, context):
    domain_key = context.input.get('domain')
    context.cruds.domain_key = domain_key
    context.cruds.model = cls
    cruds.Engine.prepare(context)
    entity = context.output['entity']
    context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
  
  @classmethod
  def read(cls, context):
    context.cruds.model = cls
    cruds.Engine.read(context)
    entity = context.output['entity']
    context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
  
  @classmethod
  def delete(cls, context):
    context.cruds.model = cls
    cruds.Engine.delete(context)
  
  @classmethod
  def search(cls, context):
    context.cruds.model = cls
    context.cruds.domain_key = context.input.get('domain')
    cruds.Engine.search(context)
  
  @classmethod
  def read_records(cls, context):
    context.cruds.model = cls
    cruds.Engine.read_records(context)
  
  @classmethod
  def build_menu(cls, context):
    domain_key = context.input.get('domain')
    domain = domain_key.get()
    context.rule.entity = cls(namespace=domain.key_namespace)
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    domain_user_key = rule.DomainUser.build_key(context.auth.user.key_id_str, namespace=domain.key.urlsafe())
    domain_user = domain_user_key.get()
    if domain_user:
      widgets = cls.query(cls.active == True,
                          cls.role.IN(domain_user.roles),
                          namespace=domain.key_namespace).order(cls.sequence).fetch()
      context.output['menu'] = widgets
      context.output['domain'] = domain
    return context
  
  @classmethod
  def selection_roles_helper(cls, namespace):  # @todo Perhaps kill this method in favor of DomainRole.search()!?
    return rule.DomainRole.query(rule.DomainRole.active == True, namespace=namespace).fetch()
