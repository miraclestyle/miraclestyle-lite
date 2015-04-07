# -*- coding: utf-8 -*-
'''
Created on Aug 30, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import datetime
import hashlib
import orm
import settings
import notifications

from models.base import *
from plugins.base import *

from models.buyer import *
from models.location import *
from models.unit import *
from plugins.order import *



__all__ = ['OrderTax', 'OrderLine', 'OrderProduct', 'OrderCarrier', 'OrderMessage', 'Order']


class OrderTax(orm.BaseModel):
  
  _kind = 32
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  type = orm.SuperStringProperty('2', required=True, default='percent', choices=('percent', 'fixed'), indexed=False)
  amount = orm.SuperDecimalProperty('3', required=True, indexed=False)


class OrderProduct(orm.BaseExpando):

  _kind = 125
  
  _use_rule_engine = False
  
  reference = orm.SuperVirtualKeyProperty('1', kind='28', required=True, indexed=False) # the reference now has catalog->image->pricetag->product key-path
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
    'weight_uom': orm.SuperLocalStructuredProperty('17', '10'),
    'volume': orm.SuperDecimalProperty('11'),
    'volume_uom': orm.SuperLocalStructuredProperty('17', '12')
    }
  
  _virtual_fields = {
    '_reference': orm.SuperComputedProperty(lambda self: self.get_reference_information() if self.reference else None)
    }

  def get_reference_information(self):
    dic = self.reference.structure()
    flat = list(self.reference.parent().pairs())
    flat.pop(3)
    dic['pricetag'] = orm.Key(pairs=flat).structure()
    return dic
  
  @classmethod
  def get_partial_reference_key_path(cls, reference_key):
    real_product_key = list(reference_key.pairs())
    real_product_key.pop(3)
    real_product_key = orm.Key(pairs=real_product_key)
    return real_product_key


class OrderCarrier(orm.BaseExpando):
  
  _kind = 123
  
  _use_rule_engine = False
  
  description = orm.SuperTextProperty('1', required=True)
  reference = orm.SuperVirtualKeyProperty('2', kind='113', required=True, indexed=False)
  unit_price = orm.SuperDecimalProperty('3', required=True, indexed=False)
  taxes = orm.SuperLocalStructuredProperty(OrderTax, '4', repeated=True)
  subtotal = orm.SuperDecimalProperty('5', required=True, indexed=False)
  total = orm.SuperDecimalProperty('6', required=True, indexed=False)
  tax_subtotal = orm.SuperDecimalProperty('7', required=True, indexed=False)
  
  _default_indexed = False


class OrderLine(orm.BaseExpando):
  
  _kind = 33
  
  _use_rule_engine = False
  
  sequence = orm.SuperIntegerProperty('1', required=True)
  product = orm.SuperLocalStructuredProperty(OrderProduct, '2', required=True)
  taxes = orm.SuperLocalStructuredProperty(OrderTax, '4', repeated=True)
  discount = orm.SuperDecimalProperty('5', required=True, indexed=False)
  subtotal = orm.SuperDecimalProperty('6', required=True, indexed=False)
  discount_subtotal = orm.SuperDecimalProperty('7', required=True, indexed=False)
  tax_subtotal = orm.SuperDecimalProperty('8', required=True, indexed=False)
  total = orm.SuperDecimalProperty('9', required=True, indexed=False)
  
  _default_indexed = False
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    parent = kwargs.get('parent')
    product = input.get('product')
    reference = product.get('reference')
    rebuilt_reference = OrderProduct.get_partial_reference_key_path(reference)
    return cls.build_key(hashlib.md5('%s-%s' % (rebuilt_reference.urlsafe(), json.dumps(product.get('variant_signature')))).hexdigest(), parent=parent)
  
  def prepare(self, **kwargs):
    parent = kwargs.get('parent')
    product = self.product.value
    product_key = self.prepare_key({'product': {'reference': product.reference, 'variant_signature': product.variant_signature}}, parent=parent)
    self.key = product_key


class OrderMessage(orm.BaseExpando):
  
  _kind = 35

  _use_rule_engine = False
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  agent = orm.SuperKeyProperty('2', kind='11', required=True, indexed=False)
  action = orm.SuperKeyProperty('3', kind='1', required=True)
  body = orm.SuperTextProperty('4', required=True, indexed=False)
  
  _default_indexed = True
  
  _virtual_fields = {
    '_agent': orm.SuperReferenceStructuredProperty('11', callback=lambda self: self._retrieve_agent(),
                                     format_callback=lambda self, value: self._retrieve_agent_details(value)),
    '_action': orm.SuperComputedProperty(lambda self: self.action.id() if self.action else '')
    }

  def _retrieve_agent(self):
    return self.agent.get_async()

  def _retrieve_agent_details(self, entity):
    return entity


class Order(orm.BaseExpando):
  
  _kind = 34

  # key path account->buyer->order
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  state = orm.SuperStringProperty('3', required=True, default='cart', choices=('cart', 'checkout', 'completed', 'canceled'))
  date = orm.SuperDateTimeProperty('4', required=True)
  seller_reference = orm.SuperKeyProperty('5', kind='23', required=True)
  billing_address = orm.SuperLocalStructuredProperty('121', '6', required=True)
  shipping_address = orm.SuperLocalStructuredProperty('121', '7', required=True)
  currency = orm.SuperLocalStructuredProperty('17', '8', required=True)
  untaxed_amount = orm.SuperDecimalProperty('9', required=True, indexed=False)
  tax_amount = orm.SuperDecimalProperty('10', required=True, indexed=False)
  total_amount = orm.SuperDecimalProperty('11', required=True, indexed=False)
  feedback = orm.SuperStringProperty('12', choices=('positive', 'neutral', 'negative'))
  feedback_adjustment = orm.SuperStringProperty('13', choices=('revision', 'reported', 'sudo'))
  payment_method = orm.SuperKeyProperty('14', required=False, indexed=False)
  payment_status = orm.SuperStringProperty('15', required=False, indexed=False)
  carrier = orm.SuperLocalStructuredProperty(OrderCarrier, '16')
  
  _default_indexed = False
  
  _virtual_fields = {
    '_seller': orm.SuperReferenceStructuredProperty('23', target_field='seller_reference', autoload=True),
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
    '_messages': orm.SuperRemoteStructuredProperty(OrderMessage, repeated=True, deleteable=False,
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
    '_records': orm.SuperRecordProperty('34'),
    '_payment_method': orm.SuperReferenceProperty(callback=lambda self: self._get_payment_method(),
                                                  format_callback=lambda self, value: value),
    '_seller_reference': orm.SuperComputedProperty(lambda self: self.seller_reference.structure() if self.seller_reference else None),
  }
  
  _global_role = GlobalRole(
    permissions=[
      #  action.key_id_str not in ["search"] and...
      # Included payment_status in field permissions, will have to further analyse exclusion...
      orm.ActionPermission('34', [orm.Action.build_key('34', 'update_line')], True,
                           'not account._is_guest and entity._original.key_root == account.key \
                           and entity._original.state == "cart"'),  # Product To Line plugin handles state as well, so not sure if state validation is required!?
      orm.ActionPermission('34', [orm.Action.build_key('34', 'view_order')], True,
                           'not account._is_guest and entity._original.key_root == account.key'),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'read')], True,
                           'account._root_admin or (not account._is_guest and ((entity._original.key_root == account.key) \
                           or (entity._original.seller_reference and entity._original.seller_reference._root == account.key)))'),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'update')], True,
                           'not account._is_guest and (entity._original.key_root == account.key \
                           and entity._original.state == "cart")'),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'search')], True,
                           'action.key_id_str == "search" and (account._root_admin \
                            or ((not account._is_guest and input["search"]["filters"][0]["field"] == "seller_reference" \
                                and input["search"]["filters"][0]["value"]._root == account.key) \
                                or (not account._is_guest and "ancestor" in input["search"] and input["search"]["ancestor"]._root == account.key)))'),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'checkout')], True,
                           'not account._is_guest and entity._original.key_root == account.key \
                           and entity._original.state == "cart"'),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'log_message')], True,
                           '(account._root_admin or (not account._is_guest and ((entity._original.key_root == account.key) \
                           or (entity._original.seller_reference \
                           and entity._original.seller_reference._root == account.key)))) \
                           and entity._original.state == "checkout"'),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'cancel')], True,
                           'not account._is_guest and entity._original.key_root == account.key \
                           and entity._original.state == "checkout"'),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'complete')], True,
                           'account._is_taskqueue and entity._original.state == "checkout"'),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'leave_feedback')], True,
                           'not account._is_guest and entity._original.key_root == account.key \
                           and entity._original.state == "completed" and entity._is_feedback_allowed \
                           and (entity._original.feedback is None or (entity._original.feedback is not None \
                           and entity._original.feedback_adjustment == "revision"))'),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'review_feedback')], True,
                           'not account._is_guest and entity._original.seller_reference and \
                           entity._original.seller_reference._root == account.key \
                           and entity._original.state == "completed" and entity._is_feedback_allowed \
                           and entity._original.feedback == "negative" and entity._original.feedback_adjustment is None'),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'report_feedback')], True,
                           'not account._is_guest and entity._original.seller_reference \
                           and entity._original.seller_reference._root == account.key \
                           and entity._original.state == "completed" \
                           and entity._is_feedback_allowed and entity._original.feedback == "negative" \
                           and entity._original.feedback_adjustment not in ["reported", "sudo"]' ),
      orm.ActionPermission('34', [orm.Action.build_key('34', 'sudo_feedback')], True,
                           'account._root_admin and entity._original.state == "completed" \
                           and entity._is_feedback_allowed'),
      # @todo Implement field permissions!
      orm.FieldPermission('34', ['created', 'updated', 'state', 'date', 'seller_reference',
                                 'billing_address', 'shipping_address', 'currency', 'untaxed_amount',
                                 'tax_amount', 'total_amount', 'feedback', 'carrier', '_seller_reference',
                                 'feedback_adjustment', 'payment_status', 'payment_method',
                                 '_lines', '_messages','_payment_method', '_records', '_seller'], False, True,
                          'account._is_taskqueue or account._root_admin or (not account._is_guest \
                          and (entity._original.key_root == account.key or (entity._original.seller_reference \
                          and entity._original.seller_reference._root == account.key)))'),
      orm.FieldPermission('34', ['date', 'seller_reference', 'billing_address', 'shipping_address',
                                 'currency', 'untaxed_amount', 'tax_amount', 'total_amount',
                                 'payment_method', '_lines', '_messages', 'carrier', '_records'], True, True,
                          'not account._is_guest and entity._original.key_root == account.key \
                           and entity._original.state == "cart" and action.key_id_str == "update_line"'),
      orm.FieldPermission('34', ['state'], True, True,
                          '(action.key_id_str == "update_line" and entity.state == "cart") \
                          or (action.key_id_str == "checkout" and entity.state == "checkout") \
                          or (action.key_id_str == "cancel" and entity.state == "canceled") \
                          or (action.key_id_str == "complete" and entity.state == "completed")'),
      orm.FieldPermission('34', ['payment_status', '_messages'], True, True,
                          'account._is_taskqueue and action.key_id_str == "complete"'), # writable when in complete action mode
      orm.FieldPermission('34', ['_messages'], True, True,
                          'account._root_admin or (not account._is_guest and ((entity._original.key_root == account.key) \
                           or (entity._original.seller_reference \
                           and entity._original.seller_reference._root == account.key)))'),
      orm.FieldPermission('34', ['shipping_address', 'billing_address', '_lines', 'carrier',
                                 'untaxed_amount', 'tax_amount', 'total_amount'], True, True,
                          'not account._is_guest and entity._original.key_root == account.key \
                           and entity._original.state == "cart" and action.key_id_str in ["view_order", "update"]'),
      orm.FieldPermission('34', ['_lines.sequence', '_lines.product', '_lines.discount', '_lines.taxes'], False, None,
                          'not account._is_guest and entity._original.key_root == account.key \
                           and entity._original.state == "cart" and action.key_id_str == "update"'),
      orm.FieldPermission('34', ['_lines.product.quantity'], True, None,
                          'not account._is_guest and entity._original.key_root == account.key \
                           and entity._original.state == "cart" and action.key_id_str == "update"'),
      orm.FieldPermission('34', ['feedback', 'feedback_adjustment'], True, True,
                          '(action.key_id_str == "leave_feedback") or (action.key_id_str == "review_feedback") \
                          or (action.key_id_str == "report_feedback") or (action.key_id_str == "sudo_feedback")'),
      orm.FieldPermission('34', ['_messages._agent.sessions', '_messages._agent.emails', '_messages._agent._primary_email',
                                 '_messages._agent.identities', '_messages._agent._records', '_messages._agent._csrf'], False, False, 'True'),
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('34', 'update_line'),
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
            PluginExec(cfg={'kinds': ['117']}), # order currency must be available for everyone
            ProductSpecs(),
            UpdateOrderLine(),
            OrderLineRemovals(),
            PluginExec(), # @todo remove
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
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
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
            ProductSpecs(),
            PluginExec(cfg={'kinds': ['113', '107']}), # @todo remove
            RulePrepare(),
            RuleExec(),
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
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True),
        'payment_method': orm.SuperVirtualKeyProperty(),
        'billing_address_reference': orm.SuperVirtualKeyProperty(kind='14'), # @todo convert to local structured 14
        'shipping_address_reference': orm.SuperVirtualKeyProperty(kind='14'), # @todo convert to local structured 14
        'carrier': orm.SuperVirtualKeyProperty(kind='113'),
        '_lines': orm.SuperLocalStructuredProperty(OrderLine, repeated=True),
        'read_arguments': orm.SuperJsonProperty() 
        # @todo include 'state' => choices => [checkout] optional
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(cfg={'read': {'_lines': {'config': {'search': {'options': {'limit': 0}}}}}}),
            Set(cfg={'d': {'_order.payment_method': 'input.payment_method',
                           '_order._lines': 'input._lines'}}),
            OrderLineRemovals(),
            ProductSpecs(),
            PluginExec(),
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
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'orders': [{'field': 'updated', 'operator': 'desc'}]},
          cfg={
            'search_arguments': {'kind': '34', 'options': {'limit': settings.SEARCH_PAGE}},
            'ancestor_kind': '19',
            'search_by_keys': True,
            'filters': {'name': orm.SuperStringProperty(),
                        'key': orm.SuperVirtualKeyProperty(kind='34', searchable=False),
                        'state': orm.SuperStringProperty(repeated=True, choices=('checkout', 'cart', 'canceled', 'completed')),
                        'seller_reference': orm.SuperKeyProperty(kind='23', searchable=False)},
            'indexes': [{'orders': [('updated', ['asc', 'desc'])]},
                        {'orders': [('created', ['asc', 'desc'])]},
                        {'filters': [('key', ['=='])]},
                        {'filters': [('state', ['IN'])], 'orders': [('updated', ['asc', 'desc']), ('key', ['asc'])]},
                        {'ancestor': True, 'filters': [('state', ['IN'])], 'orders': [('updated', ['desc']), ('key', ['asc'])]},
                        {'filters': [('seller_reference', ['=='])], 'orders': [('updated', ['desc'])]}]
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
      key=orm.Action.build_key('34', 'checkout'), # checkout needs to run last pluginExec to make sure that all data that seller and buyer provided are synced one more for last time before "big freeze"
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
      key=orm.Action.build_key('34', 'complete'),
      arguments={
        'payment_method': orm.SuperStringProperty(required=True, choices=settings.AVAILABLE_PAYMENT_METHODS),
        'request': orm.SuperPickleProperty(),
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            OrderProcessPayment(),
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
            Notify(cfg={'condition': 'entity.state == "completed"',
                        's': {'sender': settings.NOTIFY_EMAIL,
                              'subject': notifications.ORDER_COMPLETE_SUBJECT,
                              'body': notifications.ORDER_COMPLETE_BODY},
                        'd': {'recipient': '_order.seller_and_buyer_emails'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'leave_feedback'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True),
        'feedback': orm.SuperStringProperty(required=True, choices=('positive', 'neutral', 'negative')),
        'message': orm.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_order.feedback_adjustment': None},
                     'd': {'_order.feedback': 'input.feedback'}}),
            SetMessage(),
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
            # notify seller that buyer left feedback
            # @todo cron to send buyer a message when he is ready to leave feedback because there is wait time
            Notify(cfg={'s': {'sender': settings.NOTIFY_EMAIL,
                              'subject': notifications.ORDER_COMPLETE_SUBJECT,
                              'body': notifications.ORDER_COMPLETE_BODY},
                        'd': {'recipient': '_order.seller_email'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'review_feedback'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True),
        'message': orm.SuperTextProperty(required=True) # @todo max length?
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_order.feedback_adjustment': 'revision'}}),
            SetMessage(),
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
            # buyer needs to get a message so he must leave feedback again
            Notify(cfg={'s': {'sender': settings.NOTIFY_EMAIL,
                              'subject': notifications.ORDER_REVIEW_FEEDBACK_SUBJECT,
                              'body': notifications.ORDER_REVIEW_FEEDBACK_BODY},
                        'd': {'recipient': '_order.buyer_email'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'report_feedback'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True),
        'message': orm.SuperTextProperty(required=True) # @todo max length?
      },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_order.feedback_adjustment': 'reported'}}),
            SetMessage(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            # admin and buyer gets message
            Notify(cfg={'s': {'sender': settings.NOTIFY_EMAIL,
                              'subject': notifications.ORDER_REPORT_FEEDBACK_SUBJECT,
                              'body': notifications.ORDER_REPORT_FEEDBACK_BODY},
                        'd': {'recipient': '_order.admin_and_buyer_email'}}),
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('34', 'sudo_feedback'),
      arguments={
        'key': orm.SuperKeyProperty(kind='34', required=True),
        'feedback': orm.SuperStringProperty(required=True, choices=('positive', 'neutral', 'negative')),
        'message': orm.SuperTextProperty(required=True) # @todo max length?
      },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_order.feedback_adjustment': 'sudo'},
                     'd': {'_order.feedback': 'input.feedback'}}),
            SetMessage(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            # buyer and seller get message
            Notify(cfg={'s': {'sender': settings.NOTIFY_EMAIL,
                              'subject': notifications.ORDER_SUDO_FEEDBACK_SUBJECT,
                              'body': notifications.ORDER_SUDO_FEEDBACK_BODY},
                        'd': {'recipient': '_order.seller_and_buyer_emails'}}),
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
        'message': orm.SuperTextProperty(required=True) # @todo max length?
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            SetMessage(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            # send message to either seller or buyer depending on who sent it
            # if admin sends message, both buyer and seller must get it too
            Notify(cfg={'condition': 'account._root_admin',
                        's': {'sender': settings.NOTIFY_EMAIL,
                              'subject': notifications.ORDER_LOG_MESSAGE_SUBJECT,
                              'body': notifications.ORDER_LOG_MESSAGE_BODY},
                        'd': {'recipient': '_order.seller_and_buyer_emails'}}),
            Notify(cfg={'condition': 'not account._root_admin and account.key == entity._root',
                        's': {'sender': settings.NOTIFY_EMAIL,
                              'subject': notifications.ORDER_LOG_MESSAGE_SUBJECT,
                              'body': notifications.ORDER_LOG_MESSAGE_BODY},
                        'd': {'recipient': '_order.seller_email'}}),
            Notify(cfg={'condition': 'not account._root_admin and account.key == entity.seller_reference._root',
                        's': {'sender': settings.NOTIFY_EMAIL,
                              'subject': notifications.ORDER_LOG_MESSAGE_SUBJECT,
                              'body': notifications.ORDER_LOG_MESSAGE_BODY},
                        'd': {'recipient': '_order.buyer_email'}}),
            Set(cfg={'d': {'output.entity': '_order'}})
            ]
          )
        ]
      )
    ]
  
  @property
  def seller_email(self):
    return self.root_entity._primary_email

  @property
  def buyer_email(self):
    return self.seller_reference._root.entity._primary_email

  @property
  def seller_and_buyer_emails(self):
    emails = []
    emails.append(self.seller_email)
    emails.append(self.buyer_email)
    return emails
  
  @property
  def admin_and_buyer_email(self):
    emails = []
    emails.extend(settings.ROOT_ADMINS)
    emails.append(self.buyer_email)
    return emails
  
  @property
  def _is_feedback_allowed(self):
    # if the order.date is not older than x days
    return self.date > (datetime.datetime.now() - datetime.timedelta(days=settings.FEEDBACK_ALLOWED_DAYS))
  
  def _get_payment_method(self):
    self._seller.read()
    if self._seller.value:
      self._seller.value._plugin_group.read()
      if self._seller.value._plugin_group.value:
        for plugin in self._seller.value._plugin_group.value.plugins:
          if plugin.key == self.payment_method:
            return plugin
          # values of the payment method must be controlled for public
          # because we do not have permission system for remoteStructuredProperty (for multiple kinds)
    return None
