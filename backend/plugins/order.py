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
    self.message = plugin_error


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
      seller_key = product.parent().parent() # go 2 levels up, account->seller->catalog->product
    order = Order.query(Order.seller_reference == seller_key,
                        Order.state.IN(['cart', 'checkout', 'processing']),
                        ancestor=context.input.get('buyer')).get()  # we will need composite index for this
    if order is None:
      order = Order(parent=context.input.get('buyer'), name='Default Order Name') # we need a name for this
      order.state = 'cart'
      order.date = datetime.datetime.now()
      order.seller_reference = seller_key
      seller = seller_key.get()
      seller.read() # read locals
      order.seller_address = get_location(seller.address.value)
    else:
      order.read({'_lines' : {'config' : {'limit': -1}}})  # @todo It is possible that we will have to read more stuff here.
    context._order = order


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
class ProductToOrderLine(orm.BaseModel):
  
  _kind = 101
  
  _use_rule_engine = False
  
  def run(self, context):
    order = context._order
    product_key = context.input.get('product')
    if order.state != 'cart':
      raise PluginError('order_not_in_cart_state')
    variant_signature = context.input.get('variant_signature')
    line_exists = False
    if order._lines.value:
      for line in order._lines.value:
        if hasattr(line, 'product_reference') and line.product_reference == product_key \
        and line.product_variant_signature == variant_signature:
          line._state = 'modified'
          line.quantity = line.quantity + format_value('1', line.product_uom.value)
          line_exists = True
          break
    if not line_exists:
      ProductInstance = context.models['27']
      Line = context.models['33']
      product = product_key.get()
      product.read({'_product_category': {}})  # more fields probably need to be specified
      product_instance_key = ProductInstance.prepare_key(context.input, parent=product_key)
      product_instance = product_instance_key.get()
      new_line = Line()
      new_line.sequence = 0
      if order._lines.value:
        new_line.sequence = order._lines.value[-1].sequence + 1
      new_line.description = product.name
      new_line.product_reference = product_key
      new_line.product_variant_signature = variant_signature
      new_line.product_category_complete_name = product._product_category.value.complete_name
      new_line.product_category_reference = product.product_category
      new_line.code = product.code
      new_line.unit_price = product.unit_price
      new_line.product_uom = copy.deepcopy(product.product_uom.get())
      new_line.quantity = format_value('1', new_line.product_uom.value)
      new_line.discount = format_value('0', Unit(digits=4))
      if product_instance is not None:
        if hasattr(product_instance, 'unit_price'):
          new_line.unit_price = product_instance.unit_price
        if hasattr(product_instance, 'code'):
          new_line.code = product_instance.code
      lines = order._lines.value
      if lines is None:
        lines = []
      lines.append(new_line)
      order._lines = lines
      

class ProductSpecs(orm.BaseModel):
  
  _kind = 115
  
  _use_rule_engine = False
  
  def run(self, context):
    ProductInstance = context.models['27']
    order = context._order
    for line in order._lines.value:
      line._weight = None
      line._weight_uom = None
      line._volume = None
      line._volume_uom = None
      product = line.product_reference.get()
      if hasattr(product, 'weight'):
        line._weight = product.weight
        line._weight_uom = product.weight_uom.get()
      if hasattr(product, 'volume'):
        line._volume = product.volume
        line._volume_uom = product.volume_uom.get()
      if line.product_variant_signature:
        product_instance_key = ProductInstance.prepare_key({'variant_signature': line.product_variant_signature}, parent=line.product_reference)
        product_instance = product_instance_key.get()
        if product_instance is not None:
          if hasattr(product_instance, 'weight'):
            line._weight = product_instance.weight
            line._weight_uom = product_instance.weight_uom.get()
          if hasattr(product_instance, 'volume'):
            line._volume = product_instance.volume
            line._volume_uom = product_instance.volume_uom.get()


# This is system plugin, which means end user can not use it!
class OrderLineFormat(orm.BaseModel):
  
  _kind = 104
  
  _use_rule_engine = False
  
  def run(self, context):
    order = context._order
    for line in order._lines.value:
      if hasattr(line, 'product_reference'):
        if order.seller_reference._root != line.product_reference._root:
          raise PluginError('product_does_not_bellong_to_seller')
        line.discount = format_value(line.discount, Unit(digits=4))
        if line.quantity <= Decimal('0'):
          line._state = 'deleted'
        else:
          line.quantity = format_value(line.quantity, line.product_uom.value)
        line.subtotal = format_value((line.unit_price * line.quantity), order.currency.value)
        line.discount_subtotal = format_value((line.subtotal - (line.subtotal * line.discount)), order.currency.value)
        line.total = format_value(line.discount_subtotal, order.currency.value)
        tax_subtotal = format_value('0', order.currency.value)
        if line.taxes.value:
          for tax in line.taxes.value:
            if (tax.type == 'percent'):
              tax_amount = format_value(tax.tax_amount, Unit(digits=4)) * format_value('0.01', Unit(digits=4))  # or "/ DecTools.form('100')"  @todo Using fixed formating here, since it's the percentage value, such as 17.00%.
              tax_subtotal = tax_subtotal + (line.total * tax_amount)
            elif (tax.type == 'fixed'):
              tax_amount = format_value(tax.tax_amount, order.currency.value)
              tax_subtotal = tax_subtotal + tax_amount
        line.tax_subtotal = tax_subtotal


# This is system plugin, which means end user can not use it!
class OrderFormat(orm.BaseModel):
  
  _kind = 105
  
  _use_rule_engine = False
  
  # @todo We need receivable calcualtior as well!
  def run(self, context):
    order = context._order
    untaxed_amount = format_value('0', order.currency.value)
    tax_amount = format_value('0', order.currency.value)
    total_amount = format_value('0', order.currency.value)
    for line in order._lines.value:
      if hasattr(line, 'product_reference'):
        untaxed_amount = untaxed_amount + line.subtotal
        tax_amount = tax_amount + line.tax_subtotal
        total_amount = total_amount + (line.subtotal + line.tax_subtotal) # we cannot use += for decimal its not supported
    order.untaxed_amount = format_value(untaxed_amount, order.currency.value)
    order.tax_amount = format_value(tax_amount, order.currency.value)
    order.total_amount = format_value(total_amount, order.currency.value)


# Not a plugin!
class AddressRuleLocation(orm.BaseModel):
  
  _kind = 106
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  country = orm.SuperKeyProperty('3', kind='15', required=True, indexed=False)
  region = orm.SuperKeyProperty('4', kind='16', indexed=False)
  postal_code_from = orm.SuperStringProperty('5', indexed=False)
  postal_code_to = orm.SuperStringProperty('6', indexed=False)
  city = orm.SuperStringProperty('7', indexed=False)


class AddressRule(orm.BaseModel):
  
  _kind = 107
  
  _use_rule_engine = False
  
  exclusion = orm.SuperBooleanProperty('1', required=True, default=False, indexed=False)
  address_type = orm.SuperStringProperty('2', required=True, default='billing', choices=['billing', 'shipping'], indexed=False)
  locations = orm.SuperLocalStructuredProperty(AddressRuleLocation, '3', repeated=True, indexed=False)
  
  def run(self, context):
    self.read() # read locals
    order = context._order
    valid_addresses = collections.OrderedDict()
    default_address = None
    address_reference_key = '%s_address_reference' % self.address_type
    address_key = '%s_address' % self.address_type
    addresses_key = '%s_addresses' % self.address_type
    default_address_key = 'default_%s' % self.address_type
    input_address_reference = context.input.get(address_reference_key)
    order_address_reference = getattr(order, address_reference_key, None)
    buyer_addresses = order.key_parent.get()
    buyer_addresses.read() # read locals
    if buyer_addresses is None:
      raise PluginError('no_address')
    for buyer_address in buyer_addresses.addresses.value:
      if self.validate_address(buyer_address):
        valid_addresses[buyer_address.key.urlsafe()] = buyer_address
        if getattr(buyer_address, default_address_key):
          default_address = buyer_address
    if not len(valid_addresses):
      raise PluginError('no_valid_address')
    context.output[addresses_key] = valid_addresses
    if (default_address is None) and len(valid_addresses):
      default_address = valid_addresses.values()[0]
    if input_address_reference in valid_addresses:
      default_address = valid_addresses[input_address_reference]
    elif order_address_reference in valid_addresses:
      default_address = valid_addresses[order_address_reference]
    if default_address:
      setattr(order, address_reference_key, default_address.key)
      setattr(order, address_key, get_location(default_address))
      context.output[default_address_key] = default_address
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


# This plugin is incomplete!
class PayPalPayment(orm.BaseModel):
  
  _kind = 108
  
  _use_rule_engine = False
  
  # This plugin will be subscribed to many actions, among which is add_to_cart as well.
  # PayPal Shipping: Prompt for an address, but do not require one,
  # PayPal Shipping: Do not prompt for an address
  # PayPal Shipping: Prompt for an address, and require one
  
  currency = orm.SuperKeyProperty('1', kind=Unit, required=True, indexed=False)
  reciever_email = orm.SuperStringProperty('2', required=True, indexed=False)
  business = orm.SuperStringProperty('3', required=True, indexed=False)
  
  def run(self, context):
    order = context._order
    # In context of add_to_cart action runner does the following:
    order.currency = copy.deepcopy(self.currency.get())
    order.paypal_reciever_email = self.reciever_email
    order.paypal_business = self.business


# This plugin is incomplete!
class Tax(orm.BaseModel):
  
  _kind = 109
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  code = orm.SuperStringProperty('3', required=True, indexed=False)  # @todo Not sure if we need this!
  type = orm.SuperStringProperty('4', required=True, default='percent', choices=['percent', 'fixed'], indexed=False)
  amount = orm.SuperDecimalProperty('5', required=True, indexed=False)
  exclusion = orm.SuperBooleanProperty('6', required=True, default=False, indexed=False)
  address_type = orm.SuperStringProperty('7', required=True, default='billing', choices=['billing', 'shipping'], indexed=False)
  locations = orm.SuperLocalStructuredProperty(AddressRuleLocation, '8', repeated=True)  # @todo AddressRuleLocation or what?
  carriers = orm.SuperKeyProperty('9', kind='113', repeated=True, indexed=False)
  product_categories = orm.SuperKeyProperty('10', kind='24', repeated=True, indexed=False)
  
  def run(self, context):
    self.read() # read locals
    order = context._order
    allowed = self.validate_tax(order)
    for line in order._lines.value:
      taxes = line.taxes.value
      if not taxes:
        taxes = []
      for tax in taxes:
        if tax.key == self.key:
          tax._state = 'deleted'
      if (self.carriers and self.carriers.count(line.carrier_reference)) \
      or (self.product_categories and self.product_categories.count(line.product_category)):  # @todo Have to check if all lines have carrier_reference property??
        if allowed:
          tax_exists = False
          for tax in taxes:
            if tax._state == 'deleted':
              continue
            if tax.key == self.key:
              tax._state = 'modified'
              tax.name = self.name
              tax.code = self.code
              tax.type = self.type
              tax.amount = self.amount
              tax_exists = True
              break
          if not tax_exists:
            taxes.append(order.OrderLineTax(key=self.key, name=self.name, code=self.code, tax_type=self.tax_type, tax_amount=self.tax_amount))
            line.taxes = taxes
  
  def validate_tax(self, order):
    address = None
    address_reference_key = '%s_address_reference' % self.address_type
    order_address_reference = getattr(order, address_reference_key, None)
    if order_address_reference is None:
      return False
    buyer_addresses = order.key_parent.get()
    buyer_addresses.read()
    for buyer_address in buyer_addresses.addresses.value:
      if buyer_address.key == order_address_reference:
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
        if order.carrier_reference and order.carrier_reference.urlsafe() in [carrier.key.urlsafe() for carrier in self.carrieres.value]:
          allowed = True
      # If tax is configured for product categories, then check if the order contains a line which has product category to which the tax applies.
      elif self.product_categories:
        allowed = False
        for line in order._lines.value:
          if self.product_categories.count(line.product_category):
            allowed = True
            break
    return allowed


# Not a plugin!
class CarrierLineRule(orm.BaseModel):
  
  _kind = 111
  
  _use_rule_engine = False
  
  condition_type = orm.SuperStringProperty('1', required=True, default='weight', choices=['weight', 'volume', 'weight*volume', 'price', 'quantity'], indexed=False)
  condition_operator = orm.SuperStringProperty('2', required=True, default='=', choices=['=', '>', '<', '>=', '<='], indexed=False)
  condition_value = orm.SuperDecimalProperty('3', required=True, indexed=False)
  price_type = orm.SuperStringProperty('4', required=True, default='fixed', choices=['fixed', 'variable'], indexed=False)
  price_operator = orm.SuperStringProperty('5', required=True, default='weight', choices=['weight', 'volume', 'weight*volume', 'price', 'quantity'], indexed=False)
  price_value = orm.SuperDecimalProperty('5', required=True, indexed=False)
  
  def make_condition(self):
    condition = '%s %s condition_value' % (self.condition_type, self.condition_operator)
    return condition
  
  def make_price_calculator(self):
    price_calculator = ''
    if self.price_type == 'fixed':
      price_calculator = 'price'
    if self.price_type == 'variable':
      price_calculator = '%s * price' % self.price_operator
    return price_calculator


# Not a plugin!
class CarrierLine(orm.BaseModel):
  
  _kind = 112
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  exclusion = orm.SuperBooleanProperty('3', required=True, default=False)
  locations = orm.SuperLocalStructuredProperty(Location, '4', repeated=True)
  rules = orm.SuperLocalStructuredProperty(CarrierLineRule, '5', repeated=True)


# This plugin is incomplete!
class Carrier(orm.BaseModel):
  
  _kind = 113
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  lines = orm.SuperLocalStructuredProperty(CarrierLine, '2', repeated=True)
  
  def run(self, context):
    self.read() # read locals
    ProductInstance = context.models['27']
    order = context._order
    valid_lines = []
    for carrier_line in self.lines.value:
      if self.validate_line(carrier_line, order):
        valid_lines.append(carrier_line)
    if len(valid_lines):
      carrier_price = self.calculate_lines(valid_lines, order)
      if 'carriers' not in context.output:
        context.output['carriers'] = []
      context.output['carriers'].append({'name': self.name,
                                         'price': carrier_price,
                                         'key': self.key.urlsafe()})
 
  
  def calculate_lines(self, valid_lines, order):
    weight_uom = Unit.build_key('kilogram').get()
    volume_uom = Unit.build_key('cubic_meter').get()
    weight = format_value('0', weight_uom)
    volume = format_value('0', volume_uom)
    for line in order._lines.value:
      product = line.product_reference.get()
      line_weight = line._weight
      line_weight_uom = line._weight_uom
      line_volume = line._volume
      line_volume_uom = line._volume_uom
      weight = weight + convert_value(line_weight, line_weight_uom, weight_uom)
      volume = volume + convert_value(line_volume, line_volume_uom, volume_uom)
      carrier_prices = []
      for carrier_line in valid_lines:
        line_prices = []
        rules = carrier_line.rules.value
        if rules:
          for rule in carrier_line.rules.value:
            condition = rule.make_condition()
            price = rule.price_value
            if safe_eval(condition, {'weight': weight, 'condition_value': rule.condition_value, 'volume': volume, 'price': price}):
              price_calculation = rule.make_price_calculator()
              price = safe_eval(price_calculation, {'weight': weight, 'volume': volume, 'price': price})
              line_prices.append(price)
        carrier_prices.append(min(line_prices))
      return min(carrier_prices)  # Return the lowest price possible of all lines!
    
  
  def validate_line(self, carrier_line, order):
    address = None
    order_address_reference = getattr(order, 'shipping_address_reference', None)
    if order_address_reference is None:
      return False
    buyer_addresses = order.parent_entity
    if buyer_addresses:
      buyer_addresses.read()
      for buyer_address in buyer_addresses.addresses.value:
        if buyer_address.key == order_address_reference:
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
    if allowed:
      allowed = False
      price = order.total_amount
      weight_uom = Unit.build_key('kilogram').get()
      volume_uom = Unit.build_key('cubic_meter').get()
      weight = format_value('0', weight_uom)
      volume = format_value('0', volume_uom)
      for line in order._lines.value:
        line_weight = line._weight
        line_weight_uom = line._weight_uom
        line_volume = line._volume
        line_volume_uom = line._volume_uom
        weight = weight + convert_value(line_weight, line_weight_uom, weight_uom)
        volume = volume + convert_value(line_volume, line_volume_uom, volume_uom)
      for rule in carrier_line.rules.value:
        condition = rule.make_condition()
        if safe_eval(condition, {'weight': weight, 'condition_value': rule.condition_value, 'volume': volume, 'price': price}):
          allowed = True
          break
    return allowed


# OLD CODE #


class PayPalInit(orm.BaseModel):
  
  # user plugin, saved in datastore
  
  def run(self, journal, context):
    
    ipns = log.Record.query(orm.GenericProperty('ipn_txn_id') == context.input['txn_id']).fetch()
    if len(ipns):
      for ipn in ipns:
        if (ipn.payment_status == context.input['payment_status']):
          raise orm.PluginValidationError('duplicate_entry')
      entry = ipns[0].parent_entity
      if context.input['custom']:
         if (entry.key.urlsafe() == context.input['custom']):
           
            kwds = {'log_entity' : False}
            kwds.update(dict([('ipn_%s' % key, value) for key,value in context.input.items()])) # prefix
            context.log.entities.append((entry, kwds))
            
         else:
            raise orm.PluginValidationError('invalid_ipn')
      else:
        raise orm.PluginValidationError('invalid_ipn')
      
    else:    
      
      if not context.input['custom']:
        raise orm.PluginValidationError('invalid_ipn')
      else:
        try:
          entry_key = orm.Key(urlsafe=context.input['custom']) 
          entry = entry_key.get()
        except Exception as e:
          raise orm.PluginValidationError('invalid_ipn')
        
    if not entry:
      raise orm.PluginValidationError('invalid_ipn')
    
    kwds = {'log_entity' : False}
    kwds.update(dict([('ipn_%s' % key, value) for key,value in context.input.items()])) # prefix
    context.log.entities.append((entry, kwds))
    
    if not context.transaction.group:
       context.transaction.group = entry.parent_entity
       
    context.transaction.entities[journal.key.id()] = entry
    
    if not self.validate_entry(entry, context):
       raise orm.PluginValidationError('fraud_check')
     
    if (entry.paypal_payment_status == context.input['payment_status']):
        return None
      
    update_paypal_payment_status = False  
      
    if (entry.paypal_payment_status == 'Pending'):
        if (context.input['payment_status'] == 'Completed' or context.input == 'Denied'):
            update_paypal_payment_status = True
    elif (entry.paypal_payment_status == 'Completed'):
        if (context.input['payment_status'] == 'Refunded' or context.input['payment_status'] == 'Reversed'):
            update_paypal_payment_status = True
            
    if (update_paypal_payment_status):
        # ovo se verovatno treba jos doterati..
        if (entry.state == 'processing' and context.input['payment_status'] == 'Completed'):
            entry.state = 'completed'
            entry.paypal_payment_status = context.input['payment_status']
            context.log.entities.append((entry,))
        elif (entry.state == 'processing' and context.input['payment_status'] == 'Denied'): # ovo cemo jos da razmotrimo
            entry.state = 'canceled'
            entry.paypal_payment_status = context.input['payment_status']
            context.log.entities.append((entry,))
        elif (entry.state == 'completed'):
            entry.paypal_payment_status = context.input['payment_status']
            context.log.entities.append((entry,))
    
  def validate_entry(self, entry, context):
      
      mismatches = []
      ipn = context.input
      shipping_address = entry.shipping_address
 
      if (entry.paypal_receiver_email != ipn['receiver_email']):
          mismatches.append('receiver_email')
      if (entry.paypal_business != ipn['business']):
          mismatches.append('business_email')
      if (entry.currency.code != ipn['mc_currency']):
          mismatches.append('mc_currency')
      if (entry.total_amount != uom.format_value(ipn['mc_gross'], entry.currency)):
          mismatches.append('mc_gross')
      if (entry.tax_amount != uom.format_value(ipn['tax'], entry.currency)):
          mismatches.append('tax')
          
      if (entry.name != ipn['invoice']): # entry.reference bi mozda mogao da bude user.key.id-entry.key.id ili mozda entry.key.id ?
          mismatches.append('invoice')
      
      if (shipping_address.country != ipn['address_country']):
          mismatches.append('address_country')    
      if (shipping_address.country_code != ipn['address_country_code']):
          mismatches.append('address_country_code')
      if (shipping_address.city != ipn['address_city']):
          mismatches.append('address_city')
      if (shipping_address.name != ipn['address_name']):
          mismatches.append('address_name')
      
      state = shipping_address.region # po defaultu sve ostale drzave koriste name? ili i one isto kod?
      if shipping_address.country_code == 'US': # paypal za ameriku koristi 2 digit iso standard kodove za njegove stateove
         state = shipping_address.region_code
         
      if (state != ipn['address_state']):
          mismatches.append('address_state')
      if (shipping_address.street != ipn['address_street']): 
          # PayPal spaja vrednosti koje su prosledjene u cart upload procesu (address1 i address2), 
          # tako da u povratu putem IPN-a, polje address_street izgleda ovako address1\r\naddress2. 
          # Primer: u'address_street': [u'1 Edi St\r\nApartment 7'], gde je vrednost Street Address 
          # od kupca bilo "Edi St", a vrednost Street Address (Optional) "Apartment 7".
          mismatches.append('address_street')
      if (shipping_address.postal_code != ipn['address_zip']):
          mismatches.append('address_zip')
          
      for line in entry._lines:
          if (line.code != ipn['item_number%s' % str(line.sequence)]): # ovo nije u order funkcijama implementirano tako da ne znamo da li cemo to imati..
              mismatches.append('item_number%s' % str(line.sequence))
          if (line.description != ipn['item_name%s' % str(line.sequence)]):
              mismatches.append('item_name%s' % str(line.sequence))
          if (line.quantity != uom.format_value(ipn['quantity%s' % str(line.sequence)], line.product_uom)):
              mismatches.append('quantity%s' % str(line.sequence))
          if ((line.subtotal + line.tax_subtotal) != uom.format_value(ipn['mc_gross%s' % str(line.sequence)], entry.currency)):
              mismatches.append('mc_gross%s' % str(line.sequence))
      # Ukoliko je doslo do fail-ova u poredjenjima
      # radi se dispatch na notification engine sa detaljima sta se dogodilo, radi se logging i algoritam se prekida.
      if not mismatches:
         return True
      else:
         return False
