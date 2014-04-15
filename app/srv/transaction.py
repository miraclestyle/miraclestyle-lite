# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import collections

from app import ndb
from app.srv import uom


class Context:
  
  def __init__(self, **kwargs):
    self.group = None
    self.entities = collections.OrderedDict()


class Journal(ndb.BaseExpando):
  
  _kind = 49
  
  # root (namespace Domain)
  # key.id() = prefix_<user supplied value>
  # key.id defines constraint of unique journal code (<user supplied value> part of the key.id) per domain.
  # @todo sequencing counter is missing, and has to be determined how to solve that!
  
  name = ndb.SuperStringProperty('1', required=True)
  state = ndb.SuperStringProperty('2', required=True, choices=['draft', 'active', 'decommissioned'])
  entry_fields = ndb.SuperPickleProperty('3', required=True, compressed=False)
  line_fields = ndb.SuperPickleProperty('4', required=True, compressed=False)
  plugin_categories = ndb.SuperStringProperty('5', repeated=True)  # @todo Not sure if we will need this?
  
  def get_kind(self):  # @todo Do we need this?
    return 'j_%s' % self.key.id()
  
  def get_key(self, *args, **kwargs):
    if not self.key:
      return self.set_key(*args, **kwargs)
    else:
      return self.key
  
  def set_entry_global_role(self, entry):
    if hasattr(self, '_entry_global_role') and entry:
      entry._global_role = self._entry_global_role
  
  def _instance_actions(self):
    journal_actions = Action.query(Action.active == True,
                                   ancestor=self.key).fetch()
    actions = {}
    for action in journal_actions:
      actions[action.key.urlsafe()] = action
    return actions
  
  def _instance_plugins(self, action_key):
    plugins = Plugin.query(Plugin.active == True,
                           Plugin.subscriptions == action_key,
                           ancestor=self.key).order(Plugin.sequence).fetch()
    return plugins


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
