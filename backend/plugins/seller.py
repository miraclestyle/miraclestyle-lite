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
    seller = context._seller
    plugin_group = seller._plugin_group
    plugin_group.read()
    plugin_group = plugin_group.value
    if not plugin_group or not plugin_group.plugins: # now user wont be in able to delete config, he will always have these defaults
      plugins = [AddressRule(exclusion=False, address_type='billing'),
                 AddressRule(exclusion=False, address_type='shipping'),
                 OrderCurrency(currency=Unit.build_key('usd')),
                 PayPalPayment(reciever_email='your paypal e-mail', business='your paypal merchant id or e-mail')
                ]
      if not plugin_group:
        plugin_group = SellerPluginContainer(plugins=plugins)
      else:
        plugin_group.plugins = plugins
      seller._plugin_group = plugin_group