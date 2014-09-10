# -*- coding: utf-8 -*-
'''
Created on Aug 30, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models import *
from app.plugins import *


class OrderLineTax(orm.BaseModel):
  
  _kind = 116
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  code = orm.SuperStringProperty('2', required=True, indexed=False)
  formula = orm.SuperPickleProperty('3', required=True, indexed=False)


class OrderLine(orm.BaseExpando):
  
  _kind = 51
  
  _use_rule_engine = False
  
  sequence = orm.SuperIntegerProperty('1', required=True)
  description = orm.SuperTextProperty('2', required=True)
  product_reference = orm.SuperKeyProperty('3', kind='38', required=True, indexed=False)
  product_variant_signature = orm.SuperJsonProperty('4', required=True)
  product_category_complete_name = orm.SuperTextProperty('5', required=True)
  product_category_reference = orm.SuperKeyProperty('6', kind='17', required=True, indexed=False)
  code = orm.SuperStringProperty('7', required=True, indexed=False)
  unit_price = orm.SuperDecimalProperty('8', required=True, indexed=False)
  product_uom = orm.SuperLocalStructuredProperty('19', '9', required=True)
  quantity = orm.SuperDecimalProperty('10', required=True, indexed=False)
  discount = orm.SuperDecimalProperty('11', required=True, indexed=False)
  taxes = orm.SuperLocalStructuredProperty('116', '12', repeated=True)
  subtotal = orm.SuperDecimalProperty('13', required=True, indexed=False)
  discount_subtotal = orm.SuperDecimalProperty('14', required=True, indexed=False)
  total = orm.SuperDecimalProperty('15', required=True, indexed=False)
  
  _default_indexed = False


class Order(orm.BaseExpando):
  
  _kind = xx
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = orm.SuperStringProperty('3', required=True)
  state = orm.SuperStringProperty('4', required=True)
  date = orm.SuperDateTimeProperty('5', required=True)
  seller = orm.SuperKeyProperty('6', kind='23', required=True, indexed=False)  # @todo buyer_reference ??
  company_address = orm.SuperLocalStructuredProperty('68', '7', required=True)
  billing_address_reference = orm.SuperKeyProperty('8', kind='9', required=True, indexed=False)
  shipping_address_reference = orm.SuperKeyProperty('9', kind='9', required=True, indexed=False)
  billing_address = orm.SuperLocalStructuredProperty('68', '10', required=True)
  shipping_address = orm.SuperLocalStructuredProperty('68', '11', required=True)
  currency = orm.SuperLocalStructuredProperty('19', '12', required=True)
  untaxed_amount = orm.SuperDecimalProperty('13', required=True, indexed=False)
  tax_amount = orm.SuperDecimalProperty('14', required=True, indexed=False)
  total_amount = orm.SuperDecimalProperty('15', required=True, indexed=False)
  paypal_reciever_email = orm.SuperStringProperty('16', required=True, indexed=False)
  paypal_business = orm.SuperStringProperty('17', required=True, indexed=False)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_lines': orm.SuperRemoteStructuredProperty(OrderLine, repeated=True),
    '_records': orm.SuperRecordProperty('xx')
    }

# transaction.py #

# -*- coding: utf-8 -*-
'''
Created on Jun 2, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.ext.ndb.google_imports import entity_pb

from app import orm, settings
from app.models import uom
from app.models.base import *
from app.plugins.base import *
from app.plugins.transaction import *

defaults1 = ()
defaults2 = ('required',)


JOURNAL_FIELDS = ((orm.SuperStringProperty(), defaults1, defaults2), (orm.SuperTextProperty(), defaults1, defaults2),
                  (orm.SuperIntegerProperty(), defaults1, defaults2), (orm.SuperFloatProperty(), defaults1, defaults2),
                  (orm.SuperDecimalProperty(), defaults1, defaults2), (orm.SuperBooleanProperty(), defaults1, defaults2),
                  (orm.SuperJsonProperty(), defaults1, defaults2), (orm.SuperKeyProperty(), defaults1, defaults2),
                  (orm.SuperDateTimeProperty(), defaults1, defaults2))


class Action(orm.Action):
  
  _kind = 84
  
  _use_rule_engine = False
  
  arguments = orm.SuperPropertyStorageProperty('2', required=True, default={}, compressed=False, cfg=JOURNAL_FIELDS)
  
  @classmethod
  def build_key(cls, *args, **kwargs):
    new_args = [cls._get_kind()]
    new_args.extend(args)
    return orm.Key(*new_args, **kwargs)


class PluginGroup(orm.PluginGroup):
  
  _kind = 85
  
  _use_rule_engine = False
  
  subscriptions = orm.SuperKeyProperty('2', kind='84', repeated=True)
  plugins = orm.SuperPluginStorageProperty(('0',), '6', required=True, default=[], compressed=False)  # First arg is list of plugin kind ids that user can create, e.g. ('1', '2', '3').


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
    '_transaction_actions': orm.SuperRemoteStructuredProperty(Action, repeated=True),
    '_transaction_plugin_groups': orm.SuperRemoteStructuredProperty(PluginGroup, repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('49', [orm.Action.build_key('49', 'prepare'),
                                  orm.Action.build_key('49', 'create'),
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
      key=orm.Action.build_key('49', 'create'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        '_code': orm.SuperStringProperty(required=True, max_size=64),  # Regarding max_size, take a look at the transaction.JournalUpdateRead() plugin!
        'name': orm.SuperStringProperty(required=True),
        'entry_fields': orm.SuperPropertyStorageProperty(required=True, cfg=JOURNAL_FIELDS),
        'line_fields': orm.SuperPropertyStorageProperty(required=True, cfg=JOURNAL_FIELDS)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_journal.state': 'draft'},
                     'd': {'_journal.name': 'input.name',
                           '_journal.entry_fields': 'input.entry_fields',
                           '_journal.line_fields': 'input.line_fields'}}),
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
        'key': orm.SuperKeyProperty(kind='49', required=True),
        'name': orm.SuperStringProperty(required=True),
        'entry_fields': orm.SuperPropertyStorageProperty(required=True, cfg=JOURNAL_FIELDS),
        'line_fields': orm.SuperPropertyStorageProperty(required=True, cfg=JOURNAL_FIELDS),
        '_transaction_actions': orm.SuperLocalStructuredProperty(Action, repeated=True),
        '_transaction_plugin_groups': orm.SuperLocalStructuredProperty(PluginGroup, repeated=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_journal.name': 'input.name',
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
    return cls.build_key(code, namespace=kwargs.get('namespace'))  # @todo Possible prefix?
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')


# @todo Chained category keys conclusion!
# While ancestor quieries work on incomplete keys (e.g. root keys of ancestor keys), key fields can not be filtered this way!
# Chained categories prove to be useless in terms of filtering and obtaining debit/credit balances.
# Prmitive example of balance calculation algorithm is provided under the Category class.
# The provided algorithm mimics that of OpenERP however, it is extreamly inflexibile and limited.
# We would probably have to use it only for obtaining category._children_records, nothing more!
# The balance calcualtion would probably have to be done from Line perspective, with search action that will take
# Line.categories.IN(category._children_records) filter among the others! This way complex queries could be triggered,
# e.g. Line.query(Line.categories.IN(category._children_records), Line.product_reference == 'product_key', Line.uom.symbol == 'kg').fetch()
# Nevertheless, this aproach is practically unscalable,
# and will dramatically degrade in terms of performance as the dataset expands (to do inventory you have to query for lines from the beginning of time)!
# Google search engine will not be of any help here, as it imposes index size limit (10GB) and number of results returned (10K)!
# And data in this case is expected to expand, probably beyond any other model defined in the app!

# Possible solution...
# The only reasonable solution to the balance calcualtion, would be use of google search engine in a unique to the category way.
# The logic of this process should reside in plugin(s).
# There should be search index per every Category, created using Category._code and namespace.
# Each transaction should create search document per entry line that will be organized in search indexes per line category,
# respectfully. Documents will contain the subset of line data, that is only valuable to the search queries, nothing more!
# After a certain number of docuemnt entries for particualr category + custom filter (e.g. product reference),
# agregate 'snapshot' should be created buy summarizing previous lines' debit/credit values, and erasing the same lines
# from index, efectively preserving important data!
# This way, searh documents per filter will be kept in low number and index could persist.
# The reason we use google search engine is because of it's dynamic nature that can utilize different queries in runtime,
# something that datastore can not do without composite indexes. Plugin(s) should exist for each category use case.
# For example: inventory plugin(s) should be able to create search documents based on entry lines, record documents
# (during transaction) in adequate indexes, query indexes before each transaction commit to validate that inventory
# has product on stock. This arangement can be done for every scenario, and therefore should not have problem of scaling!
class CategoryBalance(orm.BaseModel):
  
  _kind = 71
  
  _use_rule_engine = False
  
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
  
  ######################################################
  # Primitive example of real time balance calculator! #
  ######################################################
  
  @classmethod
  def _get_children(cls, parent_records, children):
    entities = []
    for parent_record in parent_records:
      entities.extend(cls.query(cls.parent_record == parent_record).fetch(keys_only=True))
    if len(entities):
      children.extend(entities)
      cls._get_children(entities, children)
  
  @classmethod
  def _get_balance(cls, category):
    debit = 0
    credit = 0
    lines = Line.query(Line.categories.IN(category._children_records)).fetch()
    for line in lines:
      debit += line.debit
      credit += line.credit
    return (debit, credit, (debit - credit))
  
  @classmethod
  def _post_get_hook(cls, key, future):
    # @todo Missing super extension!
    entity = future.get_result()
    if entity is not None and entity.key:
      entity._children_records = [entity.key]
      entity._get_children([entity.key], entity._children_records)
      entity._debit, entity._credit, entity._balance = entity._get_balance(entity)
  
  ###################
  # End of example! #
  ###################
  
  _expando_fields = {
    'description': orm.SuperTextProperty('7'),
    'balances': orm.SuperLocalStructuredProperty(CategoryBalance, '8', repeated=True)
    }
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('47'),
    '_code': orm.SuperComputedProperty(lambda self: self.key_id_str)
    #'_debit': orm.SuperComputedProperty(lambda self: self._debit),
    #'_credit': orm.SuperComputedProperty(lambda self: self._credit),
    #'_balance': orm.SuperComputedProperty(lambda self: self._balance),
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
    category = self.query(self.__class__.parent_record == self.key).get()
    line = Line.query(Line.categories == self.key).get()
    return (category is not None) or (line is not None)


# @todo Conclusion regarding Line fields!
# The only field that is mandated to every line instance, regardless of its role in transaction engine, is sequence!
# Other fields are included to improve datastore query profile on entry lines!
# Sugestion: Search engine has to be tested against minimum fields possible, and that will bring final answer to the
# final entry line design!
class Line(orm.BaseExpando):
  '''Notes:
  We always seqence lines that have debit > 0, and after them come lines that have credit > 0
  In case that Entry.balanced=True, sum of all debit amounts must eqal to sum of all credit amounts.
  To make instances of lines, you must always provide parent key, that is entry's key.
  Otherwise it will break!
  Fields can only be properly loaded if are:
  - loaded from datastore
  - instanced with proper keyword argument Entry (journal or _model_schema) and Line (parent)
  
  '''
  _kind = 51
  
  _use_rule_engine = False
  
  _journal_fields_loaded = None
  
  # Expando
  # Some queries on Line require "join" with Entry.
  # That problem can be solved using search engine (or keeping some entry field values copied to lines)!
  
  #journal = orm.SuperKeyProperty('1', kind=Journal, required=True)  # delete
  #company = orm.SuperKeyProperty('2', kind='44', required=True)  # delete
  #state = orm.SuperIntegerProperty('3', required=True)  # delete
  #date = orm.SuperDateTimeProperty('4', required=True)  # delete
  sequence = orm.SuperIntegerProperty('5', required=True)
  categories = orm.SuperKeyProperty('6', kind='47', repeated=True)
  debit = orm.SuperDecimalProperty('7', required=True, indexed=False)  # debit = 0 in case that credit > 0, negative values are forbidden.
  credit = orm.SuperDecimalProperty('8', required=True, indexed=False)  # credit = 0 in case that debit > 0, negative values are forbidden.
  uom = orm.SuperLocalStructuredProperty(uom.UOM, '9', required=True)
  
  def __init__(self, *args, **kwargs):
    '''Caution! Making instances of Line() inside a transaction may
    cause performing non-entity group queries (see in add journal fields).
    As for get()s itself it will use in-memory cache when it can.
    
    '''
    entry_key = kwargs.get('parent')
    complete_key = kwargs.get('key')  # Also observe the complete key instances.
    journal_key = kwargs.pop('journal', None) # if journal key is provided use it. This is generally retarded but only way so far.
    if journal_key is not None:
      self.add_journal_fields(journal_key)
    elif entry_key is not None:
      self.add_journal_fields(entry_key.entity.journal)
    elif complete_key is not None:
      self.add_journal_fields(complete_key.parent_entity.journal)
    # we intentionally call this code before __init__ due __init__ ability to deepcopy the entity and other things beside that.
    super(Line, self).__init__(*args, **kwargs)
  
  def add_journal_fields(self, journal_key=None):
    if not self._journal_fields_loaded:
      if not journal_key and self.key:
        journal_key = self.parent_entity.journal
      journal = journal_key.get()
      if journal is None:
        raise Exception('Cannot find journal with key %r.' % journal_key)
      self._clone_properties()
      for name, prop in journal.line_fields.iteritems():
        # still not 100% sure if we need to deepcopy these properties that get loaded from datastore
        prop._code_name = name
        self._properties[prop._name] = prop
        self.add_output(name)
      self._journal_fields_loaded = True
  
  def get_kind(self):
    return '%s_%s' % (self._get_kind(), self.journal.id())
  
  def get_fields(self):
    fields = super(Line, self.__class__).get_fields()  # Calling parent get_fields.
    for name, prop in self._properties.iteritems():
      fields[prop._code_name] = prop
    return fields
  
  def _get_property_for(self, p, indexed=True, depth=0):
    '''It is always easier to override _get_property_for because you immidiately get self which tells you on which
    entity you operate, and if the entity itself has a key.
    
    '''
    if self.key is None or self.key.parent() is None:
      raise Exception('Cannot load properties of %s because it does not have parent key provided.' % self)
    else:
      if self._journal_fields_loaded is None:
        self.add_journal_fields()
    return super(Line, self)._get_property_for(p, indexed, depth)
  
  @classmethod
  def get_meta(cls):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    dic = {}
    dic['_actions'] = getattr(cls, '_actions', [])
    dic.update(super(Line, cls).get_fields())
    return dic


# @todo Conclusion regarding Entry fields!
# The only fields that are mandated to every entry instance, regardless of its role in transaction engine, are:
# created, updated and journal! Other fields are included to improve datastore query profile on entries!
# Sugestion: Search engine has to be tested against minimum fields possible, and that will bring final answer to the
# final entry design!
class Entry(orm.BaseExpando):
  '''Notes:
  In order to make proper instances of entries you must always either provide journal or _model_schema argument in constructor.
  Fields can only be properly loaded if are:
  - loaded from datastore
  - instanced with proper keyword argument Entry (journal or _model_schema) and Line (parent)
  
  '''
  _kind = 50
  
  _journal_fields_loaded = None  # Used to flag if the journal fields were loaded.
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  journal = orm.SuperKeyProperty('3', kind=Journal, required=True)
  name = orm.SuperStringProperty('4', required=True)
  state = orm.SuperStringProperty('5', required=True)  # @todo Bad thing about this prop being defined statically is that we can not have choices and default value, thus less abstraction!
  date = orm.SuperDateTimeProperty('6', required=True)
  
  _virtual_fields = {
    '_lines': orm.SuperRemoteStructuredProperty(Line, repeated=True)
    }
  
  _global_roles = {'system_sales_order': GlobalRole(
    permissions=[
      orm.FieldPermission('50', ['created', 'updated', 'state'], False, None, 'True'),
      orm.FieldPermission('50', ['created', 'updated', 'name', 'state', 'entry_fields', 'line_fields', '_records',
                                 '_code', '_transaction_actions', '_transaction_plugin_groups'], False, False,
                          'entity._original.namespace_entity._original.state != "active"'),
      orm.FieldPermission('50', ['created', 'updated', 'name', 'state', 'entry_fields', 'line_fields', '_records',
                                 '_code'], False, None,
                          'entity._original.state != "draft"'),
      orm.FieldPermission('50', ['_transaction_actions',
                                 '_transaction_plugin_groups.name',
                                 '_transaction_plugin_groups.subscriptions',
                                 '_transaction_plugin_groups.active',
                                 '_transaction_plugin_groups.sequence',
                                 '_transaction_plugin_groups.transactional'], False, None,
                          'entity._is_system'),
      orm.FieldPermission('50', ['_transaction_plugin_groups.plugins'], False, None,
                          'entity._is_system and entity._original._transaction_plugin_groups.name != "User Plugins"'),  # @todo Missing index between _transaction_plugin_groups and name!
      orm.FieldPermission('50', ['state'], True, None,
                          '(action.key_id_str == "activate" and entity.state == "active") or (action.key_id_str == "decommission" and entity.state == "decommissioned")')
      ]
    )}
  
  @property
  def _global_role(self):
    return self._global_roles.get(self.journal._id_str)
  
  def __init__(self, *args, **kwargs):
    '''Caution! Making instances of Entry() inside a transaction may
    cause performing non-entity group queries (see journal_key.get() in add journal fields).
    As for get() itself it will use in-memory cache when it can.
    
    '''
    journal = kwargs.get('journal')
    _model_schema = kwargs.pop('_model_schema', None)
    namespace = kwargs.get('namespace')
    if journal is None and (_model_schema is not None and namespace is not None):
      journal = Journal.build_key(_model_schema, namespace=namespace)
      kwargs['journal'] = journal
    if journal:
      self.add_journal_fields(journal)
    super(Entry, self).__init__(*args, **kwargs)
  
  def add_journal_fields(self, journal_key=None):
    if not self._journal_fields_loaded: # prevent from loading too many times
      if journal_key is None:
        journal_key = self.journal
      journal = journal_key.get()
      if journal is None:
        raise Exception('Cannot find journal with key %r.' % journal_key)
      self._clone_properties()
      for name, prop in journal.entry_fields.iteritems():
        prop._code_name = name
        self._properties[prop._name] = prop
        self.add_output(name)
      self._journal_fields_loaded = True
  
  def get_kind(self):  # @todo Do we have security breach here, without inclusion of namespace?
    return '%s_%s' % (self._get_kind(), self.journal.id())
  
  @property
  def _actions(self):  # @todo Cache if possible for performance gains!
    return Action.query(Action.active == True, ancestor=self.journal).fetch()
  
  def get_actions(self):
    return getattr(self, '_actions', [])
  
  def get_action(self, action):
    if isinstance(action, orm.Key):
      action_key = action
    else:
      try:
        action_key = orm.Key(urlsafe=action)
      except:
        action_key = Action.build_key(action, parent=self.journal)
    return action_key.get()
  
  def get_plugin_groups(self, action):
    return PluginGroup.query(PluginGroup.active == True,
                             PluginGroup.subscriptions == action.key,
                             ancestor=self.journal).order(PluginGroup.sequence).fetch()
  
  def get_fields(self):
    fields = super(Entry, self.__class__).get_fields()  # Calling parent get_fields.
    for name, prop in self._properties.iteritems():
      fields[prop._code_name] = prop
    return fields
  
  @classmethod
  def _from_pb(cls, pb, set_key=True, ent=None, key=None):
    '''Internal helper to create an entity from an EntityProto protobuf.
    First 10 lines of code are copied from original from_pb in order to mimic
    construction of entity instance based on its function args. The rest of the code bellow is
    used to forcefully attempt to attach properties from journal entry_fields.
    
    This is complicated because in order to properly deserialize from datastore, the deserialization
    process can only begin after we have successfully retrieved entry_fields from journal.
    
    '''
    if not isinstance(pb, entity_pb.EntityProto):
      raise TypeError('pb must be an instance of EntityProto; received %r' % pb)
    if ent is None:
      ent = cls()
    # A key passed in overrides a key in the pb.
    if key is None and pb.key().path().element_size():
      key = orm.Key(reference=pb.key())
    # If set_key is not set, skip a trivial incomplete key.
    if key is not None and (set_key or key.id() or key.parent()):
      ent._key = key
    indexed_properties = pb.property_list()
    unindexed_properties = pb.raw_property_list()
    projection = []
    all_props = [indexed_properties, unindexed_properties]
    added_fields = False
    for plist in all_props:
      for p in plist:
        # First find the journal. Then load all needed props and break the loop.
        journal_name = cls.journal._name
        if journal_name is None:
          journal_name = cls.journal._code_name
        if p.name() == journal_name:
          prop = ent._get_property_for(p, plist is indexed_properties)
          prop._deserialize(ent, p)  # Calling deserialize on entities prop will unpack the property and set the value to the entity.
          ent.add_journal_fields()  # Calling add_journal_fields without argument will use self.journal as journal key.
          added_fields = True
          break
    if not added_fields:
      raise Exception('Cannot proceed with loading of entry %s. Journal fields failed to set.' % ent)
    return super(Entry, cls)._from_pb(pb, set_key, ent, ent.key)  # Calling parent from_pb to attempt to mantain compatibility with possible NDB upgrades?

  @classmethod
  def get_meta(cls):
    '''This function returns dictionary of meta data (not stored or dynamically generated data) of the model.
    The returned dictionary can be transalted into other understandable code to clients (e.g. JSON).
    
    '''
    dic = {}
    dic['_actions'] = getattr(cls, '_actions', [])
    dic.update(super(Entry, cls).get_fields())
    return dic

class Group(orm.BaseExpando):
  
  _kind = 48
  
  _use_rule_engine = False
  _use_record_engine = False  # @todo This entity itself should probably not recorded, but we are not sure yet!
  
  _default_indexed = False
  
  _entries = None
  
  def get_entry(self, journal_key):
    for _entry in self._entries:
      if _entry.journal == journal_key:
        return _entry
  
  def insert_entry(self, entry):
    for _entry in self._entries:
      if _entry.journal == entry.journal:
        return
    self._entries.append(entry)


# from setup.py #

  def execute_create_order_journal(self):
    config_input = self.config.next_operation_input
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    models = self.context.models
    Journal = models['49']
    Action = models['84']
    PluginGroup = models['85']
    CartInit = models['99']
    PayPalPayment = models['108']
    LinesInit = models['100']
    AddressRule = models['107']
    ProductToLine = models['101']
    ProductSubtotalCalculate = models['104']
    TaxSubtotalCalculate = models['110']
    OrderTotalCalculate = models['105']
    RulePrepare = models['93']
    TransactionWrite = models['114']
    CallbackNotify = models['115']
    CallbackExec = models['97']
    Unit = models['19']
    entity = Journal(namespace=namespace, id='system_sales_order')
    entity.name = 'Sales Order Journal'
    entity.state = 'active'
    # this two need to be ordered Dictionaries because using unordered dict will cause
    # weird behaviour on user interface (e.g. on each refresh different order of properties
    entity.entry_fields = {'company_address': orm.SuperLocalStructuredProperty('68', '7', required=True),
                           'party': orm.SuperKeyProperty('8', kind='6', required=True, indexed=False),  # @todo buyer_reference ??
                           'billing_address_reference': orm.SuperKeyProperty('9', kind='9', required=True, indexed=False),
                           'shipping_address_reference': orm.SuperKeyProperty('10', kind='9', required=True, indexed=False),
                           'billing_address': orm.SuperLocalStructuredProperty('68', '11', required=True),
                           'shipping_address': orm.SuperLocalStructuredProperty('68', '12', required=True),
                           'currency': orm.SuperLocalStructuredProperty('19', '13', required=True),
                           'untaxed_amount': orm.SuperDecimalProperty('14', required=True, indexed=False),
                           'tax_amount': orm.SuperDecimalProperty('15', required=True, indexed=False),
                           'total_amount': orm.SuperDecimalProperty('16', required=True, indexed=False),
                           'paypal_reciever_email': orm.SuperStringProperty('17', required=True, indexed=False),
                           'paypal_business': orm.SuperStringProperty('18', required=True, indexed=False)}
    entity.line_fields = {'description': orm.SuperTextProperty('6', required=True),
                          'product_reference': orm.SuperKeyProperty('7', kind='38', required=True, indexed=False),
                          'product_variant_signature': orm.SuperJsonProperty('8', required=True),
                          'product_category_complete_name': orm.SuperTextProperty('9', required=True),
                          'product_category_reference': orm.SuperKeyProperty('10', kind='17', required=True, indexed=False),
                          'code': orm.SuperStringProperty('11', required=True, indexed=False),
                          'unit_price': orm.SuperDecimalProperty('12', required=True, indexed=False),
                          'product_uom': orm.SuperLocalStructuredProperty('19', '13', required=True),
                          'quantity': orm.SuperDecimalProperty('14', required=True, indexed=False),
                          'discount': orm.SuperDecimalProperty('15', required=True, indexed=False),
                          'taxes': orm.SuperLocalStructuredProperty('116', '16', required=True),
                          'subtotal': orm.SuperDecimalProperty('17', required=True, indexed=False),
                          'discount_subtotal': orm.SuperDecimalProperty('18', required=True, indexed=False)}
    entity._use_rule_engine = False
    entity.write()
    entity._transaction_actions = [
      Action(
        key=Action.build_key('add_to_cart', parent=entity.key),
        name='Add to Cart',
        active=True,
        arguments={
          'domain': orm.SuperKeyProperty(kind='6', required=True),
          'product': orm.SuperKeyProperty(kind='38', required=True),
          'variant_signature': orm.SuperJsonProperty()
          }
        )
      # Other actions: update, checkout, cancel, pay, timeout, complete, message
      ]
    entity._transaction_plugin_groups = [
      PluginGroup(
        name='Entry Init',
        active=True,
        sequence=0,
        transactional=False,
        subscriptions=[
          Action.build_key('add_to_cart', parent=entity.key)
          ],
        plugins=[
          CartInit()
          ]
        ),
      PluginGroup(
        name='Payment Services Configuration',
        active=True,
        sequence=1,
        transactional=False,
        subscriptions=[
          Action.build_key('add_to_cart', parent=entity.key)
          ],
        plugins=[
          PayPalPayment(currency=Unit.build_key('usd'),
                        reciever_email='paypal_email@example.com',
                        business='paypal_email@example.com')
          ]
        ),
      PluginGroup(
        name='Entry Lines Init',
        active=True,
        sequence=2,
        transactional=False,
        subscriptions=[
          Action.build_key('add_to_cart', parent=entity.key)
          ],
        plugins=[
          LinesInit()
          ]
        ),
      PluginGroup(
        name='Address Exclusions, Taxes, Carriers...',
        active=True,
        sequence=3,
        transactional=False,
        subscriptions=[
          Action.build_key('add_to_cart', parent=entity.key)
          ],
        plugins=[
          ]
        ),
      PluginGroup(
        name='Calculating Algorithms',
        active=True,
        sequence=4,
        transactional=False,
        subscriptions=[
          Action.build_key('add_to_cart', parent=entity.key)
          ],
        plugins=[
          AddressRule(exclusion=False, address_type='billing'),  # @todo For now we setup default address rules for both, billing & shipping addresses.
          AddressRule(exclusion=False, address_type='shipping'),  # @todo For now we setup default address rules for both, billing & shipping addresses.
          ProductToLine(),
          ProductSubtotalCalculate(),
          TaxSubtotalCalculate(),
          OrderTotalCalculate()
          ]
        ),
      PluginGroup(
        name='Commit Transaction Plugins',
        active=True,
        sequence=5,
        transactional=True,
        subscriptions=[
          Action.build_key('add_to_cart', parent=entity.key)
          ],
        plugins=[
          RulePrepare(cfg={'path': '_group._entries'}),
          TransactionWrite(),
          CallbackNotify(),
          CallbackExec()
          ]
        ),
      ]
    entity.write({'agent': self.context.user.key, 'action': self.context.action.key})
    self.config.next_operation = 'complete'
    self.config.next_operation_input = {'domain_key': domain_key}
    self.config.write()
