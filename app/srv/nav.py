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


class Filter(ndb.BaseModel):
  
  _kind = 65
  
  name = ndb.SuperStringProperty('1', required=True, indexed=False)
  kind = ndb.SuperStringProperty('2', required=True, indexed=False)
  query = ndb.SuperJsonProperty('3', required=True, indexed=False, default={})


class Widget(ndb.BaseExpando):
  
  _kind = 62
  
  name = ndb.SuperStringProperty('1', required=True)
  sequence = ndb.SuperIntegerProperty('2', required=True)
  active = ndb.SuperBooleanProperty('3', required=True, default=True)
  role = ndb.SuperKeyProperty('4', kind='60', required=True)
  search_form = ndb.SuperBooleanProperty('5', required=True, indexed=False, default=True)
  filters = ndb.SuperLocalStructuredProperty(Filter, '6', repeated=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('62', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('62', [Action.build_key('62', 'prepare'),
                              Action.build_key('62', 'create'),
                              Action.build_key('62', 'read'),
                              Action.build_key('62', 'update'),
                              Action.build_key('62', 'delete'),
                              Action.build_key('62', 'search'),
                              Action.build_key('62', 'read_records'),
                              Action.build_key('62', 'build_menu')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('62', [Action.build_key('62', 'create'),
                              Action.build_key('62', 'update'),
                              Action.build_key('62', 'delete')], False, 'context.entity._is_system'),
      FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], False, None,
                      'context.entity.namespace_entity.state != "active" or context.entity._is_system'),
      FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], None, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('62', ['role'], False, None,
                      '(context.action.key_id_str == "create" or context.action.key_id_str == "update") and (context.value and context.value.role and context.entity.key_namespace != context.value.role.entity.key_namespace)')
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
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'output.entity': 'entities.62'})
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
        common.Prepare(),
        nav.Set(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.62'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.62.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
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
        common.Set(dynamic_values={'output.entity': 'entities.62'})
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
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.62.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
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
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.62.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('62', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'sequence', 'operator': 'asc'}},
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
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(page_size=settings.SEARCH_PAGE),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities',
                                   'output.search_cursor': 'search_cursor',
                                   'output.search_more': 'search_more'})
        ]
      ),
    Action(
      key=Action.build_key('62', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(page_size=settings.RECORDS_PAGE),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.62',
                                   'output.log_read_cursor': 'log_read_cursor',
                                   'output.log_read_more': 'log_read_more'})
        ]
      ),
    Action(
      key=Action.build_key('62', 'build_menu'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        nav.BuildMenu(),
        common.Set(dynamic_values={'output.menu': 'tmp.widgets', 'output.domain': 'domain'})
        ]
      )
    ]
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')
