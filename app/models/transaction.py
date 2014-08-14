# -*- coding: utf-8 -*-
'''
Created on Jun 2, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models import uom
from app.models.base import *
from app.plugins.base import *
from app.plugins.transaction import *


__name_definition = orm.SuperStringProperty(max_size=20)
__kind_definition = orm.SuperStringProperty(max_size=10)  # We can determine also choices to be orm.Model._kind_map.keys() however not so sure about journal and entry ids.

__default_journal_field_keywords_definition = {'repeated': {'True': ('True', True), 'False': ('False', False)},
                                               'required': {'True': ('True', True), 'False': ('False', False)},
                                               'name': __name_definition}

'''
  Format used for it is:
  (System field name, (Friendly Field Name, Field instance to work with,
    {Field keyword argument name :  {
                                      'choice' : (Friendly Name, outcome),
                                    }
                                    or instance of property which .argument_format will be
                                    called upon and retrieve the outcome
                                    or callback to format the outcome})
'''
JOURNAL_FIELDS = collections.OrderedDict([('string', ('String', orm.SuperStringProperty, __default_journal_field_keywords_definition)),
                                          ('int', ('Integer', orm.SuperIntegerProperty, __default_journal_field_keywords_definition)),
                                          ('decimal', ('Decimal', orm.SuperDecimalProperty, __default_journal_field_keywords_definition)),
                                          ('float', ('Float', orm.SuperFloatProperty, __default_journal_field_keywords_definition)),
                                          ('datetime', ('DateTime', orm.SuperDateTimeProperty, {'required': {'True': ('True', True),
                                                                                                             'False': ('False', False)},
                                                                                                'auto_now': {'True': ('True', True),
                                                                                                             'False': ('False', False)},
                                                                                                'auto_now_add': {'True': ('True', True),
                                                                                                                 'False': ('False', False)},
                                                                                                'name': __name_definition})),
                                          ('bool', ('Boolean', orm.SuperBooleanProperty, __default_journal_field_keywords_definition)),
                                          ('reference', ('Reference', orm.SuperKeyProperty, {'repeated': {'True': ('True', True),
                                                                                                          'False': ('False', False)},
                                                                                             'required': {'True': ('True', True),
                                                                                                          'False': ('False', False)},
                                                                                             'kind': __kind_definition,
                                                                                             'name': __name_definition})),
                                          ('text', ('Text', orm.SuperTextProperty, __default_journal_field_keywords_definition)),
                                          ('json', ('JSON', orm.SuperJsonProperty, {'required': {'True': ('True', True),
                                                                                                 'False': ('False', False)},
                                                                                    'kind': __kind_definition,
                                                                                    'name': __name_definition}))])


class TransactionAction(orm.Action):
  
  arguments = orm.SuperPropertyStorageProperty('2', required=True, default={}, compressed=False, cfg=JOURNAL_FIELDS)


class TransactionPluginGroup(orm.PluginGroup):
  
  # First arg is list of plugin kind ids that user can create (e.g. ['1', '2', '3']).
  plugins = orm.SuperPluginStorageProperty([], '6', required=True, default=[], compressed=False)


# @todo sequencing counter is missing, and has to be determined how to solve that!
class Journal(orm.BaseExpando):
  
  _kind = 49
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = orm.SuperStringProperty('3', required=True)
  state = orm.SuperStringProperty('4', required=True, default='draft', choices=['draft', 'active', 'decommissioned'])
  entry_fields = orm.SuperPickleProperty('5', required=True, indexed=False, compressed=False)
  line_fields = orm.SuperPickleProperty('6', required=True, indexed=False, compressed=False)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('49'),
    '_code': orm.SuperComputedProperty(lambda self: self.key_id_str),
    '_transaction_actions': orm.SuperStorageStructuredProperty(orm.Action, storage='remote_multi'),
    '_transaction_plugin_groups': orm.SuperStorageStructuredProperty(orm.PluginGroup, storage='remote_multi')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('49', [orm.Action.build_key('49', 'prepare'),
                                  orm.Action.build_key('49', 'read'),
                                  orm.Action.build_key('49', 'update'),
                                  orm.Action.build_key('49', 'delete'),
                                  orm.Action.build_key('49', 'search'),
                                  orm.Action.build_key('49', 'activate'),
                                  orm.Action.build_key('49', 'decommission')], False, 'entity._original.namespace_entity._original.state != "active"'),
      orm.ActionPermission('49', [orm.Action.build_key('49', 'delete')], False, 'entity._original.state != "draft"'),
      orm.ActionPermission('49', [orm.Action.build_key('49', 'activate')], False, 'entity._original.state == "active"'),
      orm.ActionPermission('49', [orm.Action.build_key('49', 'decommission')], False, 'entity._is_system or entity._original.state != "active"'),
      orm.FieldPermission('49', ['created', 'updated', 'state'], False, None, 'True'),
      orm.FieldPermission('49', ['created', 'updated', 'name', 'state', 'entry_fields', 'line_fields', '_records',
                                 '_code', '_transaction_actions', '_transaction_plugin_groups'], False, False,
                          'entity._original.namespace_entity._original.state != "active"'),
      orm.FieldPermission('49', ['created', 'updated', 'name', 'state', 'entry_fields', 'line_fields', '_records',
                                 '_code'], False, None,
                          'entity._original.state != "draft"'),
      orm.FieldPermission('49', ['_transaction_actions',
                                 '_transaction_plugin_groups.name',
                                 '_transaction_plugin_groups.subscriptions',
                                 '_transaction_plugin_groups.active',
                                 '_transaction_plugin_groups.sequence',
                                 '_transaction_plugin_groups.transactional'], False, None,
                          'entity._is_system'),
      orm.FieldPermission('49', ['_transaction_plugin_groups.plugins'], False, None,
                          'entity._is_system and entity._original._transaction_plugin_groups.name != "User Plugins"'),  # @todo Missing index between _transaction_plugin_groups and name!
      orm.FieldPermission('49', ['state'], True, None,
                          '(action.key_id_str == "activate" and entity.state == "active") or (action.key_id_str == "decommission" and entity.state == "decommissioned")')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('49', 'prepare'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_journal'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('49', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='49', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_journal'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('49', 'update'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        '_code': orm.SuperStringProperty(required=True, max_size=64),  # Regarding max_size, take a look at the transaction.JournalUpdateRead() plugin!
        'name': orm.SuperStringProperty(required=True),
        'entry_fields': orm.SuperPropertyStorageProperty(required=True, cfg=JOURNAL_FIELDS),
        'line_fields': orm.SuperPropertyStorageProperty(required=True, cfg=JOURNAL_FIELDS),
        '_transaction_actions': orm.SuperLocalStructuredProperty(TransactionAction, repeated=True),
        '_transaction_plugin_groups': orm.SuperLocalStructuredProperty(TransactionPluginGroup, repeated=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_journal.state': 'draft'},  # @todo Do we handle this like this!?
                     'd': {'_journal.name': 'input.name',
                           '_journal.entry_fields': 'input.entry_fields',
                           '_journal.line_fields': 'input.line_fields',
                           '_journal._transaction_actions': 'input._transaction_actions',
                           '_journal._transaction_plugin_groups': 'input._transaction_plugin_groups'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_journal'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('49', 'delete'),
      arguments={
        'key': orm.SuperKeyProperty(kind='49', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Delete(),
            Set(cfg={'d': {'output.entity': '_journal'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('49', 'search'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'orders': [{'field': 'name', 'operator': 'asc'}]},
          cfg={
            'search_arguments': {'kind': '49', 'options': {'limit': settings.SEARCH_PAGE}},
            'filters': {'name': orm.SuperStringProperty(),
                        'state': orm.SuperStringProperty(choices=[])},
            'indexes': [{'orders': [('name', ['asc', 'desc'])]},
                        {'orders': [('state', ['asc', 'desc'])]},
                        {'filters': [('name', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!=']), ('name', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]}]
            }
          )
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Search(),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('49', 'activate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='49', required=True),
        'message': orm.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_journal.state': 'active'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_journal'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('49', 'decommission'),
      arguments={
        'key': orm.SuperKeyProperty(kind='49', required=True),
        'message': orm.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_journal.state': 'decommissioned'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_journal'}})
            ]
          )
        ]
      )
    ]
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    code = input.get('_code')
    return cls.build_key(code, namespace=kwargs.get('domain').urlsafe())  # @todo Possible prefix?
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')


class CategoryBalance(orm.BaseModel):
  
  _kind = 71
  
  from_date = orm.SuperDateTimeProperty('1', required=True, indexed=False)
  to_date = orm.SuperDateTimeProperty('2', required=True, indexed=False)
  debit = orm.SuperDecimalProperty('3', required=True, indexed=False)
  credit = orm.SuperDecimalProperty('4', required=True, indexed=False)
  balance = orm.SuperDecimalProperty('5', required=True, indexed=False)
  uom = orm.SuperLocalStructuredProperty(uom.UOM, '6', required=True, indexed=False)


class Category(orm.BaseExpando):
  
  _kind = 47
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  parent_record = orm.SuperKeyProperty('3', kind='47')
  name = orm.SuperStringProperty('4', required=True)
  complete_name = orm.SuperTextProperty('5', required=True)
  active = orm.SuperBooleanProperty('6', required=True, default=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'description': orm.SuperTextProperty('7'),
    'balances': orm.SuperLocalStructuredProperty(CategoryBalance, '8', repeated=True)
    }
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('47'),
    '_code': orm.SuperComputedProperty(lambda self: self.key_id_str)
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('47', [orm.Action.build_key('47', 'prepare'),
                                  orm.Action.build_key('47', 'create'),
                                  orm.Action.build_key('47', 'read'),
                                  orm.Action.build_key('47', 'update'),
                                  orm.Action.build_key('47', 'delete'),
                                  orm.Action.build_key('47', 'search')], False, 'entity._original.namespace_entity._original.state != "active"'),
      orm.ActionPermission('47', [orm.Action.build_key('47', 'create'),
                                  orm.Action.build_key('47', 'update'),
                                  orm.Action.build_key('47', 'delete')], False, 'entity._is_system'),
      orm.ActionPermission('47', [orm.Action.build_key('47', 'delete')], False, 'entity._is_used'),
      orm.FieldPermission('47', ['created', 'updated'], False, None, 'True'),
      orm.FieldPermission('47', ['created', 'updated', 'parent_record', 'name', 'complete_name',
                                 'active', 'description', 'balances', '_records', '_code'], False, False,
                          'entity._original.namespace_entity._original.state != "active"'),
      orm.FieldPermission('47', ['created', 'updated', 'parent_record', 'name', 'complete_name',
                                 'active', 'description', 'balances', '_records', '_code'], False, None,
                          'entity._is_system')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('47', 'prepare'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_category'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'create'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        '_code': orm.SuperStringProperty(required=True, max_size=64),  # Regarding max_size, take a look at the transaction.CategoryUpdateRead() plugin!
        'parent_record': orm.SuperKeyProperty(kind='47'),
        'name': orm.SuperStringProperty(required=True),
        'active': orm.SuperBooleanProperty(required=True, default=True),
        'description': orm.SuperTextProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            CategoryUpdateSet(),  # @todo Unless we decide to implement that complete_name handling property, this will stay.
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_category'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='47', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_category'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='47', required=True),
        'parent_record': orm.SuperKeyProperty(kind='47'),
        'name': orm.SuperStringProperty(required=True),
        'active': orm.SuperBooleanProperty(required=True, default=True),
        'description': orm.SuperTextProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            CategoryUpdateSet(),  # @todo Unless we decide to implement that complete_name handling property, this will stay.
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_category'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'delete'),
      arguments={
        'key': orm.SuperKeyProperty(kind='47', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Delete(),
            Set(cfg={'d': {'output.entity': '_category'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'search'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'search': orm.SuperSearchProperty(
          default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}], 'orders': [{'field': 'name', 'operator': 'asc'}]},
          cfg={
            'search_by_keys': True,
            'search_arguments': {'kind': '47', 'options': {'limit': settings.SEARCH_PAGE}},
            'filters': {'name': orm.SuperStringProperty(),
                        'active': orm.SuperBooleanProperty()},
            'indexes': [{'orders': [('name', ['asc', 'desc'])]},
                        {'orders': [('created', ['asc', 'desc'])]},
                        {'orders': [('updated', ['asc', 'desc'])]},
                        {'orders': [('active', ['asc', 'desc'])]},
                        {'filters': [('name', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('active', ['=='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('active', ['==']), ('name', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]}]
            }
          )
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Search(),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      )
    ]
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    code = input.get('_code')
    return cls.build_key(code, namespace=kwargs.get('namespace'))  # @todo Possible prefix?
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')
  
  @property
  def _is_used(self):
    if self.key.id() is None:
      return False
    category = self.query(self.parent_record == self.key).get()
    line = Line.query(Line.categories == self.key).get()
    return (category is not None) or (line is not None)


class Line(orm.BaseExpando):
  
  _kind = 51
  
  # ancestor Entry (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_move_line.py#L432
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_analytic_line.py#L29
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l486
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/line.py#l14
  # uvek se prvo sekvencionisu linije koje imaju debit>0 a onda iza njih slede linije koje imaju credit>0
  # u slucaju da je Entry balanced=True, zbir svih debit vrednosti u linijama mora biti jednak zbiru credit vrednosti
  journal = orm.SuperKeyProperty('1', kind=Journal, required=True)  # delete
  company = orm.SuperKeyProperty('2', kind='44', required=True)  # delete
  state = orm.SuperIntegerProperty('3', required=True)  # delete
  date = orm.SuperDateTimeProperty('4', required=True)  # delete
  sequence = orm.SuperIntegerProperty('5', required=True)  # @todo Can we sequence Line.id()?
  categories = orm.SuperKeyProperty('6', kind=Category, repeated=True)
  debit = orm.SuperDecimalProperty('7', required=True, indexed=False)  # debit=0 u slucaju da je credit>0, negativne vrednosti su zabranjene
  credit = orm.SuperDecimalProperty('8', required=True, indexed=False)  # credit=0 u slucaju da je debit>0, negativne vrednosti su zabranjene
  uom = orm.SuperLocalStructuredProperty(uom.UOM, '9', required=True)
  # Expando
  # neki upiti na Line zahtevaju "join" sa Entry poljima
  # taj problem se mozda moze resiti map-reduce tehnikom ili kopiranjem polja iz Entry-ja u Line-ove
  
  def get_kind(self):  # @todo Do we need this?
    return 'l_%s' % self.parent_entity.journal.id()
  
  def get_actions(self):  # @todo Do we need this?
    journal_actions = orm.Action.query(orm.Action.active == True,
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


class Entry(orm.BaseExpando):
  
  _kind = 50
  
  # ancestor Group (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L1279
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l38
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  journal = orm.SuperKeyProperty('3', kind=Journal, required=True)
  name = orm.SuperStringProperty('4', required=True)
  state = orm.SuperStringProperty('5', required=True)
  date = orm.SuperDateTimeProperty('6', required=True)
  
  _virtual_fields = {
    '_lines': orm.SuperLocalStructuredProperty(Line, repeated=True)
    }
  
  def get_kind(self):
    return 'e_%s' % self.journal.id()
  
  def get_actions(self):
    journal_actions = orm.Action.query(orm.Action.active == True,
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
    journal_actions = orm.Action.query(orm.Action.active == True,
                                       ancestor=self.journal).fetch()
    actions = {}
    for action in journal_actions:
      actions[action.key.urlsafe()] = action
    return actions


class Group(orm.BaseExpando):
  
  _kind = 48
  
  _default_indexed = False
