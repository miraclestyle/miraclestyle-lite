# -*- coding: utf-8 -*-
'''
Created on Sep 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import datetime
import copy

from google.appengine.api import search

import orm
from tools.base import *
from util import *

__all__ = ['SellerSetupDefaults', 'SellerCronGenerateFeedbackStats']

# @todo This plugin is pseudo coded, and needs to be rewritten!
class SellerCronGenerateFeedbackStats(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    order_age = self.cfg.get('age', 90)
    Order = context.models['34']
    SellerFeedbackStats = context.models['36']
    positive_count = Order.query(Order.seller_reference == 'seller_key',
                                 Order.date == (datetime.datetime.now() - datetime.timedelta(days=order_age)),
                                 Order.feedback == 'positive',
                                 Order.feedback_adjustment.IN([None, 'sudo'])).count(keys_only=True)
    neutral_count = Order.query(Order.seller_reference == 'seller_key',
                                Order.date == (datetime.datetime.now() - datetime.timedelta(days=order_age)),
                                Order.feedback == 'neutral',
                                Order.feedback_adjustment.IN([None, 'sudo'])).count(keys_only=True)
    negative_count = Order.query(Order.seller_reference == 'seller_key',
                                 Order.date == (datetime.datetime.now() - datetime.timedelta(days=order_age)),
                                 Order.feedback == 'negative',
                                 Order.feedback_adjustment.IN([None, 'sudo'])).count(keys_only=True)
    context._seller._feedback.feedbacks.append(SellerFeedbackStats(date=datetime.datetime.now() - datetime.timedelta(days=order_age),
                                                                   positive_count=positive_count,
                                                                   neutral_count=neutral_count,
                                                                   negative_count=negative_count))

class SellerSetupDefaults(orm.BaseModel):
  
  def run(self, context):
    SellerPluginContainer = context.models['22']
    AddressRule = context.models['107']
    PayPalPayment = context.models['108']
    Unit = context.models['17']
    OrderCurrency = context.models['117']
    Carrier = context.models['113']
    CarrierLine = context.models['112']
    seller = context._seller
    plugin_group = seller._plugin_group
    plugin_group.read()
    plugin_group = plugin_group.value
    default_address_rule_shipping = AddressRule(name='Default Address Shipping Rule', exclusion=False, address_type='shipping')
    default_address_rule_billing = AddressRule(name='Default Address Shipping Rule', exclusion=False, address_type='billing')
    default_carrier = Carrier(name='World Wide Shipping', active=True, lines=[CarrierLine(name='Free Shipping', active=True)])
    default_currency = OrderCurrency(name='Default Currency', currency=Unit.build_key('usd'))
    default_paypal_payment = PayPalPayment(name='Paypal Payment Method', reciever_email='your paypal e-mail', business='your paypal merchant id or e-mail')
    if not plugin_group or not plugin_group.plugins: # now user wont be in able to delete the config completely, he will always have these defaults
      plugins = [default_address_rule_shipping,
                 default_address_rule_billing,
                 default_currency,
                 default_paypal_payment,
                 default_carrier]
      if not plugin_group:
        plugin_group = SellerPluginContainer(plugins=plugins)
        seller._plugin_group = plugin_group
      else:
        plugin_group.plugins = plugins
    else:
      default_currency_find = filter(lambda x: x.get_kind() == '117', plugin_group.plugins)
      default_carrier_find = filter(lambda x: x.get_kind() == '113', plugin_group.plugins)
      default_paypal_payment_find = filter(lambda x: x.get_kind() == '108', plugin_group.plugins)
      if not default_currency_find:
        plugin_group.plugins.append(default_currency)
      if not default_carrier_find:
        plugin_group.plugins.append(default_carrier)
      if not default_paypal_payment_find:
        plugin_group.plugins.append(default_paypal_payment)