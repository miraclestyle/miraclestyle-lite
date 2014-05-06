# -*- coding: utf-8 -*-
'''
Created on Feb 24, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv.event import Action
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.srv import log as ndb_log
from app.plugins import common, rule, log, callback, nav


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
    '_records': ndb_log.SuperLocalStructuredRecordProperty('62', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('62', Action.build_key('62', 'prepare').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('62', Action.build_key('62', 'create').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active' or context.entity._is_system"),
      ActionPermission('62', Action.build_key('62', 'read').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('62', Action.build_key('62', 'update').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active' or context.entity._is_system"),
      ActionPermission('62', Action.build_key('62', 'delete').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active' or context.entity._is_system"),
      ActionPermission('62', Action.build_key('62', 'search').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('62', Action.build_key('62', 'read_records').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      ActionPermission('62', Action.build_key('62', 'build_menu').urlsafe(), False,
                       "context.entity.namespace_entity.state != 'active'"),
      FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], False, None,
                      "context.entity.namespace_entity.state != 'active' or context.entity._is_system"),
      FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], None, False,
                      "context.entity.namespace_entity.state != 'active'"),
      FieldPermission('62', ['role'], False, None,
                      "(context.action.key_id_str == 'create' or context.action.key_id_str == 'update') and (context.value and context.value.role and context.entity.key_namespace != context.value.role.entity.key_namespace)")
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('62', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'output.entity': 'entities.62'}),
        nav.SelectRoles()
        ]
      ),
    Action(
      key=Action.build_key('62', 'create'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'sequence': ndb.SuperIntegerProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True),
        'role': ndb.SuperKeyProperty(kind='60', required=True),
        'search_form': ndb.SuperBooleanProperty(default=True),
        'filters': ndb.SuperJsonProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        nav.Set(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.62'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.62.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('62', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.62'}),
        nav.SelectRoles()
        ]
      ),
    Action(
      key=Action.build_key('62', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'sequence': ndb.SuperIntegerProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True),
        'role': ndb.SuperKeyProperty(kind='60', required=True),
        'search_form': ndb.SuperBooleanProperty(default=True),
        'filters': ndb.SuperJsonProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        nav.Set(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.62'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.62.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('62', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Delete(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.62'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.62.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('62', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "sequence", "operator": "asc"}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'role': {'operators': ['==', '!='], 'type': ndb.SuperKeyProperty(kind='60')},
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
            'sequence': {'operators': ['asc', 'desc']}
            }
          ),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('62', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.62', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('62', 'build_menu'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        nav.BuildMenu(),
        common.Set(dynamic_values={'output.menu': 'widgets', 'output.domain': 'domain'})
        ]
      )
    ]
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')

 