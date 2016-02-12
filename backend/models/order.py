# -*- coding: utf-8 -*-
'''
Created on Aug 30, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime
import hashlib
import json

import orm
import settings
import notifications
from plugins.base import *
from models.buyer import *
from models.location import *
from models.unit import *
from plugins.order import *


__all__ = ['OrderNotifyTracker', 'OrderTax', 'OrderLine', 'OrderProduct', 'OrderCarrier', 'OrderMessage', 'Order']


class OrderNotifyTracker(orm.BaseModel):

  _kind = 136

  _use_rule_engine = False

  timeout = orm.SuperDateTimeProperty('1', required=True)
  buyer = orm.SuperBooleanProperty('2', default=False, indexed=False)
  seller = orm.SuperBooleanProperty('3', default=True, indexed=False)


class OrderTax(orm.BaseModel):

  _kind = 32

  _use_rule_engine = False

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  type = orm.SuperStringProperty('2', required=True, default='proportional', choices=('proportional', 'fixed'), indexed=False)
  amount = orm.SuperDecimalProperty('3', required=True, indexed=False)


class OrderProduct(orm.BaseExpando):

  _kind = 125

  _use_rule_engine = False

  reference = orm.SuperVirtualKeyProperty('1', kind='28', required=True, indexed=False)  # the reference now has catalog->image->pricetag->product key-path
  category = orm.SuperLocalStructuredProperty('24', '2', required=True)
  name = orm.SuperStringProperty('3', required=True, indexed=False)
  uom = orm.SuperLocalStructuredProperty('17', '4', required=True)
  code = orm.SuperStringProperty('5', required=True, indexed=False)
  unit_price = orm.SuperDecimalProperty('6', required=True, indexed=False)
  variant_signature = orm.SuperJsonProperty('7', required=True, default={}, indexed=False)
  quantity = orm.SuperDecimalProperty('8', required=True, indexed=False)

  _default_indexed = False

  _expando_fields = {
      'weight': orm.SuperDecimalProperty('9'),
      'volume': orm.SuperDecimalProperty('10')
  }

  _virtual_fields = {
      '_reference': orm.SuperComputedProperty(lambda self: self.get_reference_information() if self.reference else None)
  }

  def get_reference_information(self):
    key_structure = self.reference._structure
    key_flat = list(self.reference.parent().pairs())
    key_flat.pop(3)
    key_structure['pricetag'] = orm.Key(pairs=key_flat)._structure
    return key_structure

  @classmethod
  def get_partial_reference_key_path(cls, reference_key):
    product_key = list(reference_key.pairs())
    product_key.pop(3)
    return orm.Key(pairs=product_key)


class OrderCarrier(orm.BaseExpando):

  _kind = 123

  _use_rule_engine = False

  description = orm.SuperTextProperty('1', required=True)
  reference = orm.SuperVirtualKeyProperty('2', kind='113', required=True, indexed=False)
  unit_price = orm.SuperDecimalProperty('3', required=True, indexed=False)
  taxes = orm.SuperLocalStructuredProperty(OrderTax, '4', repeated=True)
  subtotal = orm.SuperDecimalProperty('5', required=True, indexed=False)
  tax_subtotal = orm.SuperDecimalProperty('6', required=True, indexed=False)
  total = orm.SuperDecimalProperty('7', required=True, indexed=False)

  _default_indexed = False


class OrderLine(orm.BaseExpando):

  _kind = 33

  _use_rule_engine = False

  sequence = orm.SuperIntegerProperty('1', required=True)
  product = orm.SuperLocalStructuredProperty(OrderProduct, '2', required=True)
  taxes = orm.SuperLocalStructuredProperty(OrderTax, '3', repeated=True)
  discount = orm.SuperDecimalProperty('4', required=True, indexed=False)
  subtotal = orm.SuperDecimalProperty('5', required=True, indexed=False)
  discount_subtotal = orm.SuperDecimalProperty('6', required=True, indexed=False)
  tax_subtotal = orm.SuperDecimalProperty('7', required=True, indexed=False)
  total = orm.SuperDecimalProperty('8', required=True, indexed=False)

  _default_indexed = False

  @classmethod
  def prepare_key(cls, input, **kwargs):
    parent = kwargs.get('parent')
    product = input.get('product')
    reference = product.get('reference')
    reference_key_path = OrderProduct.get_partial_reference_key_path(reference)
    return cls.build_key(hashlib.md5('%s-%s' % (reference_key_path.urlsafe(), json.dumps(product.get('variant_signature')))).hexdigest(), parent=parent)

  def prepare(self, **kwargs):
    parent = kwargs.get('parent')
    product = self.product.value
    self.key = self.prepare_key({'product': {'reference': product.reference, 'variant_signature': product.variant_signature}}, parent=parent)


class OrderMessage(orm.BaseExpando):

  _kind = 35

  _use_rule_engine = False

  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  agent = orm.SuperKeyProperty('2', kind='11', required=True, indexed=False)
  action = orm.SuperKeyProperty('3', kind='1', required=True)
  body = orm.SuperTextProperty('4', required=True)

  _default_indexed = True

  _virtual_fields = {
      '_agent': orm.SuperReferenceStructuredProperty('11', callback=lambda self: self.agent.get_async(),
                                                     format_callback=lambda self, value: value),
      '_action': orm.SuperComputedProperty(lambda self: self.action.id() if self.action else '')
  }


class Order(orm.BaseExpando):

  _kind = 34


  '''
  read:
    read_<order.account.id>
  search:
    search_34_<order.account.id>
  '''

  DELETE_CACHE_POLICY = {'group': [lambda context: 'read_34_%s' % context._order.key._root._id_str,
                                   'search_34_admin',
                                   'search_34',
                                   lambda context: 'search_34_seller_%s' % context._order.seller_reference._root._id_str,
                                   lambda context: 'search_34_buyer_%s' % context._order.key._root._id_str
                                   ]}

  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  state = orm.SuperStringProperty('3', required=True, default='cart', choices=('cart', 'order')) # 'checkout', 'completed', 'canceled'
  date = orm.SuperDateTimeProperty('4', required=True)
  seller_reference = orm.SuperKeyProperty('5', kind='23', required=True)
  billing_address = orm.SuperLocalStructuredProperty('121', '6')
  shipping_address = orm.SuperLocalStructuredProperty('121', '7')
  currency = orm.SuperLocalStructuredProperty('17', '8', required=True)
  untaxed_amount = orm.SuperDecimalProperty('9', required=True, indexed=False)
  tax_amount = orm.SuperDecimalProperty('10', required=True, indexed=False)
  total_amount = orm.SuperDecimalProperty('11', required=True, indexed=False)
  payment_method = orm.SuperStringProperty('12', required=False, choices=settings.AVAILABLE_PAYMENT_METHODS)
  payment_status = orm.SuperStringProperty('13', required=False, indexed=True)
  carrier = orm.SuperLocalStructuredProperty(OrderCarrier, '14')

  _default_indexed = False

  _virtual_fields = {
      '_seller': orm.SuperReferenceStructuredProperty('23', autoload=True, target_field='seller_reference'),
      '_lines': orm.SuperRemoteStructuredProperty(OrderLine, repeated=True, search={
          'default': {
              'filters': [],
              'orders': [{
                  'field': 'sequence',
                  'operator': 'asc'
              }]
          },
          'cfg': {
              'indexes': [{
                  'ancestor': True,
                  'filters': [],
                  'orders': [('sequence', ['asc'])]
              }],
          }
      }),
      '_messages': orm.SuperRemoteStructuredProperty(OrderMessage, repeated=True,
                                                     search={
                                                         'default': {
                                                             'filters': [],
                                                             'orders': [{
                                                                 'field': 'created',
                                                                 'operator': 'desc'
                                                             }]
                                                         },
                                                         'cfg': {
                                                             'indexes': [{
                                                                 'ancestor': True,
                                                                 'filters': [],
                                                                 'orders': [('created', ['desc'])]
                                                             }],
                                                         }
                                                     }),
      '_seller_reference': orm.SuperComputedProperty(lambda self: self.seller_reference._structure if self.seller_reference else None),
  }

  def condition_taskqueue(account, **kwargs):
    return account._is_taskqueue
  
  def condition_cron(account, **kwargs):
    return account._is_cron

  def condition_not_guest_and_owner_and_cart(account, entity, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key \
        and entity._original.state == "cart"

  def condition_root_or_owner_or_seller(account, entity, **kwargs):
    if entity._original.seller_reference is None:
      return False
    return account._root_admin or (not account._is_guest and ((entity._original.key_root == account.key)
                                                              or (entity._original.seller_reference._root == account.key)))

  def condition_search(account, action, entity, input, **kwargs):
    return action.key_id_str == "search" and (account._root_admin
                                              or ((not account._is_guest and input["search"]["filters"][0]["field"] == "seller_reference"
                                                   and input["search"]["filters"][0]["value"]._root == account.key)
                                                  or (not account._is_guest and "ancestor" in input["search"] and input["search"]["ancestor"]._root == account.key)))

  def condition_pay(action, entity, **kwargs):
    return action.key_id_str == "pay" and entity._original.state == "cart"
  
  def condition_notify(action, entity, **kwargs):
    return action.key_id_str == "notify" and entity._original.state == "order"

  def condition_update_line(account, entity, action, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key \
        and entity._original.state == "cart" and action.key_id_str == "update_line"

  def condition_state(action, entity, **kwargs):
    return (action.key_id_str == "update_line" and entity.state == "cart") \
        or (action.key_id_str == "pay" and entity.state == "order")

  def condition_update_and_view_order(account, entity, action, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key \
        and entity._original.state == "cart" and action.key_id_str in ("view_order", "update")

  def cache_group_search(context):
    key = 'search_34'
    _ancestor = context.input['search'].get('ancestor')
    filters = context.input['search'].get('filters')
    if context.account._root_admin:
      return '%s_admin' % key
    if filters and filters[0]['field'] == 'seller_reference' and filters[0]['value']._root == context.account.key:
      return '%s_seller_%s' % (key, context.account.key_id_str)
    if _ancestor and _ancestor._root == context.account.key:
      return '%s_buyer_%s' % (key, context.account.key_id_str)
    return key

  _permissions = [
      #  action.key_id_str not in ["search"] and...
      # Included payment_status in field permissions, will have to further analyse exclusion...
      orm.ExecuteActionPermission(('update_line', 'view_order', 'update', 'delete', 'pay'), condition_not_guest_and_owner_and_cart),
      orm.ExecuteActionPermission(('read', 'log_message'), condition_root_or_owner_or_seller),
      orm.ExecuteActionPermission('search', condition_search),
      orm.ExecuteActionPermission('delete', condition_taskqueue),
      orm.ExecuteActionPermission(('cron', 'cron_notify'), condition_cron),
      orm.ExecuteActionPermission('see_messages', condition_root_or_owner_or_seller),
      orm.ExecuteActionPermission('notify', condition_notify),

      orm.ReadFieldPermission(('created', 'updated', 'state', 'date', 'seller_reference',
                               'billing_address', 'shipping_address', 'currency', 'untaxed_amount',
                               'tax_amount', 'total_amount', 'carrier', '_seller_reference',
                               'payment_status', 'payment_method',
                               '_lines', '_messages.created', '_messages.agent', '_messages.action', '_messages.body',
                               '_messages._action', '_seller.name',
                               '_seller.logo',
                               '_seller._stripe_publishable_key',
                               '_seller._currency'), condition_root_or_owner_or_seller),
      orm.WriteFieldPermission(('date', 'seller_reference',
                                'currency', 'untaxed_amount', 'tax_amount', 'total_amount',
                                'payment_method', '_lines', 'carrier'), condition_update_line),
      orm.WriteFieldPermission('state', condition_state),
      orm.WriteFieldPermission(('payment_status', '_messages'), condition_pay),
      orm.WriteFieldPermission(('payment_status', '_messages'), condition_notify),
      orm.WriteFieldPermission('_messages', condition_root_or_owner_or_seller),
      orm.WriteFieldPermission(('date', 'shipping_address', 'billing_address', '_lines', 'carrier',
                                'untaxed_amount', 'tax_amount', 'total_amount', 'payment_method'), condition_update_and_view_order),
      orm.DenyWriteFieldPermission(('_lines.taxes', '_lines.product.reference',
                                    '_lines.product.category', '_lines.product.name', '_lines.product.uom',
                                    '_lines.product.code', '_lines.product.unit_price', '_lines.product.variant_signature',
                                    '_lines.product.weight', '_lines.product.volume'), condition_update_and_view_order)
  ]

  _actions = [
      orm.Action(
          id='update_line',
          arguments={
              'buyer': orm.SuperKeyProperty(kind='19', required=True),
              'quantity': orm.SuperDecimalProperty(required=True),
              'product': orm.SuperKeyProperty(kind='28', required=True),
              'image': orm.SuperKeyProperty(kind='30', required=True),
              'variant_signature': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      OrderInit(),
                      OrderPluginExec(cfg={'kinds': ['117']}),
                      OrderProductSpecsFormat(),
                      OrderUpdateLine(),
                      OrderLineRemove(),
                      OrderStockManagement(),
                      OrderLineFormat(),
                      OrderCarrierFormat(),
                      OrderFormat(),
                      RulePrepare(),
                      RuleExec()
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      Write(),
                      DeleteCache(cfg=DELETE_CACHE_POLICY),
                      Set(cfg={'d': {'output.entity': '_order'}})
                  ]
              )
          ]
      ),
      orm.Action(
          id='view_order',
          arguments={
              'buyer': orm.SuperKeyProperty(kind='19', required=True),
              'seller': orm.SuperKeyProperty(kind='23', required=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      GetCache(cfg={'group': lambda context: 'read_34_%s' % context.input['buyer']._root._id_str, 'cache': ['account']}),
                      OrderInit(),
                      OrderPluginExec(cfg={'kinds': ['117']}),  # order currency must be available for everyone
                      OrderProductSpecsFormat(),
                      RulePrepare(),
                      RuleExec(),
                      Set(cfg={'d': {'output.entity': '_order'}}),
                      CallbackExec()
                  ]
              )
          ]
      ),
      orm.Action(
          id='read',
          arguments={
              'key': orm.SuperKeyProperty(kind='34', required=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      GetCache(cfg={'group': lambda context: 'read_34_%s' % context.input['key']._root._id_str, 'cache': ['account']}),
                      Read(),
                      RulePrepare(),
                      RuleExec(),
                      Set(cfg={'d': {'output.entity': '_order'}}),
                      CallbackExec()
                  ]
              )
          ]
      ),
      orm.Action(
          id='update',
          arguments={
              'key': orm.SuperKeyProperty(kind='34', required=True),
              'billing_address': orm.SuperLocalStructuredProperty('14'),
              'shipping_address': orm.SuperLocalStructuredProperty('14'),
              'carrier': orm.SuperVirtualKeyProperty(kind='113'),
              '_lines': orm.SuperLocalStructuredProperty(OrderLine, repeated=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(cfg={'read': {'_lines': {'config': {'search': {'options': {'limit': 0}}}}}}),
                      Set(cfg={'d': {'_order._lines': 'input._lines'}}),
                      OrderLineRemove(),
                      OrderStockManagement(),
                      OrderProductSpecsFormat(),
                      OrderFormat(),  # Needed for Carrier. Alternative is to break down this plugin in two, pre-carrier & post-carrier one.
                      OrderPluginExec(),
                      OrderLineFormat(),
                      OrderCarrierFormat(),
                      OrderFormat(),
                      RulePrepare(),
                      RuleExec()
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      Write(),
                      RulePrepare(),
                      DeleteCache(cfg=DELETE_CACHE_POLICY),
                      Set(cfg={'d': {'output.entity': '_order'}})
                  ]
              )
          ]
      ),
      orm.Action(
          id='delete',
          arguments={
              'key': orm.SuperKeyProperty(kind='34', required=True)
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
                      DeleteCache(cfg=DELETE_CACHE_POLICY),
                      RulePrepare(),
                      Set(cfg={'d': {'output.entity': '_order'}})
                  ]
              )
          ]
      ),
      orm.Action(
          id='search',
          arguments={
              'search': orm.SuperSearchProperty(
                  default={'filters': [], 'orders': [{'field': 'updated', 'operator': 'desc'}]},
                  cfg={
                      'search_arguments': {'kind': '34', 'options': {'limit': settings.SEARCH_PAGE}},
                      'ancestor_kind': '19',
                      'search_by_keys': True,
                      'filters': {'name': orm.SuperStringProperty(),
                                  'key': orm.SuperVirtualKeyProperty(kind='34', searchable=False),
                                  'state': orm.SuperStringProperty(repeated=True, choices=('cart', 'order')),
                                  'seller_reference': orm.SuperKeyProperty(kind='23', searchable=False)},
                      'indexes': [{'orders': [('updated', ['asc', 'desc'])]},
                                  {'orders': [('created', ['asc', 'desc'])]},
                                  {'filters': [('key', ['=='])]},
                                  {'filters': [('state', ['IN'])], 'orders': [('updated', ['asc', 'desc'])]},
                                  {'ancestor': True, 'filters': [('state', ['IN'])], 'orders': [('updated', ['desc'])]},
                                  {'filters': [('seller_reference', ['=='])], 'orders': [('updated', ['desc'])]}]
                  }
              )
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      GetCache(cfg={'group': cache_group_search, 'cache': ['account']}),
                      Read(),
                      RulePrepare(),
                      RuleExec(),
                      Search(),
                      RulePrepare(cfg={'path': '_entities'}),
                      Set(cfg={'d': {'output.entities': '_entities',
                                     'output.cursor': '_cursor',
                                     'output.more': '_more'}}),
                      CallbackExec()
                  ]
              )
          ]
      ),
      orm.Action(
          id='cron',
          arguments={},
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      RulePrepare(),
                      RuleExec(),
                      OrderCronDelete(cfg={'page': 100,
                                           'cart_life': settings.ORDER_CART_LIFE,
                                           'unpaid_order_life': settings.ORDER_UNPAID_LIFE}),
                      CallbackExec()
                  ]
              )
          ]
      ),
      orm.Action(
          id='notify',
          skip_csrf=True,
          arguments={
              'payment_method': orm.SuperStringProperty(required=True, choices=settings.AVAILABLE_PAYMENT_METHODS),
              'request': orm.SuperPickleProperty(),
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      OrderNotify(cfg={'options': {'paypal': {'webscr': settings.PAYPAL_WEBSCR}}}),
                      OrderSetMessage(cfg={
                        'expando_fields': 'new_message_fields',
                        'expando_values': 'new_message'
                      }),
                      RulePrepare(),
                      RuleExec()
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      Write(),
                      RulePrepare(),
                      Set(cfg={'d': {'output.entity': '_order'}}),
                      # both seller and buyer must get the message
                      Notify(cfg={'s': {'sender': settings.NOTIFY_EMAIL,
                                        'for_seller': False,
                                        'subject': notifications.ORDER_NOTIFY_SUBJECT,
                                        'body': notifications.ORDER_NOTIFY_BODY},
                                  'd': {'recipient': '_order.buyer_email'}}),
                      Notify(cfg={'s': {'sender': settings.NOTIFY_EMAIL,
                                        'for_seller': True,
                                        'subject': notifications.ORDER_NOTIFY_SUBJECT,
                                        'body': notifications.ORDER_NOTIFY_BODY},
                                  'd': {'recipient': '_order.seller_email'}}),
                      DeleteCache(cfg=DELETE_CACHE_POLICY)
                  ]
              )
          ]
      ),
      orm.Action(
          id='pay',
          arguments={
              'key': orm.SuperKeyProperty(kind='34', required=True),
              'token': orm.SuperStringProperty(required=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(cfg={'read': {'_lines': {'config': {'search': {'options': {'limit': 0}}}}}})
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      # Transaction failures can still cause payment charges to succeed.
                      # Isolate as little plugins as possible in transaction to minimize transaction failures.
                      # We can also implement a two step payment to make the payment more robust.
                      OrderPay(),
                      OrderSetMessage(cfg={
                        'expando_fields': 'new_message_fields',
                        'expando_values': 'new_message'
                      }),
                      RulePrepare(),
                      RuleExec(),
                      Write(),
                      RulePrepare(),
                      DeleteCache(cfg=DELETE_CACHE_POLICY),
                      Set(cfg={'d': {'output.entity': '_order'}})
                  ]
              ),
              orm.PluginGroup(
                  plugins=[
                      # both seller and buyer must get the message
                      Notify(cfg={'s': {'sender': settings.NOTIFY_EMAIL,
                                        'for_seller': False,
                                        'subject': notifications.ORDER_NOTIFY_SUBJECT,
                                        'body': notifications.ORDER_NOTIFY_BODY},
                                  'd': {'recipient': '_order.buyer_email'}}),
                      Notify(cfg={'s': {'sender': settings.NOTIFY_EMAIL,
                                        'for_seller': True,
                                        'subject': notifications.ORDER_NOTIFY_SUBJECT,
                                        'body': notifications.ORDER_NOTIFY_BODY},
                                  'd': {'recipient': '_order.seller_email'}})
                  ]
              )
          ]
      ),
      orm.Action(
          id='see_messages',
          arguments={
            'key': orm.SuperKeyProperty(kind='34', required=True)
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
                      OrderNotifyTrackerSeen()
                  ]
              )
          ]
      ),
      orm.Action(
          id='log_message',
          arguments={
              'key': orm.SuperKeyProperty(kind='34', required=True),
              'message': orm.SuperTextProperty(required=True, max_size=settings.MAX_MESSAGE_SIZE)
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      OrderSetMessage(),
                      RulePrepare(),
                      RuleExec()
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      Write(),
                      Set(cfg={'d': {'output.entity': '_order'}}),
                      OrderNotifyTrackerSet(cfg=settings.ORDER_CRON_NOTIFY_TIMER),
                      DeleteCache(cfg=DELETE_CACHE_POLICY)
                  ]
              )
          ]
      ),
      orm.Action(
          id='cron_notify',
          arguments={},
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
                  transactional=False,
                  plugins=[
                      # This plugin isolates its parts in transaction, so the group is wrapped in transaction.
                      OrderCronNotify(cfg={'s': {'sender': settings.NOTIFY_EMAIL,
                                                 'subject': notifications.ORDER_LOG_MESSAGE_SUBJECT,
                                                 'body': notifications.ORDER_LOG_MESSAGE_BODY},
                                           'hours': settings.ORDER_CRON_NOTIFY_TIMER['hours'],
                                           'minutes': settings.ORDER_CRON_NOTIFY_TIMER['minutes'],
                                           'seconds': settings.ORDER_CRON_NOTIFY_TIMER['seconds']}),

                      CallbackExec()
                  ]
              )
          ]
      )
  ]

  @property
  def buyer_email(self):
    account = self.root_entity
    account.read()
    return account._primary_email

  @property
  def seller_email(self):
    account = self.seller_reference._root.entity
    account.read()
    return account._primary_email

  @property
  def seller_and_buyer_emails(self):
    emails = []
    emails.append(self.seller_email)
    emails.append(self.buyer_email)
    return emails
