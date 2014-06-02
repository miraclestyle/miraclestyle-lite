# -*- coding: utf-8 -*-
'''
Created on Jun 2, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv.event import Action
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.srv import log as ndb_log
from app.srv import uom as ndb_uom
from app.plugins import common, rule, log, callback, notify


class Journal(ndb.BaseExpando):
  
  _kind = 49
  
  # root (namespace Domain)
  # key.id() = prefix_<user supplied value>
  # key.id defines constraint of unique journal code (<user supplied value> part of the key.id) per domain.
  # @todo sequencing counter is missing, and has to be determined how to solve that!
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = ndb.SuperStringProperty('3', required=True)
  state = ndb.SuperStringProperty('4', required=True, default='draft', choices=['draft', 'active', 'decommissioned'])
  entry_fields = ndb.SuperPickleProperty('5', required=True, compressed=False)
  line_fields = ndb.SuperPickleProperty('6', required=True, compressed=False)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('49', repeated=True)
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
      FieldPermission('49', ['created', 'updated', 'name', 'state', 'entry_fields', 'line_fields', '_records'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('49', ['created', 'updated', 'name', 'state', 'entry_fields', 'line_fields', '_records'], False, None,
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
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'output.entity': 'entities.49'})
        ]
      ),
    Action(
      key=Action.build_key('49', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.49'})
        ]
      ),
    Action(
      key=Action.build_key('49', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'entry_fields': ndb.SuperJsonProperty(required=True),
        'line_fields': ndb.SuperJsonProperty(required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        transaction.JournalSet(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.49'}),
        callback.Notify(transactional=True),
        callback.Exec(transactional=True)
        ]
      ),
    Action(
      key=Action.build_key('49', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True)
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
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.49'}),
        callback.Notify(transactional=True),
        callback.Exec(transactional=True)
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
      key=Action.build_key('49', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
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
      ),
    Action(
      key=Action.build_key('49', 'activate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True),
        'message': ndb.SuperTextProperty(required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(static_values={'values.49.state': 'active'}),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        rule.Prepare(transactional=True, skip_user_roles=False, strict=False),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.49'}),
        callback.Notify(transactional=True),
        callback.Exec(transactional=True)
        ]
      ),
    Action(
      key=Action.build_key('49', 'decommission'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='49', required=True),
        'message': ndb.SuperTextProperty(required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(static_values={'values.49.state': 'decommissioned'}),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        rule.Prepare(transactional=True, skip_user_roles=False, strict=False),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.49'}),
        callback.Notify(transactional=True),
        callback.Exec(transactional=True)
        ]
      )
    ]
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')
  
  # _actions [prepare, read, update, delete, search, read_records, activate, decommission]


class CategoryBalance(ndb.BaseExpando):
  
  _kind = 71
  
  # LocalStructuredProperty model
  # ovaj model dozvoljava da se radi feedback trending per month per year
  # mozda bi se mogla povecati granulacija per week, tako da imamo oko 52 instance per year, ali mislim da je to nepotrebno!
  # ovde treba voditi racuna u scenarijima kao sto je napr. promena feedback-a iz negative u positive state,
  # tako da se za taj record uradi negative_feedback_count - 1 i positive_feedback_count + 1
  # najbolje je raditi update jednom dnevno, ne treba vise od toga, tako da bi mozda cron ili task queue bilo resenje za agregaciju
  from_date = ndb.SuperDateTimeProperty('1', auto_now_add=True, required=True)
  to_date = ndb.SuperDateTimeProperty('2', auto_now_add=True, required=True)
  debit = ndb.SuperDecimalProperty('3', required=True, indexed=False)# debit=0 u slucaju da je credit>0, negativne vrednosti su zabranjene
  credit = ndb.SuperDecimalProperty('4', required=True, indexed=False)
  balance = ndb.SuperDecimalProperty('5', required=True, indexed=False)
  uom = ndb.SuperLocalStructuredProperty(uom.UOM, '6', required=True)


class Category(ndb.BaseExpando):
  
  _kind = 47
  
  # root (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L448
  # http://hg.tryton.org/modules/account/file/933f85b58a36/account.py#l525
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/account.py#l19
  parent_record = ndb.SuperKeyProperty('1', kind='47', required=True)
  name = ndb.SuperStringProperty('2', required=True)
  code = ndb.SuperStringProperty('3', required=True)
  active = ndb.SuperBooleanProperty('4', required=True, default=True)
  complete_name = ndb.SuperTextProperty('5', required=True)
  
  _expando_fields = {
    'description': ndb.SuperTextProperty('6'),
    'balances': ndb.SuperLocalStructuredProperty(CategoryBalance, '7', repeated=True)
    }


class Group(ndb.BaseExpando):
  
  _kind = 48
  
  # root (namespace Domain)


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
