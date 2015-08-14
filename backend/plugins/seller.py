# -*- coding: utf-8 -*-
'''
Created on Sep 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime
import collections
from decimal import Decimal

import orm

__all__ = ['SellerSetupDefaults', 'SellerCronGenerateFeedbackStats']


class SellerCronGenerateFeedbackStats(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    Seller = context.models['23']
    Order = context.models['34']
    SellerFeedback = context.models['37']
    SellerFeedbackStats = context.models['36']
    Account = context.models['11']
    result = Seller.query().fetch_page(1, start_cursor=context.input.get('cursor'))
    if len(result) and len(result[0]):
      seller = result[0][0]
    else:
      # reached end
      return
    context._seller = seller
    context.entity = seller
    now = datetime.datetime.now()
    today = datetime.datetime(now.year, now.month, now.day)
    year_start = today - datetime.timedelta(days=365)
    year_end = today
    feedback_states = ['positive', 'neutral', 'negative']
    more = True
    feedbacks = collections.OrderedDict()
    current_month = today
    for i in xrange(0, 12):
      current_month = datetime.datetime(current_month.year, current_month.month, 1)
      feedbacks[current_month] = {'positive': 0, 'neutral': 0, 'negative': 0}
      previus_month = current_month - datetime.timedelta(days=1)
      current_month = datetime.datetime(previus_month.year, previus_month.month, 1)
    while more:
      futures = []
      for feedback_state in feedback_states:
        futures.append(Order.query(Order.seller_reference == seller.key,
                                   Order.date > year_start,
                                   Order.date < year_end,
                                   Order.feedback == feedback_state,
                                   Order.feedback_adjustment.IN([None, 'sudo']))
                       .order(Order.date, Order.key)
                       .fetch_page_async(100, projection=[Order.date], use_memcache=False, use_cache=False))
      more = False
      account_stats = {}
      for i, future in enumerate(futures):
        feedback_state = feedback_states[i]
        result = future.get_result()
        if result[1] and result[2]:
          more = True
        for order in result[0]:
          account_key = order.key._root
          month = datetime.datetime(order.date.year, order.date.month, 1)
          feedbacks[month][feedback_state] += 1
          if account_key not in account_stats:
            account_stats[account_key] = {}
          if month not in account_stats[account_key]:
            account_stats[account_key][month] = {'positive': 0, 'neutral': 0, 'negative': 0}
          account_stats[account_key][month][feedback_state] += 1
      accounts = orm.get_multi(account_keys, use_memcache=False, use_cache=True)
      for account in accounts:
        if account.state != 'active':
          stats = account_stats.get(account.key)
          for month, feedback_stats in feedbacks.iteritems():
            if month in stats:
              for feedback_state in feedback_states:
                feedback_stats[feedback_state] -= stats[month][feedback_state]

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
    if result[2] and result[1]:  # if result.more and result.cursor
      data = {'action_id': 'cron_generate_feedback_stats',
              'action_model': '23',
              'cursor': result[1]}
      context._callbacks.append(('callback', data))


class SellerSetupDefaults(orm.BaseModel):

  def run(self, context):
    SellerPluginContainer = context.models['22']
    OrderAddressPlugin = context.models['107']
    OrderPayPalPaymentPlugin = context.models['108']
    Unit = context.models['17']
    OrderCurrencyPlugin = context.models['117']
    OrderCarrierPlugin = context.models['113']
    OrderCarrierLine = context.models['112']
    OrderDiscountPlugin = context.models['126']
    OrderDiscountLine = context.models['124']
    OrderTaxPlugin = context.models['109']
    seller = context._seller
    plugin_group = seller._plugin_group
    plugin_group.read()
    plugin_group = plugin_group.value
    default_address_shipping = OrderAddressPlugin(name='Shipping worldwide', exclusion=False, address_type='shipping')
    default_address_billing = OrderAddressPlugin(name='Billing worldwide', exclusion=False, address_type='billing')
    default_carrier = OrderCarrierPlugin(name='Free international shipping', active=True, lines=[OrderCarrierLine(name='Shipping everywhere', active=True)])
    default_currency = OrderCurrencyPlugin(name='Currency (USD)', currency=Unit.build_key('usd'))
    default_paypal_payment = OrderPayPalPaymentPlugin(name='PayPal payments', reciever_email=context.account._primary_email, business=context.account._primary_email)
    default_discount = OrderDiscountPlugin(name='Discount on quantity (10%)',
                                           lines=[OrderDiscountLine(name='Discount on quantity (10%)',
                                                                    condition_type='quantity',
                                                                    condition_operator='>',
                                                                    condition_value=Decimal('5'),
                                                                    discount_value=Decimal('10'),
                                                                    active=True)], active=False)
    default_tax = OrderTaxPlugin(name='Sales tax', address_type='shipping', type='proportional', amount=Decimal('6'), active=False)
    if not plugin_group or not plugin_group.plugins:  # now user wont be in able to delete the config completely, he will always have these defaults
      plugins = [default_address_billing,
                 default_address_shipping,
                 default_carrier,
                 default_currency,
                 default_discount,
                 default_paypal_payment,
                 default_tax]
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
      else:
        default_currency_find[0].active = True
      if not default_carrier_find:
        plugin_group.plugins.append(default_carrier)
      else:
        default_carrier_find[0].active = True
      if not default_paypal_payment_find:
        plugin_group.plugins.append(default_paypal_payment)
      else:
        default_paypal_payment_find[0].active = True
