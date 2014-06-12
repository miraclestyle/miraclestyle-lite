# -*- coding: utf-8 -*-
'''
Created on Jun 2, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv.event import Action, PluginGroup
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.srv import log as ndb_log
from app.srv import uom as ndb_uom
from app.plugins import common, rule, log, callback, notify



class EntryAction(Action):
  
  _kind = 100
  
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('49', repeated=True),
    '_code': ndb.SuperStringProperty()
    }
  

# @todo sequencing counter is missing, and has to be determined how to solve that!
class Journal(ndb.BaseExpando):
  
  _kind = 49
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = ndb.SuperStringProperty('3', required=True)
  state = ndb.SuperStringProperty('4', required=True, default='draft', choices=['draft', 'active', 'decommissioned'])
  entry_fields = ndb.SuperPickleProperty('5', required=True, indexed=False, compressed=False)
  line_fields = ndb.SuperPickleProperty('6', required=True, indexed=False, compressed=False)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('49', repeated=True),
    '_code': ndb.SuperStringProperty(),
    '__actions': ndb.SuperPickleProperty(default={}, compressed=False)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('49', [Action.build_key('49', 'prepare'),
                              Action.build_key('49', 'read'),
                              Action.build_key('49', 'update'),
                              Action.build_key('49', 'delete'),
                              Action.build_key('49', 'search'),
                              Action.build_key('49', 'read_records'),
                              Action.build_key('49', 'activate'),
                              Action.build_key('49', 'decommission')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('49', [Action.build_key('49', 'update'),
                              Action.build_key('49', 'delete')], False, 'context.entity._is_system or context.entity.state != "draft"'),
      ActionPermission('49', [Action.build_key('49', 'activate')], False, 'context.entity.state == "active"'),
      ActionPermission('49', [Action.build_key('49', 'decommission')], False, 'context.entity._is_system or context.entity.state == "decommissioned"'),
      FieldPermission('49', ['created', 'updated', 'state'], False, None, 'True'),
      FieldPermission('49', ['created', 'updated', 'name', 'state', 'entry_fields', 'line_fields', '_records', '_code'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('49', ['created', 'updated', 'name', 'state', 'entry_fields', 'line_fields', '_records', '_code'], False, None,
                      'context.entity._is_system'),
      FieldPermission('49', ['state'], True, None,
                      '(context.action.key_id_str == "activate" and context.value and context.value.state == "active") or (context.action.key_id_str == "decommission" and context.value and context.value.state == "decommissioned")')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('49', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(),
            transaction.JournalFields(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            common.Set(dynamic_values={'output.entity': 'entities.49',
                                       'output.available_fields': 'tmp.available_fields'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            transaction.JournalFields(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            transaction.JournalRead(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.49',
                                       'output.available_fields': 'tmp.available_fields'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'update'),
      arguments={
        #'key': ndb.SuperKeyProperty(kind='49', required=True),
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        '_code': ndb.SuperStringProperty(required=True, max_size=64),  # Regarding max_size, take a look at the transaction.JournalUpdateRead() plugin!
        'name': ndb.SuperStringProperty(required=True),
        'entry_fields': ndb.SuperJsonProperty(required=True),
        'line_fields': ndb.SuperJsonProperty(required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            transaction.JournalUpdateRead(),
            transaction.JournalSet(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            transaction.JournalRead()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            log.Entity(),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.49'}),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            common.Delete(),
            log.Entity(),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.49'}),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()}
            },
          indexes=[
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']],
                          ['state', ['asc', 'desc']]]},
            {'filter': ['state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['state', ['asc', 'desc']]]},
            {'filter': ['name', 'state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['state', ['asc', 'desc']]]},
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']],
                          ['state', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']},
            'state': {'operators': ['asc', 'desc']}
            }
          ),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
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
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            log.Read(page_size=settings.RECORDS_PAGE),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.49',
                                       'output.log_read_cursor': 'log_read_cursor',
                                       'output.log_read_more': 'log_read_more'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'read_actions'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True),
        'actions_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            transaction.JournalReadActions(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.49',
                                       'output.actions_cursor': 'tmp.actions_cursor',
                                       'output.actions_more': 'tmp.actions_more'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'activate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True),
        'message': ndb.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            common.Set(static_values={'values.49.state': 'active'}),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            rule.Prepare(skip_user_roles=False, strict=False),  # @todo Should run out of transaction!!!
            log.Entity(dynamic_arguments={'message': 'input.message'}),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.49'}),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'decommission'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True),
        'message': ndb.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            common.Set(static_values={'values.49.state': 'decommissioned'}),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            rule.Prepare(skip_user_roles=False, strict=False),  # @todo Should run out of transaction!!!
            log.Entity(dynamic_arguments={'message': 'input.message'}),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.49'}),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    
    
    Action(
      key=Action.build_key('49', 'action_prepare'),
      arguments={
        'parent': ndb.SuperKeyProperty(kind='49', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(),  # @todo Not sure if Read plugin (to load parent journal) is needed here?
            common.Prepare(kind_id='100', parent_path='input.parent'),
            transaction.EntryActionArguments(),
            rule.Prepare(prepare_entities=['49', '100'], skip_user_roles=False, strict=False),
            rule.Exec(),
            common.Set(dynamic_values={'output.entity': 'entities.100',
                                       'output.available_arguments': 'tmp.available_arguments'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'action_read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='100', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(read_entities={'100': 'input.key'}),
            common.Read(read_entities={'49': 'entities.56.key_parent'}),
            transaction.EntryActionArguments(),
            rule.Prepare(prepare_entities=['49', '100'], skip_user_roles=False, strict=False),
            rule.Exec(),
            transaction.EntryActionRead(),
            rule.Read(read_entities=['100']),
            common.Set(dynamic_values={'output.entity': 'entities.100',
                                       'output.available_arguments': 'tmp.available_arguments'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'update'),
      arguments={
        #'key': ndb.SuperKeyProperty(kind='49', required=True),
        'parent': ndb.SuperKeyProperty(kind='49', required=True),
        '_code': ndb.SuperStringProperty(required=True, max_size=64),  # Regarding max_size, take a look at the transaction.JournalUpdateRead() plugin!
        'name': ndb.SuperStringProperty(required=True),
        'arguments': ndb.SuperJsonProperty(required=True),
        'active': ndb.SuperBooleanProperty(required=True, default=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(),  # @todo Not sure if Read plugin (to load parent journal) is needed here?
            transaction.EntryActionUpdateRead(),
            transaction.EntryActionSet(),
            rule.Prepare(prepare_entities=['49', '100'], skip_user_roles=False, strict=False),
            rule.Exec(),
            transaction.EntryActionRead()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(write_entities=['100']),
            common.Write(write_entities=['100']),
            log.Entity(log_entities=['100']),
            log.Write(),
            rule.Read(read_entities=['100']),
            common.Set(dynamic_values={'output.entity': 'entities.100'}),
            callback.Notify(dynamic_data={'caller_entity': 'entities.100.key_urlsafe'}),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('49', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='100', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(),  # @todo Not sure if Read plugin (to load parent journal) is needed here?
            common.Read(read_entities={'100': 'input.key'}),
            rule.Prepare(prepare_entities=['49', '100'], skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            common.Delete(delete_entities=['100']),
            log.Entity(log_entities=['100']),
            log.Write(),
            rule.Read(read_entities=['100']),
            common.Set(dynamic_values={'output.entity': 'entities.100'}),
            callback.Notify(dynamic_data={'caller_entity': 'entities.100.key_urlsafe'}),
            callback.Exec()
            ]
          )
        ]
      )
    ]
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')


class CategoryBalance(ndb.BaseModel):
  
  _kind = 71
  
  from_date = ndb.SuperDateTimeProperty('1', required=True, indexed=False)
  to_date = ndb.SuperDateTimeProperty('2', required=True, indexed=False)
  debit = ndb.SuperDecimalProperty('3', required=True, indexed=False)
  credit = ndb.SuperDecimalProperty('4', required=True, indexed=False)
  balance = ndb.SuperDecimalProperty('5', required=True, indexed=False)
  uom = ndb.SuperLocalStructuredProperty(ndb_uom.UOM, '6', required=True, indexed=False)


class Category(ndb.BaseExpando):
  
  _kind = 47
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  parent_record = ndb.SuperKeyProperty('3', kind='47')
  name = ndb.SuperStringProperty('4', required=True)
  complete_name = ndb.SuperTextProperty('5', required=True)
  active = ndb.SuperBooleanProperty('6', required=True, default=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'description': ndb.SuperTextProperty('7'),
    'balances': ndb.SuperLocalStructuredProperty(CategoryBalance, '8', repeated=True)
    }
  
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('47', repeated=True),
    '_code': ndb.SuperStringProperty()
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('47', [Action.build_key('47', 'prepare'),
                              Action.build_key('47', 'read'),
                              Action.build_key('47', 'update'),
                              Action.build_key('47', 'delete'),
                              Action.build_key('47', 'search'),
                              Action.build_key('47', 'read_records')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('47', [Action.build_key('47', 'update'),
                              Action.build_key('47', 'delete')], False, 'context.entity._is_system'),
      ActionPermission('47', [Action.build_key('47', 'delete')], False, 'context.entity._is_used'),
      FieldPermission('47', ['created', 'updated'], False, None, 'True'),
      FieldPermission('47', ['created', 'updated', 'parent_record', 'name', 'complete_name', 'active', 'description', 'balances', '_records', '_code'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('47', ['created', 'updated', 'parent_record', 'name', 'complete_name', 'active', 'description', 'balances', '_records', '_code'], False, None,
                      'context.entity._is_system')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('47', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            common.Set(dynamic_values={'output.entity': 'entities.47'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('47', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='47', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            transaction.CategoryRead(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.47'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('47', 'update'),
      arguments={
        #'key': ndb.SuperKeyProperty(kind='47', required=True),
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        '_code': ndb.SuperStringProperty(required=True, max_size=64),  # Regarding max_size, take a look at the transaction.CategoryUpdateRead() plugin!
        'parent_record': ndb.SuperKeyProperty(kind='47'),
        'name': ndb.SuperStringProperty(required=True),
        'active': ndb.SuperBooleanProperty(required=True, default=True),
        'description': ndb.SuperTextProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            transaction.CategoryUpdateRead(),
            transaction.CategorySet(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            transaction.CategoryRead()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            log.Entity(),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.47'}),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('47', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='47', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            common.Delete(),
            log.Entity(),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.47'}),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('47', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty(choices=[True])}
            },
          indexes=[
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']],
                          ['active', ['asc', 'desc']]]},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['active', ['asc', 'desc']]]},
            {'filter': ['name', 'active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['active', ['asc', 'desc']]]},
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']],
                          ['active', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']},
            'active': {'operators': ['asc', 'desc']}
            }
          ),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
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
          )
        ]
      ),
    Action(
      key=Action.build_key('47', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='47', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            log.Read(page_size=settings.RECORDS_PAGE),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.47',
                                       'output.log_read_cursor': 'log_read_cursor',
                                       'output.log_read_more': 'log_read_more'})
            ]
          )
        ]
      )
    ]
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')
  
  @property
  def _is_used(self):
    line = Line.query(Line.categories == self.key).get()
    return line != None


class Group(ndb.BaseExpando):
  
  _kind = 48
  
  _default_indexed = False


class Entry(ndb.BaseExpando):
  
  _kind = 50
  
  # ancestor Group (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L1279
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l38
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  journal = ndb.SuperKeyProperty('3', kind=Journal, required=True)
  name = ndb.SuperStringProperty('4', required=True)
  state = ndb.SuperStringProperty('5', required=True)
  date = ndb.SuperDateTimeProperty('6', required=True)
  
  _virtual_fields = {
    '_lines': ndb.SuperLocalStructuredProperty(Line, repeated=True)
    }
  
  def get_kind(self):
    return 'e_%s' % self.journal.id()
  
  def get_actions(self):
    journal_actions = Action.query(Action.active == True,
                                   ancestor=self.journal).fetch()
    actions = {}
    for action in journal_actions:
      actions[action.key.urlsafe()] = action
    return actions
  
  def get_fields(self):
    fields = super(Entry, self).get_fields()
    journal = self.journal.get()
    line_fields = {}
    expando_entry_fields = {}
    expando_line_fields = {}
    for prop_key, prop in Line._properties.items():
      line_fields[prop._code_name] = prop
    if hasattr(Line, 'get_expando_fields'):
      expando_fields = Line.get_expando_fields()
      if expando_fields:
        for expando_prop_key, expando_prop in expando_fields.items():
          line_fields[expando_prop._code_name] = expando_prop
    for entry_field_key, entry_field in journal.entry_fields.items():
      expando_entry_fields['e_%s' % entry_field_key] = entry_field
    for line_field_key, line_field in journal.line_fields.items():
      expando_line_fields['l_%s' % line_field_key] = line_field
    fields.update(line_fields)
    fields.update(expando_entry_fields)
    fields.update(expando_line_fields)
    return fields
  
  @property
  def _actions(self):
    journal_actions = Action.query(Action.active == True,
                                   ancestor=self.journal).fetch()
    actions = {}
    for action in journal_actions:
      actions[action.key.urlsafe()] = action
    return actions


class Line(ndb.BaseExpando):
  
  _kind = 51
  
  # ancestor Entry (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_move_line.py#L432
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_analytic_line.py#L29
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l486
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/line.py#l14
  # uvek se prvo sekvencionisu linije koje imaju debit>0 a onda iza njih slede linije koje imaju credit>0
  # u slucaju da je Entry balanced=True, zbir svih debit vrednosti u linijama mora biti jednak zbiru credit vrednosti
  journal = ndb.SuperKeyProperty('1', kind=Journal, required=True)  # delete
  company = ndb.SuperKeyProperty('2', kind='44', required=True)  # delete
  state = ndb.SuperIntegerProperty('3', required=True)  # delete
  date = ndb.SuperDateTimeProperty('4', required=True)  # delete
  sequence = ndb.SuperIntegerProperty('5', required=True)  # @todo Can we sequence Line.id()?
  categories = ndb.SuperKeyProperty('6', kind=Category, repeated=True)
  debit = ndb.SuperDecimalProperty('7', required=True, indexed=False)  # debit=0 u slucaju da je credit>0, negativne vrednosti su zabranjene
  credit = ndb.SuperDecimalProperty('8', required=True, indexed=False)  # credit=0 u slucaju da je debit>0, negativne vrednosti su zabranjene
  uom = ndb.SuperLocalStructuredProperty(uom.UOM, '9', required=True)
  # Expando
  # neki upiti na Line zahtevaju "join" sa Entry poljima
  # taj problem se mozda moze resiti map-reduce tehnikom ili kopiranjem polja iz Entry-ja u Line-ove
  
  def get_kind(self):  # @todo Do we need this?
    return 'l_%s' % self.parent_entity.journal.id()
  
  def get_actions(self):  # @todo Do we need this?
    journal_actions = Action.query(Action.active == True,
                                   ancestor=self.parent_entity.journal).fetch()
    actions = {}
    for action in journal_actions:
      actions[action.key.urlsafe()] = action
    return actions
  
  def get_fields(self):  # @todo Do we need this?
    fields = super(Line, self).get_fields()
    journal = self.parent_entity.journal.get()
    expando_line_fields = {}
    for line_field_key, line_field in journal.line_fields.items():
      expando_line_fields['l_%s' % line_field_key] = line_field
    fields.update(expando_line_fields)
    return fields
