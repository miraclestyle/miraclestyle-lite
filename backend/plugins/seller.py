# -*- coding: utf-8 -*-
'''
Created on Sep 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime
import collections
from decimal import Decimal
import tools

import orm

__all__ = ['SellerSetupDefaults', 'SellerDeleteFarCacheGroups', 'SellerMaybeDeleteFarCacheGroups']


class SellerMaybeDeleteFarCacheGroups(orm.BaseModel):

  def run(self, context):
    seller = context._seller
    original = seller._original
    send = False
    props = ['name', 'logo.value.serving_url', '_currency.key']
    for prop in props:
      v1 = tools.get_attr(seller, prop)
      v2 = tools.get_attr(original, prop)
      if v1 != v2:
        tools.log.debug(['found at', prop, v1, v2])
        send = True
        break
    if send:
      context._callbacks.append(('callback', {'action_id': 'far_cache_groups_flush', 'key': seller.key_urlsafe, 'action_model': '23'}))


class SellerDeleteFarCacheGroups(orm.BaseModel):

  def run(self, context):
    Catalog = context.models['31']
    Order = context.models['34']
    key = context._seller.key
    groups = []
    context.delete_cache_groups = groups
    if key:
      account_seller_id = key._root._id_str
      any_public = Catalog.query(Catalog.state.IN(['published', 'indexed']), ancestor=key).count(1)
      catalog_keys = Catalog.query(ancestor=key).fetch(keys_only=True)
      if any_public:
        groups.append('search_31')
      if catalog_keys:
        groups.append('search_31_admin')
        groups.append('search_31_%s' % account_seller_id)
        for catalog_key in catalog_keys:
          groups.append('read_31_%s' % catalog_key._id_str)

      order_keys = Order.query(Order.seller_reference == key).fetch(keys_only=True)
      if order_keys:
        groups.append('search_34_admin')
        groups.append('search_34')
        for order_key in order_keys:
          groups.append('search_34_seller_%s' % account_seller_id)
          groups.append('search_34_buyer_%s' % order_key._root._id_str)
          groups.append('read_34_%s' % order_key._id_str)


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
    default_address_shipping = OrderAddressPlugin(name='Shipping worldwide', exclusion=False, address_type='shipping', active=True)
    default_address_billing = OrderAddressPlugin(name='Billing worldwide', exclusion=False, address_type='billing', active=True)
    default_carrier = OrderCarrierPlugin(name='Free international shipping', active=True, lines=[OrderCarrierLine(name='Shipping everywhere', active=True)])
    default_currency = OrderCurrencyPlugin(name='Currency (USD)', currency=Unit.build_key('usd'), active=True)
    default_paypal_payment = OrderPayPalPaymentPlugin(name='PayPal payments', reciever_email=context.account._primary_email, business=context.account._primary_email, active=False)
    default_discount = OrderDiscountPlugin(name='Discounts',
                                           lines=[OrderDiscountLine(name='Discount 10% on quantity over 5',
                                                                    condition_type='quantity',
                                                                    condition_operator='>',
                                                                    condition_value=Decimal('5'),
                                                                    discount_value=Decimal('10'),
                                                                    active=True)], active=False)
    default_tax = OrderTaxPlugin(name='Sales tax', address_type='billing', type='proportional', amount=Decimal('6.5'), active=False)
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
      default_currency_find = filter(lambda x: x.get_kind() == OrderCurrencyPlugin.get_kind(), plugin_group.plugins)
      default_addresses = filter(lambda x: x.get_kind() == OrderAddressPlugin.get_kind(), plugin_group.plugins)
      default_carrier_find = filter(lambda x: x.get_kind() == OrderCarrierPlugin.get_kind(), plugin_group.plugins)

      def always_active(entities):
        if len(entities):
          actives = filter(lambda x: x.active == True, entities)
          if not actives:
            entities[0].active = True

      if not default_addresses:
        plugin_group.plugins.extend([default_address_billing, default_address_shipping])
      else:
        default_addresses_shipping = filter(lambda x: x.get_kind() == OrderAddressPlugin.get_kind() and x.address_type == 'shipping', plugin_group.plugins)
        default_addresses_billing = filter(lambda x: x.get_kind() == OrderAddressPlugin.get_kind() and x.address_type == 'billing', plugin_group.plugins)
        if not default_addresses_billing:
          plugin_group.plugins.append(default_address_billing)
        else:
          always_active(default_addresses_billing)
        if not default_addresses_shipping:
          plugin_group.plugins.append(default_address_shipping)
        else:
          always_active(default_addresses_shipping)
        if len(default_addresses) < 2:
          address = default_addresses[0]
          address.active = True # active always
          if address.address_type == 'shipping':
            plugin_group.plugins.append(default_address_billing)
          if address.address_type == 'billing':
            plugin_group.plugins.append(default_address_shipping)
        else:
          for address in default_addresses:
            address.active = True # active always
      if not default_currency_find:
        plugin_group.plugins.append(default_currency)
      else:
        always_active(default_currency_find)
      if not default_carrier_find:
        plugin_group.plugins.append(default_carrier)
      else:
        always_active(default_carrier_find)
