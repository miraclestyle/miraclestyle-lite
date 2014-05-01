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
                       "not context.entities['62'].namespace_entity.state == 'active'"),
      ActionPermission('62', Action.build_key('62', 'create').urlsafe(), False,
                       "not context.entities['62'].namespace_entity.state == 'active' or context.entities['62']._is_system"),
      ActionPermission('62', Action.build_key('62', 'read').urlsafe(), False,
                       "not context.entities['62'].namespace_entity.state == 'active'"),
      ActionPermission('62', Action.build_key('62', 'update').urlsafe(), False,
                       "not context.entities['62'].namespace_entity.state == 'active' or context.entities['62']._is_system"),
      ActionPermission('62', Action.build_key('62', 'delete').urlsafe(), False,
                       "not context.entities['62'].namespace_entity.state == 'active' or context.entities['62']._is_system"),
      ActionPermission('62', Action.build_key('62', 'search').urlsafe(), False,
                       "not context.entities['62'].namespace_entity.state == 'active'"),
      ActionPermission('62', Action.build_key('62', 'read_records').urlsafe(), False,
                       "not context.entities['62'].namespace_entity.state == 'active'"),
      ActionPermission('62', Action.build_key('62', 'build_menu').urlsafe(), False,
                       "not context.entities['62'].namespace_entity.state == 'active'"),
      FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], False, None,
                      "not context.entities['62'].namespace_entity.state == 'active' or context.entities['62']._is_system"),
      FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], None, False,
                      "not context.entities['62'].namespace_entity.state == 'active'")
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('62', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
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
        }
      ),
    Action(
      key=Action.build_key('62', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True)
        }
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
        }
      ),
    Action(
      key=Action.build_key('62', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True)
        }
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
        }
      ),
    Action(
      key=Action.build_key('62', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    Action(
      key=Action.build_key('62', 'build_menu'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      )
    ]
  
  _plugins = [
    common.Context(
      subscriptions=[
        Action.build_key('62', 'prepare'),
        Action.build_key('62', 'create'),
        Action.build_key('62', 'read'),
        Action.build_key('62', 'update'),
        Action.build_key('62', 'delete'),
        Action.build_key('62', 'search'),
        Action.build_key('62', 'read_records'),
        Action.build_key('62', 'build_menu')
        ]
      ),
    common.Prepare(
      subscriptions=[
        Action.build_key('62', 'prepare'),
        Action.build_key('62', 'create'),
        Action.build_key('62', 'search'),
        Action.build_key('62', 'build_menu')
        ],
      domain_model=True
      ),
    common.Read(
      subscriptions=[
        Action.build_key('62', 'read'),
        Action.build_key('62', 'update'),
        Action.build_key('62', 'delete'),
        Action.build_key('62', 'read_records')
        ]
      ),
    rule.Prepare(
      subscriptions=[
        Action.build_key('62', 'prepare'),
        Action.build_key('62', 'create'),
        Action.build_key('62', 'read'),
        Action.build_key('62', 'update'),
        Action.build_key('62', 'delete'),
        Action.build_key('62', 'search'),
        Action.build_key('62', 'read_records'),
        Action.build_key('62', 'build_menu')
        ],
      skip_user_roles=False,
      strict=False
      ),
    rule.Exec(
      subscriptions=[
        Action.build_key('62', 'prepare'),
        Action.build_key('62', 'create'),
        Action.build_key('62', 'read'),
        Action.build_key('62', 'update'),
        Action.build_key('62', 'delete'),
        Action.build_key('62', 'search'),
        Action.build_key('62', 'read_records'),
        Action.build_key('62', 'build_menu')
        ]
      ),
    nav.Set(
      subscriptions=[
        Action.build_key('62', 'create'),
        Action.build_key('62', 'update')
        ]
      ),
    nav.BuildMenu(
      subscriptions=[
        Action.build_key('62', 'build_menu')
        ]
      ),
    rule.Write(
      subscriptions=[
        Action.build_key('62', 'create'),
        Action.build_key('62', 'update')
        ],
      transactional=True
      ),
    common.Write(
      subscriptions=[
        Action.build_key('62', 'create'),
        Action.build_key('62', 'update')
        ],
      transactional=True
      ),
    common.Delete(
      subscriptions=[
        Action.build_key('62', 'delete')
        ],
      transactional=True
      ),
    log.Entity(
      subscriptions=[
        Action.build_key('62', 'create'),
        Action.build_key('62', 'update'),
        Action.build_key('62', 'delete')
        ],
      transactional=True
      ),
    log.Write(
      subscriptions=[
        Action.build_key('62', 'create'),
        Action.build_key('62', 'update'),
        Action.build_key('62', 'delete')
        ],
      transactional=True
      ),
    rule.Read(
      subscriptions=[
        Action.build_key('62', 'create'),
        Action.build_key('62', 'update'),
        Action.build_key('62', 'delete')
        ],
      transactional=True
      ),
    common.Set(
      subscriptions=[
        Action.build_key('62', 'create'),
        Action.build_key('62', 'update'),
        Action.build_key('62', 'delete')
        ],
      transactional=True,
      dynamic_values={'output.entity': 'entities.62'}
      ),
    callback.Payload(
      subscriptions=[
        Action.build_key('62', 'create'),
        Action.build_key('62', 'update'),
        Action.build_key('62', 'delete')
        ],
      transactional=True,
      queue = 'notify',
      static_data = {'action_key': 'initiate', 'action_model': '61'},
      dynamic_data = {'caller_entity': 'entities.62.key_urlsafe'}
      ),
    callback.Exec(
      subscriptions=[
        Action.build_key('62', 'create'),
        Action.build_key('62', 'update'),
        Action.build_key('62', 'delete')
        ],
      transactional=True,
      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'}
      ),
    log.Read(
      subscriptions=[
        Action.build_key('62', 'read_records')
        ]
      ),
    common.Search(
      subscriptions=[
        Action.build_key('62', 'search')
        ]
      ),
    rule.Prepare(
      subscriptions=[
        Action.build_key('62', 'search')
        ],
      skip_user_roles=False,
      strict=False
      ),
    rule.Read(
      subscriptions=[
        Action.build_key('62', 'read'),
        Action.build_key('62', 'search'),
        Action.build_key('62', 'read_records')
        ]
      ),
    common.Set(
      subscriptions=[
        Action.build_key('62', 'prepare'),
        Action.build_key('62', 'read')
        ],
      dynamic_values={'output.entity': 'entities.62'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('62', 'search')
        ],
      dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'next_cursor', 'output.more': 'more'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('62', 'read_records')
        ],
      dynamic_values={'output.entity': 'entities.62', 'output.next_cursor': 'next_cursor', 'output.more': 'more'}
      ),
    common.Set(
      subscriptions=[
        Action.build_key('62', 'build_menu')
        ],
      dynamic_values={'output.menu': 'widgets', 'output.domain': 'domain'}
      ),
    nav.SelectRoles(
      subscriptions=[
        Action.build_key('62', 'prepare'),
        Action.build_key('62', 'read')
        ]
      )
    ]
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')
