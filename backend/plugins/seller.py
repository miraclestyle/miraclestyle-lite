# -*- coding: utf-8 -*-
'''
Created on Sep 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import datetime
import copy
import collections

from google.appengine.api import search

import orm
from tools.base import *
from util import *

__all__ = ['SellerSetupDefaults', 'SellerCronGenerateFeedbackStats', 'SellerCron']

# @todo This plugin is pseudo coded, and needs to be rewritten!
class SellerCronGenerateFeedbackStats(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    seller = context._seller
    Order = context.models['34']
    SellerFeedback = context.models['37']
    SellerFeedbackStats = context.models['36']
    Account = context.models['11']
    today = datetime.datetime.now()
    start_of_this_month = datetime.datetime(today.year, today.month, today.day)
    year_start = start_of_this_month - datetime.timedelta(days=365)
    year_end = start_of_this_month
    feedback_states = ['positive', 'neutral', 'negative']
    run = True
    feedbacks = collections.OrderedDict()
    while run:
      futures = []
      for feedback_state in feedback_states:
        futures.append(Order.query(Order.seller_reference == seller.key,
                                   Order.date > year_start,
                                   Order.date < year_end,
                                   Order.feedback == feedback_state,
                                   Order.feedback_adjustment.IN([None, 'sudo']))
                             .order(Order.date, Order.key)
                             .fetch_page_async(100, projection=[Order.date], use_memcache=False, use_cache=False))
      should_keep_running = False
      dataset = {'accounts': {}}
      for i, future in enumerate(futures):
        state = feedback_states[i]
        result = future.get_result()
        if result[1] and result[2]:
          should_keep_running = True
        for order in result[0]:
          key = order.key._root
          gets = dataset['accounts'].get(key)
          month = datetime.datetime(order.date.year, order.date.month, 1)
          if not gets:
            gets = {'orders': {}}
            dataset['accounts'][key] = gets
          if not month in gets['orders']:
            gets['orders'][month] = {}
            for state in feedback_states:
              gets['orders'][month][state] = 0
          gets['orders'][month][state] += 1
      accounts = orm.get_multi(dataset['accounts'].keys(), use_memcache=False, use_cache=True)
      for account in accounts:
        if account.state == 'active':
          data = dataset['accounts'].get(account.key)
          for month, order in data['orders'].iteritems():
            if month not in feedbacks:
              feedbacks[month] = {}
              for feedback_state in feedback_states:
                feedbacks[month][feedback_state] = 0
            for state, count in order.iteritems():
              feedbacks[month][state] += count
      run = should_keep_running

    gets = start_of_this_month
    for i in xrange(0, 12):
      gets = datetime.datetime(gets.year, gets.month, 1)
      if gets not in feedbacks:
        feedbacks[gets] = {'positive': 0, 'neutral': 0, 'negative': 0}
      lastMonth = gets - datetime.timedelta(days=1)
      gets = datetime.datetime(lastMonth.year, lastMonth.month, 1)
    set_feedbacks = []
    for date, counts in feedbacks.iteritems():
      set_feedbacks.append(SellerFeedbackStats(date=date,
                                               positive_count=counts['positive'],
                                               neutral_count=counts['neutral'],
                                               negative_count=counts['negative']))

    set_feedbacks.sort(key=lambda x: x.date)
    for i, s in enumerate(set_feedbacks):
      s._sequence = i
    context._seller._feedback = SellerFeedback(feedbacks=set_feedbacks)

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


class SellerCron(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    Seller = context.models['23']
    sellers = Seller.query().fetch_page(4, start_cursor=context.input.get('cursor'))
    for seller in sellers[0]:
      data = {'action_id': 'cron_generate_feedback_stats',
              'action_model': '23',
              'key': seller.key_urlsafe}
      context._callbacks.append(('callback', data))
    cursor = None
    if sellers[2] and sellers[1]:
      cursor = sellers[1]
    if cursor is None:
      return
    data = {'action_id': 'cron',
            'action_model': '23',
            'cursor': cursor}
    context._callbacks.append(('callback', data))