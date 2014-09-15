# -*- coding: utf-8 -*-
'''
Created on Aug 30, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models import *
from app.plugins import *


class OrderLineTax(orm.BaseModel):
  
  _kind = 32
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  code = orm.SuperStringProperty('2', required=True, indexed=False)
  formula = orm.SuperPickleProperty('3', required=True, indexed=False)


class OrderLine(orm.BaseExpando):
  
  _kind = 33
  
  _use_rule_engine = False
  
  sequence = orm.SuperIntegerProperty('1', required=True)
  description = orm.SuperTextProperty('2', required=True)
  product_reference = orm.SuperKeyProperty('3', kind='28', required=True, indexed=False)
  product_variant_signature = orm.SuperJsonProperty('4', required=True)
  product_category_complete_name = orm.SuperTextProperty('5', required=True)
  product_category_reference = orm.SuperKeyProperty('6', kind='24', required=True, indexed=False)
  code = orm.SuperStringProperty('7', required=True, indexed=False)
  unit_price = orm.SuperDecimalProperty('8', required=True, indexed=False)
  product_uom = orm.SuperLocalStructuredProperty(UOM, '9', required=True)  # @todo Or Unit (or _kind, 16 stands for UOM model, 17 for Unit)!?
  quantity = orm.SuperDecimalProperty('10', required=True, indexed=False)
  discount = orm.SuperDecimalProperty('11', required=True, indexed=False)
  taxes = orm.SuperLocalStructuredProperty(OrderLineTax, '12', repeated=True)
  subtotal = orm.SuperDecimalProperty('13', required=True, indexed=False)
  discount_subtotal = orm.SuperDecimalProperty('14', required=True, indexed=False)
  total = orm.SuperDecimalProperty('15', required=True, indexed=False)
  
  _default_indexed = False


class Order(orm.BaseExpando):
  
  _kind = 34
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = orm.SuperStringProperty('3', required=True)  # @todo Not sure if we need this, or how to use it to construct some unique order name?
  state = orm.SuperStringProperty('4', required=True, default='cart', choices=['cart', 'checkout', 'processing', 'completed', 'canceled'])
  date = orm.SuperDateTimeProperty('5', required=True)
  seller_reference = orm.SuperKeyProperty('6', kind='23', required=True)
  seller_address = orm.SuperLocalStructuredProperty(Address, '7', required=True)
  billing_address_reference = orm.SuperKeyProperty('8', kind='14', required=True, indexed=False)
  shipping_address_reference = orm.SuperKeyProperty('9', kind='14', required=True, indexed=False)
  billing_address = orm.SuperLocalStructuredProperty(Address, '10', required=True)
  shipping_address = orm.SuperLocalStructuredProperty(Address, '11', required=True)
  currency = orm.SuperLocalStructuredProperty(UOM, '12', required=True)  # @todo Or Unit (or _kind, 16 stands for UOM model, 17 for Unit)!?
  untaxed_amount = orm.SuperDecimalProperty('13', required=True, indexed=False)
  tax_amount = orm.SuperDecimalProperty('14', required=True, indexed=False)
  total_amount = orm.SuperDecimalProperty('15', required=True, indexed=False)
  paypal_reciever_email = orm.SuperStringProperty('16', required=True, indexed=False)
  paypal_business = orm.SuperStringProperty('17', required=True, indexed=False)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_lines': orm.SuperRemoteStructuredProperty(OrderLine, repeated=True),
    '_records': orm.SuperRecordProperty('34')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('34', [orm.Action.build_key('34', 'update'),
                                  orm.Action.build_key('34', 'read')], True,
                           'not account._is_guest and entity._original.key_root == account.key'),
      orm.FieldPermission('34', ['notify', 'sellers', '_records', '_sellers.name', '_sellers.logo'], True, True,
                          'not account._is_guest and entity._original.key_root == account.key')
      ]
    )
  
  _actions = [
    # @todo Two of the search actions should be merged if possible! However, they have different forced contrains!
    # buyer_search has to be constrained buy ancestor query, ancestor being buyer.
    # seller_search has to be constrained by query filter, with filter Order.seller_reference being seller.
    orm.Action(
      key=orm.Action.build_key('34', 'add_to_cart'),
      arguments={
        'buyer': orm.SuperKeyProperty(kind='19', required=True),
        'seller': orm.SuperKeyProperty(kind='23', required=True),
        'product': orm.SuperKeyProperty(kind='28', required=True),
        'variant_signature': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            OrderInit(),
            PayPalPayment(currency=Unit.build_key('usd'), reciever_email='', business=''), # @todo For now we setup default currency for the order.
            AddressRule(exclusion=False, address_type='billing'),  # @todo For now we setup default address rules for both, billing & shipping addresses.
            AddressRule(exclusion=False, address_type='shipping'),  # @todo For now we setup default address rules for both, billing & shipping addresses.
            ProductToOrderLine(),
            PluginExec(),  # ('Payment Services, Address Exclusions, Taxes, Carriers...'),
            OrderLineFormat(),
            OrderFormat(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      )
    orm.Action(
      # @todo This action was derived from read. It uses buyer and seller keys as input, instead of key to perform entity read.
      # @todo We need this action in order for buyer to see order from catalog view! Perhaps to figure out other appropriate name??
      key=orm.Action.build_key('34', 'view_order'),
      arguments={
        'buyer': orm.SuperKeyProperty(kind='19', required=True),
        'seller': orm.SuperKeyProperty(kind='23', required=True),
        'read_arguments': orm.SuperJsonProperty()  # @todo This action has to be evaluated!
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            OrderInit(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True),
        'billing_address_reference': orm.SuperKeyProperty(kind='14'),
        'shipping_address_reference': orm.SuperKeyProperty(kind='14'),
        '_lines': orm.SuperLocalStructuredProperty(OrderLine, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_order.billing_address_reference': 'input.billing_address_reference',
                           '_order.shipping_address_reference': 'input.shipping_address_reference',
                           '_order._lines': 'input._lines'}}),
            PayPalPayment(currency=Unit.build_key('usd'), reciever_email='', business=''), # @todo For now we setup default currency for the order.
            AddressRule(exclusion=False, address_type='billing'),  # @todo For now we setup default address rules for both, billing & shipping addresses.
            AddressRule(exclusion=False, address_type='shipping'),  # @todo For now we setup default address rules for both, billing & shipping addresses.
            PluginExec(),  # PluginAgregator('Payment Services, Address Exclusions, Taxes, Carriers...'),
            OrderLineFormat(),
            OrderFormat(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'buyer_search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'orders': [{'field': 'created', 'operator': 'asc'}]},
          cfg={
            'ancestor_kind': '11',
            'search_by_keys': True,
            'filters': {'name': orm.SuperStringProperty(),
                        'state': orm.SuperStringProperty(choices=['invited', 'accepted'])},
            'indexes': [{'orders': [('name', ['asc', 'desc'])]},
                        {'orders': [('created', ['asc', 'desc'])]},
                        {'orders': [('updated', ['asc', 'desc'])]},
                        {'filters': [('name', ['==', 'contains', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!=']), ('name', ['==', 'contains', '!='])],
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
            Search(cfg={'s': {'kind': '34', 'options': {'limit': settings.SEARCH_PAGE}},
                        'd': {'ancestor': 'account.key'}}),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'seller_search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'orders': [{'field': 'created', 'operator': 'asc'}]},
          cfg={
            'ancestor_kind': '11',
            'search_by_keys': True,
            'filters': {'name': orm.SuperStringProperty(),
                        'state': orm.SuperStringProperty(choices=['invited', 'accepted'])},
            'indexes': [{'orders': [('name', ['asc', 'desc'])]},
                        {'orders': [('created', ['asc', 'desc'])]},
                        {'orders': [('updated', ['asc', 'desc'])]},
                        {'filters': [('name', ['==', 'contains', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!=']), ('name', ['==', 'contains', '!='])],
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
            Search(cfg={'s': {'kind': '34', 'options': {'limit': settings.SEARCH_PAGE}},
                        'd': {'ancestor': 'account.key'}}),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'checkout'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_order.state': 'checkout'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'cancel'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_order.state': 'canceled'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'pay'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_order.state': 'processing'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'timeout'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_order.state': 'checkout'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'complete'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_order.state': 'completed'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'log_message'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True),
        'message': orm.SuperTextProperty(required=True),
        'note': orm.SuperTextProperty()
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
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      )
    ]


# from setup.py #
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
