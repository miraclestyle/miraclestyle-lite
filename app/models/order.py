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
  name = orm.SuperStringProperty('3', required=True)
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
    # Other actions: add_to_cart, update, checkout, cancel, pay, timeout, complete, message
    orm.Action(
      key=orm.Action.build_key('34', 'add_to_cart'),
      arguments={
        'seller': orm.SuperKeyProperty(kind='23', required=True),
        'product': orm.SuperKeyProperty(kind='28', required=True),
        'variant_signature': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            CartInit(),
            PluginAgregator(),
            Read(),
            Set(cfg={'d': {'_collection.notify': 'input.notify', '_collection.accounts': 'input.accounts'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_collection'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('18', 'read'),
      arguments={
        'account': orm.SuperKeyProperty(kind='11', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_collection'}})
            ]
          )
        ]
      )
    ]


# from setup.py #

    
    entity._use_rule_engine = False
    entity.write()
    entity._transaction_actions = [
      Action(
        key=Action.build_key('add_to_cart', parent=entity.key),
        name='Add to Cart',
        active=True,
        arguments={
          'seller': orm.SuperKeyProperty(kind='6', required=True),
          'product': orm.SuperKeyProperty(kind='38', required=True),
          'variant_signature': orm.SuperJsonProperty()
          }
        )
      # Other actions: add_to_cart, update, checkout, cancel, pay, timeout, complete, message
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
