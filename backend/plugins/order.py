# -*- coding: utf-8 -*-
'''
Created on Aug 25, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime
import collections
import re
import copy

import orm
from tools.base import *
from util import *

from models.location import *
from models.unit import *


class PluginError(Exception):
  
  def __init__(self, plugin_error):
    self.message = {'plugin_error': plugin_error}


# This is system plugin, which means end user can not use it!
class OrderInit(orm.BaseModel):
  
  _kind = 99
  
  _use_rule_engine = False
  
  def run(self, context):
    Order = context.models['34']
    seller_key = context.input.get('seller')
    if not seller_key:
      product = context.input.get('product')
      if not product:
        raise PluginError('seller_missing')
      seller_key = product.parent().parent().parent() # go 3 levels up, account->seller->catalog->pricetag->product
    order = Order.query(Order.seller_reference == seller_key,
                        Order.state.IN(['cart', 'checkout']),
                        ancestor=context.input.get('buyer')).get()  # we will need composite index for this
    if order is None:
      order = Order(parent=context.input.get('buyer'), name='Default Order Name') # we need a name for this
      order.state = 'cart'
      order.date = datetime.datetime.now()
      order.seller_reference = seller_key
      seller = seller_key.get()
      seller.read() # read locals
    else:
      defaults = {'_lines' : {'config': {'search': {'options': {'limit': 0}}}}}
      if 'read_arguments' in context.input:
        override_dict(defaults, context.input.get('read_arguments'))
      order.read(defaults)  # @todo It is possible that we will have to read more stuff here.
    context._order = order


# This is system plugin, which means end user can not use it!
class PluginExec(orm.BaseModel):
  
  _kind = 114
  
  _use_rule_engine = False
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    plugin_kinds = self.cfg.get('kinds') # this is the flexibility we need, just to specify which plugin kinds to execute
    order = context._order
    seller = order.seller_reference.get()
    seller.read({'_plugin_group': {'plugins': {}}}) # read plugin container
    plugin_container = seller._plugin_group.value
    if plugin_container:
      for plugin in seller._plugin_group.value.plugins:
        if plugin_kinds is not None and plugin.get_kind() not in plugin_kinds:
          continue
        plugin.run(context)


# This is system plugin, which means end user can not use it!
class UpdateOrderLine(orm.BaseModel):
  
  _kind = 101
  
  _use_rule_engine = False
  
  def run(self, context):
    OrderProduct = context.models['125']
    CatalogProduct = context.models['28']
    order = context._order
    product_key = context.input.get('product')
    image_key = context.input.get('image')
    quantity = context.input.get('quantity')
    if order.state != 'cart':
      raise PluginError('order_not_in_cart_state')
    variant_signature = context.input.get('variant_signature')
    line_exists = False
    if order._lines.value:
      for line in order._lines.value:
        product = line.product.value
        real_product_key = OrderProduct.get_partial_reference_key_path(product.reference)
        if product and real_product_key == product_key \
        and product.variant_signature == variant_signature:
          line._state = 'modified'
          product.quantity = format_value(quantity, product.uom.value)
          line_exists = True
          break
    if not line_exists:
      ProductInstance = context.models['27']
      Line = context.models['33']
      product = product_key.get()
      product_instance = None
      product.read({'_category': {}})  # more fields probably need to be specified
      if variant_signature:
        product_instance_query = ProductInstance.query()
        for variant in variant_signature:
          item = variant.iteritems().next()
          product_instance_query = product_instance_query.filter(ProductInstance.variant_options == '%s: %s' % (item[0], item[1]))
        product_instance = product_instance_query.get()
      new_line = Line()
      new_line.sequence = 1
      if order._lines.value:
        new_line.sequence = order._lines.value[-1].sequence + 1
      copy_product = OrderProduct()
      copy_product.name = product.name
      modified_product_key = CatalogProduct.get_complete_key_path(image_key, product_key)
      copy_product.reference = modified_product_key
      copy_product.variant_signature = variant_signature
      copy_product.category = copy.deepcopy(product._category.value)
      copy_product.code = product.code
      copy_product.unit_price = format_value(product.unit_price, order.currency.value)
      copy_product.uom = copy.deepcopy(product.uom.get())
      if product_instance is not None:
        if hasattr(product_instance, 'unit_price') and product_instance.unit_price is not None:
          copy_product.unit_price = product_instance.unit_price
        if hasattr(product_instance, 'code') and product_instance.code is not None:
          copy_product.code = product_instance.code
      copy_product.weight = None
      copy_product.weight_uom = None
      copy_product.volume = None
      copy_product.volume_uom = None
      if product.weight is not None and product.weight_uom is not None:
        copy_product.weight = product.weight
        copy_product.weight_uom = copy.deepcopy(product.weight_uom.get())
      if product.volume is not None and product.volume_uom is not None:
        copy_product.volume = product.volume
        copy_product.volume_uom = copy.deepcopy(product.volume_uom.get())
      if copy_product.variant_signature:
        if product_instance is not None:
          if hasattr(product_instance, 'weight') and product_instance.weight is not None and product_instance.weight_uom  is not None:
            copy_product.weight = product_instance.weight
            copy_product.weight_uom = copy.deepcopy(product_instance.weight_uom.get())
          if hasattr(product_instance, 'volume') and product_instance.volume is not None and product_instance.volume_uom is not None:
            copy_product.volume = product_instance.volume
            copy_product.volume_uom = copy.deepcopy(product_instance.volume_uom.get())
      copy_product.quantity = format_value(quantity, copy_product.uom.value)
      new_line.product = copy_product
      new_line.discount = format_value('0', Unit(digits=2))
      lines = order._lines.value
      if lines is None:
        lines = []
      lines.append(new_line)
      order._lines = lines


# This is system plugin, which means end user can not use it!
class ProductSpecs(orm.BaseModel):
  
  _kind = 115
  
  _use_rule_engine = False
  
  def run(self, context):
    ProductInstance = context.models['27']
    order = context._order
    weight_uom = Unit.build_key('kilogram').get()
    volume_uom = Unit.build_key('cubic_meter').get()
    unit_uom = Unit.build_key('unit').get()
    total_weight = format_value('0', weight_uom)
    total_volume = format_value('0', volume_uom)
    total_quantity = format_value('0', unit_uom)
    if order._lines.value:
      for line in order._lines.value:
        product = line.product.value
        if product.weight is not None:
          total_weight = total_weight + (convert_value(product.weight, product.weight_uom.value, weight_uom) * product.quantity)
        if product.volume is not None:
          total_volume = total_volume + (convert_value(product.volume, product.volume_uom.value, volume_uom) * product.quantity)
        total_quantity = total_quantity + convert_value(product.quantity, product.uom.value, unit_uom)
    order._total_weight = total_weight
    order._total_volume = total_volume
    order._total_quantity = total_quantity


# This is system plugin, which means end user can not use it!
class OrderLineFormat(orm.BaseModel):
  
  _kind = 104
  
  _use_rule_engine = False
  
  def run(self, context):
    order = context._order
    for line in order._lines.value:
      product = line.product.value
      if product:
        if order.seller_reference._root != product.reference._root:
          raise PluginError('product_does_not_bellong_to_seller')
        line.discount = format_value(line.discount, Unit(digits=2))
        if product.quantity <= Decimal('0'):
          line._state = 'deleted'
        else:
          product.quantity = format_value(product.quantity, product.uom.value)
        line.subtotal = format_value((product.unit_price * product.quantity), order.currency.value)
        if line.discount is not None:
          discount = line.discount * format_value('0.01', Unit(digits=2))  # or "/ format_value('100', Unit(digits=2))"
          line.discount_subtotal = format_value((line.subtotal - (line.subtotal * discount)), order.currency.value)
        else:
          line.discount_subtotal = format_value('0', Unit(digits=2))
        tax_subtotal = format_value('0', order.currency.value)
        if line.taxes.value:
          for tax in line.taxes.value:
            if tax.type == 'percent':
              tax_amount = format_value(tax.amount, Unit(digits=2)) * format_value('0.01', Unit(digits=2))  # or "/ format_value('100', Unit(digits=2))"  @todo Using fixed formating here, since it's the percentage value, such as 17.00%.
              tax_subtotal = tax_subtotal + (line.discount_subtotal * tax_amount)
            elif tax.type == 'fixed':
              tax_amount = format_value(tax.amount, order.currency.value)
              tax_subtotal = tax_subtotal + tax_amount
        line.tax_subtotal = tax_subtotal
        line.total = format_value(line.discount_subtotal + line.tax_subtotal, order.currency.value)


# This is system plugin, which means end user can not use it!
class OrderCarrierFormat(orm.BaseModel):
  
  _kind = 122
  
  _use_rule_engine = False
  
  def run(self, context):
    order = context._order
    carrier = order.carrier.value
    if carrier:
      carrier.subtotal = format_value(carrier.unit_price, order.currency.value)
      tax_subtotal = format_value('0', order.currency.value)
      if carrier.taxes.value:
        for tax in carrier.taxes.value:
          if tax.type == 'percent':
            tax_amount = format_value(tax.amount, Unit(digits=2)) * format_value('0.01', Unit(digits=2))
            tax_subtotal = tax_subtotal + (carrier.subtotal * tax_amount)
          elif tax.type == 'fixed':
            tax_amount = format_value(tax.amount, order.currency.value)
            tax_subtotal = tax_subtotal + tax_amount
      carrier.tax_subtotal = tax_subtotal
      carrier.total = format_value(carrier.subtotal + carrier.tax_subtotal, order.currency.value)


# This is system plugin, which means end user can not use it!
class OrderFormat(orm.BaseModel):
  
  _kind = 105
  
  _use_rule_engine = False
  
  def run(self, context):
    order = context._order
    untaxed_amount = format_value('0', order.currency.value)
    tax_amount = format_value('0', order.currency.value)
    total_amount = format_value('0', order.currency.value)
    for line in order._lines.value:
      product = line.product.value
      if product:
        untaxed_amount = untaxed_amount + line.discount_subtotal
        tax_amount = tax_amount + line.tax_subtotal
        total_amount = total_amount + (line.discount_subtotal + line.tax_subtotal) # we cannot use += for decimal its not supported
    carrier = order.carrier.value
    if carrier:
      untaxed_amount = untaxed_amount + carrier.subtotal
      tax_amount = tax_amount + carrier.tax_subtotal
      total_amount = total_amount + (carrier.subtotal + carrier.tax_subtotal)
    order.untaxed_amount = format_value(untaxed_amount, order.currency.value)
    order.tax_amount = format_value(tax_amount, order.currency.value)
    order.total_amount = format_value(total_amount, order.currency.value)


# Not a plugin!
class AddressRuleLocation(orm.BaseModel):
  
  _kind = 106
  
  _use_rule_engine = False
  
  country = orm.SuperKeyProperty('1', kind='12', required=True, indexed=False)
  region = orm.SuperKeyProperty('2', kind='13', indexed=False)
  postal_code_from = orm.SuperStringProperty('3', indexed=False)
  postal_code_to = orm.SuperStringProperty('4', indexed=False)
  city = orm.SuperStringProperty('5', indexed=False)
  
  _virtual_fields = {
    '_country': orm.SuperReferenceStructuredProperty('12', autoload=True, target_field='country'),
    '_region': orm.SuperReferenceStructuredProperty('13', autoload=True, target_field='region')
  }


class AddressRule(orm.BaseModel):
  
  _kind = 107
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  exclusion = orm.SuperBooleanProperty('3', required=True, default=False, indexed=False)
  address_type = orm.SuperStringProperty('4', required=True, default='billing', choices=['billing', 'shipping'], indexed=False)
  locations = orm.SuperLocalStructuredProperty(AddressRuleLocation, '5', repeated=True, indexed=False)
  
  def run(self, context):
    if not self.active:
      return # inactive plugin
    self.read() # read locals
    order = context._order
    valid_addresses = []
    default_address = None
    address_reference_key = '%s_address_reference' % self.address_type
    address_key = '%s_address' % self.address_type
    addresses_key = '%s_addresses' % self.address_type
    input_address_reference = context.input.get(address_reference_key)
    order_address = getattr(order, address_key)
    order_address = order_address.value
    buyer_addresses = order.key_parent.get()
    buyer_addresses.read() # read locals
    if buyer_addresses is None:
      raise PluginError('no_address')
    for buyer_address in buyer_addresses.addresses.value:
      if self.validate_address(buyer_address):
        if not filter(lambda x: x.key == buyer_address.key, valid_addresses):
          valid_addresses.append(buyer_address)
    if not len(valid_addresses):
      raise PluginError('no_valid_address')
    context.output[addresses_key] = valid_addresses
    input_address_value = filter(lambda x: x.key == input_address_reference, valid_addresses)
    order_address_value = None
    if order_address:
      order_address_value = filter(lambda x: x.key == order_address.reference, valid_addresses)
    if input_address_value:
      default_address = input_address_value[0]
    elif order_address_value:
      default_address = order_address_value[0]
    else:
      default_address = valid_addresses[0]
    if default_address:
      setattr(order, address_key, default_address.get_location())
    else:
      raise PluginError('no_address_found')
  
  def validate_address(self, address):
    '''
    @todo few problems with postal_code_from and postal_code_to
    Postal code cant always be a number unless its like that in countries.
    
    postal_code_from and postal_code_to must be converted into int, because strings cant be compared 
    to achive logical result other than native string's comparing logic:
    
    native strings compare method:
    __cmp__(self, other)
      return len(self) > len(other)
      
      One way to deal with this is to use postal_codes repeated string property on backend, and
      provide a user with UI tool where he can build a list of postal codes using
      postal_code_from and postal_code_to integers, or manually specify each individual postal code.
      Comparison can be much easier than.
    '''
    if self.exclusion:
      # Shipping only at the following locations.
      allowed = False
    else:
      # Shipping everywhere except at the following locations.
      allowed = True
    for loc in self.locations.value:
      if not (loc.region and loc.postal_code_from and loc.postal_code_to):
        if (address.country == loc.country):
          allowed = self.exclusion
          break
      elif not (loc.postal_code_from and loc.postal_code_to):
        if (address.country == loc.country and address.region == loc.region):
          allowed = self.exclusion
          break
      elif not (loc.postal_code_to):
        if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
          allowed = self.exclusion
          break
      else:
        if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
          allowed = self.exclusion
          break
    return allowed


class OrderCurrency(orm.BaseModel):
  
  _kind = 117
  
  _use_rule_engine = False
  
  # This plugin will be subscribed to many actions, among which is add_to_cart as well.
  # PayPal Shipping: Prompt for an address, but do not require one,
  # PayPal Shipping: Do not prompt for an address
  # PayPal Shipping: Prompt for an address, and require one
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  currency = orm.SuperKeyProperty('3', kind=Unit, required=True, indexed=False)
  
  def run(self, context):
    if not self.active:
      return # inactive currency
    order = context._order
    # In context of add_to_cart action runner does the following:
    order.currency = copy.deepcopy(self.currency.get())


class PaymentMethod(orm.BaseModel):
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  
  def _get_name(self):
    return self.__class__.__name__
  
  def _get_system_name(self):
    return self.__class__.__name__.lower()
  
  def run(self, context):
    if not self.active:
      return # inactive payment
    if 'payment_methods' not in context.output:
      context.output['payment_methods'] = []
    context.output['payment_methods'].append({'key': self.key,
                                              'system_name': self._get_system_name(),
                                              'name': self._get_name()})


# This plugin is incomplete!
class PayPalPayment(PaymentMethod):
  
  _kind = 108
  
  _use_rule_engine = False
  
  # This plugin will be subscribed to many actions, among which is add_to_cart as well.
  # PayPal Shipping: Prompt for an address, but do not require one,
  # PayPal Shipping: Do not prompt for an address
  # PayPal Shipping: Prompt for an address, and require one
  reciever_email = orm.SuperStringProperty('3', required=True, indexed=False)
  business = orm.SuperStringProperty('4', required=True, indexed=False)
  
  def _get_name(self):
    return 'Paypal'
  
  def _get_system_name(self):
    return 'paypal'
  
  def run(self, context):
    if not self.active:
      return
    super(PayPalPayment, self).run(context)
    # currently we only support paypal, so its enforced by default
    context._order.payment_method = self.key
  
  def complete(self, context):
    # @todo Remove settings from here, from ALL PLUGINS!!
    if settings.PAYPAL_SANDBOX:
      url = settings.PAYPAL_WEBSCR_SANDBOX
    else:
      url = settings.PAYPAL_WEBSCR
    request = context.input['request']
    ipn = request['params']
    order = context._order
    # validate if the request came from ipn
    result = urlfetch.fetch(url=url,
                            payload='cmd=_notify-validate&%s' % request['body'],
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/x-www-form-urlencoded', 'Connection': 'Close'})
    if result.content != 'VERIFIED':
      raise PluginError('invalid_ipn_message') # log somehow

    # begin ipn message validation
    mismatches = []
    shipping_address = order.shipping_address.value
    order_currency = order.currency.value
    
    # ipn alias
    ipn_payment_status = ipn['payment_status']
    
    # only verified ipn messages are to be saved
    OrderMessage = context.models['35']
    Account = context.models['11']
    order_messages = OrderMessage.query(orm.GenericProperty('ipn_txn_id') == ipn['txn_id']).fetch()
    for order_message in order_messages:
      if order_message.payment_status == ipn_payment_status:
        raise orm.TerminateAction('duplicate_entry') # ipns that come in with same payment_status are to be rejected
        # by the way, we cannot raise exceptions cause that will cause status code other than 200 and cause that the same
        # ipn will be called again until it reaches 200 status response code
        # ipn will retry for x amount of times till it gives up
        # so we might as well use `return` statement to exit silently
    body = 'Paypal Payment action %s' % ipn_payment_status # @todo modify accordingly
    new_order_message = OrderMessage(ipn_txn_id=ipn['txn_id'], ancestor=order.key, agent=Account.build_key('system'), body=body, payment_status=ipn_payment_status)
    new_order_message._clone_properties() # this is a hack, because we put all properties indexed = True
    new_order_message._properties['ipn'] = orm.SuperTextProperty(name='ipn', compressed=True)
    new_order_message._properties['ipn']._set_value(new_order_message, request['body'])
    order._messages = [new_order_message] # add this to queue
    
    if (self.reciever_email != ipn['receiver_email']):
      mismatches.append('receiver_email')
    if 'business' in ipn:
      if (self.business != ipn['business']):
        mismatches.append('business_email')
    if (order_currency.code != ipn['mc_currency']):
      mismatches.append('mc_currency')
    if (order.total_amount != format_value(ipn['mc_gross'], order_currency)):
      mismatches.append('mc_gross')
    if (order.tax_amount != format_value(ipn['tax'], order_currency)):
      mismatches.append('tax')
    if (order.key.urlsafe() != ipn['invoice']): # @todo we do not use order.name here anymore, but we could after we decide on how to uniquely build it
      mismatches.append('invoice')
    if (shipping_address.country != ipn['address_country']):
      mismatches.append('address_country')
    if (shipping_address.country_code != ipn['address_country_code']):
      mismatches.append('address_country_code')
    if (shipping_address.city != ipn['address_city']):
      mismatches.append('address_city')
    if (shipping_address.name != ipn['address_name']):
      mismatches.append('address_name')
    if shipping_address.country_code == 'US' and shipping_address.region_code[len(shipping_address.country_code) + 1:] != ipn['address_state']: # paypal za ameriku koristi 2 digit iso standard kodove za njegove stateove
      mismatches.append('address_state')
    if (shipping_address.street != ipn['address_street']): 
      # PayPal spaja vrednosti koje su prosledjene u cart upload procesu (address1 i address2), 
      # tako da u povratu putem IPN-a, polje address_street izgleda ovako address1\r\naddress2. 
      # Primer: u'address_street': [u'1 Edi St\r\nApartment 7'], gde je vrednost Street Address 
      # od kupca bilo "Edi St", a vrednost Street Address (Optional) "Apartment 7".
      mismatches.append('address_street')
    if (shipping_address.postal_code != ipn['address_zip']):
      mismatches.append('address_zip')
        
    for line in order._lines.value:
      product = line.product.value
      log('Order sequence %s' % line.sequence)
      # our line sequences begin with 0 but should begin with 1 because paypal does not support 0
      if (str(line.sequence) != ipn['item_number%s' % str(line.sequence)]): # ovo nije u order funkcijama implementirano tako da ne znamo da li cemo to imati..
        mismatches.append('item_number%s' % str(line.sequence))
      if (product.name != ipn['item_name%s' % str(line.sequence)]):
        mismatches.append('item_name%s' % str(line.sequence))
      if (product.quantity != format_value(ipn['quantity%s' % str(line.sequence)], product.uom.value)):
        mismatches.append('quantity%s' % str(line.sequence))
      if (line.subtotal != format_value(ipn['mc_gross_%s' % str(line.sequence)], order_currency)):
        mismatches.append('mc_gross_%s' % str(line.sequence))
    # Ukoliko je doslo do fail-ova u poredjenjima
    # radi se dispatch na notification engine sa detaljima sta se dogodilo, radi se logging i algoritam se prekida.
    if not mismatches:
      if order.payment_status == ipn_payment_status:
        # @todo also log?
        return None # nothing to do since the payment status is exactly the same
      else:
        update_paypal_payment_status = False
        if order.payment_status == 'Pending' or order.payment_status == None: # send update command ONLY if the payment_status is pending or it wasnt set (e.g. new order)
          if ipn_payment_status == 'Completed' or ipn_payment_status == 'Denied':
            update_paypal_payment_status = True
        elif order.payment_status == 'Completed':
          if ipn_payment_status == 'Refunded' or ipn_payment_status == 'Reversed':
            update_paypal_payment_status = True
        if update_paypal_payment_status:
            # ovo se verovatno treba jos doterati..
            if order.state == 'checkout' and ipn_payment_status == 'Completed':
              order.state = 'completed'
              order.payment_status = ipn_payment_status
            elif order.state == 'checkout' and ipn_payment_status == 'Denied': # ovo cemo jos da razmotrimo
              order.state = 'canceled'
              order.payment_status = ipn_payment_status
            elif order.state == 'completed':
              order.payment_status = ipn_payment_status
    else:
      # log that there were missmatches, where we should log that?
      log('Found mismatches=%s with ipn=%s for order=%s' % (mismatches, ipn, order.key))
    log('Set Order state %s' % order.state)
    log('Set Order payment_status %s' % order.payment_status)


class Tax(orm.BaseModel):
  
  _kind = 109
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  type = orm.SuperStringProperty('3', required=True, default='percent', choices=['percent', 'fixed'], indexed=False)
  amount = orm.SuperDecimalProperty('4', required=True, indexed=False)
  carriers = orm.SuperVirtualKeyProperty('5', kind='113', repeated=True, indexed=False)
  product_categories = orm.SuperKeyProperty('6', kind='24', repeated=True, indexed=False)
  address_type = orm.SuperStringProperty('7', required=True, default='billing', choices=['billing', 'shipping'], indexed=False)
  exclusion = orm.SuperBooleanProperty('8', required=True, default=False, indexed=False)
  locations = orm.SuperLocalStructuredProperty(AddressRuleLocation, '9', repeated=True)
  
  def run(self, context):
    if not self.active:
      return # tax is inactive
    self.read() # read locals
    OrderTax = context.models['32']
    order = context._order
    allowed = self.validate_tax(order)
    for line in order._lines.value:
      taxes = line.taxes.value
      if not taxes:
        taxes = []
      for tax in taxes:
        if tax.key_id_str == self.key_id_str:
          tax._state = 'deleted'
      if (self.product_categories and self.product_categories.count(copy_product.category.key)) \
      or (not self.carriers and not self.product_categories):
        if allowed:
          tax_exists = False
          for tax in taxes:
            if tax.key_id_str == self.key_id_str:
              tax._state = None
              tax.name = self.name
              tax.type = self.type
              tax.amount = self.amount
              tax_exists = True
              break
          if not tax_exists:
            taxes.append(OrderTax(id=self.key_id_str, name=self.name, type=self.type, amount=self.amount))
          line.taxes = taxes
    if self.carriers and order.carrier.value:
      taxes = order.carrier.value.taxes.value
      if not taxes:
        taxes = []
      for tax in taxes:
        if tax.key_id_str == self.key_id_str:
          tax._state = 'deleted'
      if self.carriers.count(order.carrier.value.reference) and allowed:
        tax_exists = False
        for tax in taxes:
          if tax.key_id_str == self.key_id_str:
            tax._state = None
            tax.name = self.name
            tax.type = self.type
            tax.amount = self.amount
            tax_exists = True
            break
        if not tax_exists:
          taxes.append(OrderTax(id=self.key_id_str, name=self.name, type=self.type, amount=self.amount))
        order.carrier.value.taxes = taxes

  def validate_tax(self, order):
    address = None
    address_key = '%s_address' % self.address_type
    order_address = getattr(order, address_key)
    order_address = order_address.value
    if order_address is None:
      return False
    buyer_addresses = order.key_parent.get()
    buyer_addresses.read()
    for buyer_address in buyer_addresses.addresses.value:
      if buyer_address.key == order_address.reference:
        address = buyer_address
        break
    if address is None:
      return False
    if self.exclusion:
      # Apply only at the following locations.
      allowed = False
    else:
      # Apply everywhere except at the following locations.
      allowed = True
    if self.locations.value:
      for loc in self.locations.value:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = self.exclusion
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = self.exclusion
            break
        elif not (loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
            allowed = self.exclusion
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
            allowed = self.exclusion
            break
    if allowed:
      # If tax is configured for carriers then check if the order references carrier on which the tax applies.
      if self.carriers:
        allowed = False
        if order.carrier.value and order.carrier.value.reference and order.carrier.value.reference.urlsafe() in [carrier_key.urlsafe() for carrier_key in self.carriers]:
          allowed = True
      # If tax is configured for product categories, then check if the order contains a line which has product category to which the tax applies.
      elif self.product_categories:
        allowed = False
        for line in order._lines.value:
          product = line.product.value
          if self.product_categories.count(product.category.value.key):
            allowed = True
            break
    return allowed


# Not a plugin!
class CarrierLineRule(orm.BaseModel):
  
  _kind = 111
  
  _use_rule_engine = False
  
  condition_type = orm.SuperStringProperty('1', required=True, default='weight', choices=['weight', 'volume', 'weight*volume', 'price', 'quantity'], indexed=False)
  condition_operator = orm.SuperStringProperty('2', required=True, default='=', choices=['==', '>', '<', '>=', '<='], indexed=False)
  condition_value = orm.SuperDecimalProperty('3', required=True, indexed=False)
  price_type = orm.SuperStringProperty('4', required=True, default='fixed', choices=['fixed', 'variable'], indexed=False)
  price_operator = orm.SuperStringProperty('5', required=True, default='weight', choices=['weight', 'volume', 'weight*volume', 'price', 'quantity'], indexed=False)
  price_value = orm.SuperDecimalProperty('6', required=True, indexed=False)
  
  def make_condition(self):
    condition = '%s %s condition_value' % (self.condition_type, self.condition_operator)
    return condition
  
  def make_price_calculator(self):
    price_calculator = ''
    if self.price_type == 'fixed':
      price_calculator = 'price_value'
    if self.price_type == 'variable':
      price_calculator = '%s * price_value' % self.price_operator
    return price_calculator


# Not a plugin!
class CarrierLine(orm.BaseModel):
  
  _kind = 112
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  exclusion = orm.SuperBooleanProperty('3', required=True, default=False)
  locations = orm.SuperLocalStructuredProperty(AddressRuleLocation, '4', repeated=True)
  rules = orm.SuperLocalStructuredProperty(CarrierLineRule, '5', repeated=True)


class Carrier(orm.BaseModel):
  
  _kind = 113
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  lines = orm.SuperLocalStructuredProperty(CarrierLine, '3', repeated=True)
  
  def run(self, context):
    if not self.active:
      return # this is not active carrier
    self.read() # read locals
    ProductInstance = context.models['27']
    OrderCarrier = context.models['123']
    carrier = context.input.get('carrier')
    order = context._order
    valid_lines = []
    for carrier_line in self.lines.value:
      if not carrier_line.active:
        continue # inactive carrier line
      if self.validate_line(carrier_line, order):
        valid_lines.append(carrier_line)
    current_carrier = order.carrier.value
    if len(valid_lines):
      carrier_price = self.calculate_lines(valid_lines, order)
      if 'carriers' not in context.output:
        context.output['carriers'] = []
      if carrier and carrier == self.key:
        order.carrier = OrderCarrier(description=self.name, unit_price=carrier_price, reference=self.key)
      elif not current_carrier:
        set_carrier = OrderCarrier(description=self.name, unit_price=carrier_price, reference=self.key)
        order.carrier = set_carrier
      context.output['carriers'].append({'name': self.name,
                                         'price': carrier_price,
                                         'key': self.key})
  
  def calculate_lines(self, valid_lines, order):
    if not order._lines.value:
      return Decimal('0') # if no lines are present return 0
    total = Decimal('0')
    for line in order._lines.value:
      product = line.product.value
      carrier_lines_prices = []
      for carrier_line in valid_lines:
        rule_line_prices = []
        rules = carrier_line.rules.value
        if rules:
          for rule in carrier_line.rules.value:
            condition = rule.make_condition()
            condition_data = {
              'condition_value': rule.condition_value,
              'weight': order._total_weight,
              'volume': order._total_volume,
              'price': order.total_amount,
              'quantity': order._total_quantity,
            }
            if safe_eval(condition, condition_data):
              price_calculation = rule.make_price_calculator()
              price_data = {
                'weight': product.weight * product.quantity,
                'volume': product.volume * product.quantity,
                'quantity': product.quantity,
                'price_value': rule.price_value,
              }
              price = safe_eval(price_calculation, price_data)
              rule_line_prices.append(price)
        else:
          rule_line_prices.append(Decimal('0'))
        carrier_lines_prices.append(min(rule_line_prices))
      total = total + min(carrier_lines_prices)  # Return the lowest price possible of all lines!
    return total
    
  
  def validate_line(self, carrier_line, order):
    address = None
    order_address = getattr(order, 'shipping_address')
    order_address = order_address.value
    if order_address is None:
      return False
    buyer_addresses = order.parent_entity
    if buyer_addresses:
      buyer_addresses.read()
      for buyer_address in buyer_addresses.addresses.value:
        if buyer_address.key == order_address.reference:
          address = buyer_address
          break
    if address is None:
      return False
    if carrier_line.exclusion:
      # Apply only at the following locations.
      allowed = False
    else:
      # Apply everywhere except at the following locations.
      allowed = True
    if carrier_line.locations.value:
      for loc in carrier_line.locations.value:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = carrier_line.exclusion
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = carrier_line.exclusion
            break
        elif not (loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
            allowed = carrier_line.exclusion
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
            allowed = carrier_line.exclusion
            break
    else:
      allowed = True # if no locations were defined for the specific rule, then its always considered truthly
    if allowed:
      allowed = False
      if carrier_line.rules.value:
        for rule in carrier_line.rules.value:
          condition = rule.make_condition()
          condition_data = {
            'condition_value': rule.condition_value,
            'weight': order._total_weight,
            'volume': order._total_volume,
            'price': order.total_amount,
            'quantity': order._total_quantity,
          }
          if safe_eval(condition, condition_data):
            allowed = True
            break
      else:
        allowed = True # if no rules were provided, its considered truthly
    return allowed


class OrderProcessPayment(orm.BaseModel):
  
  _kind = 118
  
  def run(self, context):
    order = getattr(self, 'find_order_%s' % context.input.get('payment_method'))(context) # will throw an error if the payment method does not exist
    context._order = order
    order.read({'_lines': {'config': {'search': {'options': {'limit': 0}}}}, '_payment_method': {}})
    payment_plugin = order._payment_method
    if not payment_plugin:
      raise PluginError('no_payment_method_supplied') # @todo generally payment method should always be present
    # payment_plugin => Instance of PaypalPayment for example.
    payment_plugin.complete(context)

  def find_order_paypal(self, context):
    ipn = context.input['request']['params']
    order_key = orm.SuperKeyProperty(kind='34').value_format(ipn['custom'])
    return order_key.get()


class SetMessage(orm.BaseModel):
  
  _kind = 119
  
  def run(self, context):
    OrderMessage = context.models['35']
    # this could be extended to allow params
    context._order._messages = [OrderMessage(agent=context.account.key, _agent=context.account, body=context.input['message'], action=context.action.key)]
