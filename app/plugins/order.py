# -*- coding: utf-8 -*-
'''
Created on Aug 25, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime
import collections
import re

from app import orm
from app.tools.base import *
from app.util import *
from app.models import location, uom  # transaction, rule, log


# Virtual representation of order entry object to serve as a reference of expected structure (will be removed later)!
# Regarding the structured properties in entries and lines, shall we standardize thos properties to be JSON and transform data apropriately on input?
class OrderEntry(orm.BaseExpando):
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  journal = orm.SuperKeyProperty('3', kind=Journal, required=True)
  name = orm.SuperStringProperty('4', required=True)
  state = orm.SuperStringProperty('5', required=True)
  date = orm.SuperDateTimeProperty('6', required=True)
  company_address = orm.SuperLocalStructuredProperty(location.Location, '7', required=True)
  party = orm.SuperKeyProperty('8', kind=auth.User, required=True)
  billing_address_reference = orm.SuperStringProperty('9', required=True)
  shipping_address_reference = orm.SuperStringProperty('10', required=True)
  billing_address = orm.SuperLocalStructuredProperty(location.Location, '11', required=True)
  shipping_address = orm.SuperLocalStructuredProperty(location.Location, '12', required=True)
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('47', 'add_to_cart'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          name='Init'
          plugins=[
            Context(),
            CartInit()
            ]
          ),
        orm.PluginGroup(
          name='Payment Config'  # User Editable
          plugins=[
            PayPalPayment()
            ]
          ),
        orm.PluginGroup(
          name='Lines Init'
          plugins=[
            LinesInit()
            ]
          ),
        orm.PluginGroup(
          name='Address Rules'  # User Editable
          plugins=[
            AddressRule()
            ]
          ),
        orm.PluginGroup(
          name='Taxes'  # User Editable
          plugins=[
            Tax()
            ]
          ),
        orm.PluginGroup(
          name='Carriers'  # User Editable
          plugins=[
            Carrier()
            ]
          ),
        orm.PluginGroup(
          name='Final'
          plugins=[
            ProductToLine(),
            ProductSubtotalCalculate(),
            TaxSubtotalCalculate(),
            OrderTotalCalculate()
            ]
          ),
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'update'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            ]
          ),
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'checkout'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            ]
          ),
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'cancel'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            ]
          ),
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'pay'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            ]
          ),
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'timeout'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            ]
          ),
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'complete'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            ]
          ),
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('47', 'message'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            ]
          ),
        ]
      )
    ]


# @todo Not sure if we are gonna use this instead of orm.ActionDenied()? ActionDenied lacks descreptive messaging!
class PluginError(Exception):
  
  def __init__(self, plugin_error):
    self.message = plugin_error


# This is system plugin, which means end user can not use it!
class CartInit(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  def run(self, context):
    catalog_key = context.input.get('catalog')
    catalog = catalog_key.get()
    user_key = context.user.key()
    Group = context.models['48']
    Entry = context.models['50']
    entry = Entry.query(Entry.journal == context.model.journal,
                        Entry.party == user_key,
                        Entry.state.IN(['cart', 'checkout', 'processing']),
                        namespace=context.model.journal._namespace).get()
    if entry is None:
      entry = Entry()
      entry.set_key(None, namespace=context.model.journal._namespace)
      entry.journal = context.model.journal
      entry.company_address = # Source of company address required!
      entry.state = 'cart'
      entry.date = datetime.datetime.now()
      entry.party = user_key
      context._group = Group()
    else:
      entry.read(read_arguments)  # @todo What read arguments do we put here? We surely need entry._lines loaded.
      context._group = entry.parent_entity
    context._group.insert_entry(entry)
    if entry.state != 'cart':
      raise orm.ActionDenied(context.action)  # @todo Replace with raise PluginError('entry_not_in_cart_state')!?


# This is system plugin, which means end user can not use it!
class LinesInit(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    Category = context.models['47']
    Line = context.models['51']
    receivable_line = Line(sequence=0, uom=entry.currency, description='Accounts Receivable',
                           debit=format_value('0', entry.currency), credit=format_value('0', entry.currency),
                           categories=[Category.build_key('1102', namespace=context.model.journal._namespace)])  # Debtors (1102) account.
    tax_line = Line(sequence=1, uom=entry.currency, description='Sales Tax',
                    debit=format_value('0', entry.currency), credit=format_value('0', entry.currency),
                    categories=[Category.build_key('121', namespace=context.model.journal._namespace)])  # Tax Received (121) account.
    if len(entry._lines) == 0:
      entry._lines = [receivable_line, tax_line]


# This is system plugin, which means end user can not use it!
class ProductToLine(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    product_key = context.input.get('product')
    variant_signature = context.input.get('variant_signature')
    line_exists = False
    for line in entry._lines:
      if hasattr(line, 'product_reference')
      and line.product_reference == product_key
      and line.product_variant_signature == variant_signature:
        line.quantity = line.quantity + format_value('1', line.product_uom)
        line_exists = True
        break
    if not line_exists:
      ProductInstance = context.models['39']
      Category = context.models['47']
      Line = context.models['51']
      product = product_key.get()
      product_instance_key = ProductInstance.prepare_key(context.input, parent=product_key)
      product_instance = product_instance_key.get()
      new_line = Line()
      new_line.sequence = entry._lines[-1].sequence + 1
      new_line.categories = [Category.build_key('200', namespace=context.model.journal._namespace)]  # Product Sales (200) account.
      new_line.uom = entry.currency
      new_line.product_reference = product_key
      new_line.product_variant_signature = variant_signature
      new_line.product_category_complete_name = product._product_category.complete_name
      new_line.product_category_reference = product.product_category
      new_line.description = product.name
      new_line.code = product.code
      new_line.unit_price = product.unit_price
      new_line.product_uom = uom.get_uom(product.product_uom)  # @todo Where is get_uom function? We lost it somewhere!
      new_line.quantity = format_value('1', new_line.product_uom)
      new_line.discount = format_value('0', uom.UOM(digits=4))
      if hasattr(product, 'weight'):
        new_line._weight = product.weight  # @todo Perhaps we might need to build these fields during certain actions, and not only while adding new lines (to ensure thir life accros carrier plugins)!
      if hasattr(product, 'volume'):
        new_line._volume = product.volume
      if product_instance is not None:
        if hasattr(product_instance, 'unit_price'):
          new_line.unit_price = product_instance.unit_price
        if hasattr(product_instance, 'code'):
          new_line.code = product_instance.code
        if hasattr(product_instance, 'weight'):
          new_line._weight = product_instance.weight
        if hasattr(product_instance, 'volume'):
          new_line._volume = product_instance.volume
      entry._lines.append(new_line)


# This is system plugin, which means end user can not use it!
# @todo Not sure if need this plugin, since we have field level rule engine, which would be capable of controling which field can be edited!?
class UpdateProductLine(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    delete_lines = []
    quantity = context.input.get('quantity')
    discount = context.input.get('discount')
    for i, line in enumerate(entry._lines):
      if hasattr(line, 'product_reference'):
        if quantity is not None:
          if quantity[i] <= 0:
            delete_lines.append(i)
          else:
            line.quantity = format_value(quantity[i], line.product_uom)
        if discount is not None:
          line.discount = format_value(discount[i], uom.UOM(digits=4))
    for line in delete_lines:
      entry._lines.pop(line)


# This is system plugin, which means end user can not use it!
class EntryFieldAutoUpdate(transaction.Plugin):
  
  _kind = xx
  
  _use_rule_engine = False
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    static_values = self.cfg.get('s', {})
    dynamic_values = self.cfg.get('d', {})
    remove_values = self.cfg.get('rm', [])
    entry = context._group.get_entry(context.model.journal)
    for key, value in static_values.iteritems():
      set_attr(entry, key, value)
    for key, value in dynamic_values.iteritems():
      set_value = get_attr(context, value, Nonexistent)
      if set_value is not Nonexistent:
        set_attr(entry, key, set_value)
    for key in remove_values:
      del_attr(entry, key)


# This is system plugin, which means end user can not use it!
class ProductSubtotalCalculate(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    for line in entry._lines:
      if hasattr(line, 'product_reference'):
        line.subtotal = format_value((line.unit_price * line.quantity), line.uom)  # @todo Is this ok!?
        line.discount_subtotal = format_value((line.subtotal - (line.subtotal * line.discount)), line.uom) # @todo Is this ok!?
        line.debit = format_value('0', line.uom)
        line.credit = format_value(line.discount_subtotal, line.uom)  # @todo Is this ok!?


# This is system plugin, which means end user can not use it!
class OrderTotalCalculate(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  # @todo We need receivable calcualtior as well!
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    untaxed_amount = format_value('0', entry.currency)
    tax_amount = format_value('0', entry.currency)
    total_amount = format_value('0', entry.currency)
    for line in entry._lines:
      if hasattr(line, 'product_reference'):
        untaxed_amount += line.subtotal
        tax_amount += line.tax_subtotal
        total_amount += line.subtotal + line.tax_subtotal
    entry.untaxed_amount = format_value(untaxed_amount, entry.currency)
    entry.tax_amount = format_value(tax_amount, entry.currency)
    entry.total_amount = format_value(total_amount, entry.currency)


# Not a plugin!
class Location(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  country = orm.SuperKeyProperty('1', kind='15', required=True, indexed=False)
  region = orm.SuperKeyProperty('2', kind='16', indexed=False)
  postal_code_from = orm.SuperStringProperty('3', indexed=False)
  postal_code_to = orm.SuperStringProperty('4', indexed=False)
  city = orm.SuperStringProperty('5', indexed=False)
  
  # @todo Do we need __init__ at all!?
  def __init__(self, *args, **kwargs):
    super(Address, self).__init__(**kwargs)
    if len(args):
      country, region, postal_code_from, postal_code_to, city = args
      self.country = country
      self.region = region
      self.postal_code_from = postal_code_from
      self.postal_code_to = postal_code_to
      self.city = city


class AddressRule(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  exclusion = orm.SuperBooleanProperty('1', required=True, default=False)
  address_type = orm.SuperStringProperty('2', required=True, default='billing', choices=['billing', 'shipping'])
  locations = orm.SuperLocalStructuredProperty(Location, '3', repeated=True)
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    valid_addresses = collections.OrderedDict()
    default_address = None
    address_reference_key = '%s_address_reference' % self.address_type
    address_key = '%s_address' % self.address_type
    addresses_key = '%s_addresses' % self.address_type
    default_address_key = 'default_%s' % self.address_type
    input_address_reference = context.input.get(address_reference_key)
    entry_address_reference = getattr(entry, address_reference_key, None)
    buyer_addresses = orm.Key('77', entry.partner._id_str, parent=entry.partner).get()
    if buyer_addresses is None:
      raise orm.ActionDenied(context.action)  # @todo Replace with raise PluginError('no_address')!?
    for buyer_address in buyer_addresses.addresses:
      if self.validate_address(buyer_address):
        valid_addresses[buyer_address.internal_id] = buyer_address
        if getattr(buyer_address, default_address_key):
          default_address = buyer_address
    if not len(valid_addresses):
      raise orm.ActionDenied(context.action)  # @todo Replace with raise PluginError('no_valid_address')!?
    context.output[addresses_key] = valid_addresses
    if (default_address is None) and len(valid_addresses):
      default_address = valid_addresses.values()[0]
    if input_address_reference in valid_addresses:
      default_address = valid_addresses[input_address_reference]
    elif entry_address_reference in valid_addresses:
      default_address = valid_addresses[entry_address_reference]
    if default_address:
      setattr(entry, address_reference_key, default_address.internal_id)
      setattr(entry, address_key, location.get_location(default_address))
      context.output[default_address_key] = default_address
    else:
      raise orm.ActionDenied(context.action)  # @todo Replace with raise PluginError('no_address_found')!?
  
  def validate_address(self, address):
    if self.exclusion:
      # Shipping only at the following locations.
      allowed = False
    else:
      # Shipping everywhere except at the following locations.
      allowed = True
    for loc in self.locations:
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
  
  _kind = xx
  
  _use_rule_engine = False
  
  # This plugin will be subscribed to many actions, among which is add_to_cart as well.
  # PayPal Shipping: Prompt for an address, but do not require one,
  # PayPal Shipping: Do not prompt for an address
  # PayPal Shipping: Prompt for an address, and require one
  
  currency = orm.SuperKeyProperty('1', kind=uom.Unit)
  reciever_email = orm.SuperStringProperty('2')
  business = orm.SuperStringProperty('3')
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    # In context of add_to_cart action runner does the following:
    entry.currency = uom.get_uom(self.currency)  # @todo Where is get_uom function? We lost it somewhere!
    entry.paypal_reciever_email = self.reciever_email
    entry.paypal_business = self.business


# This plugin is incomplete!
class Tax(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1')
  formula = orm.SuperStringProperty('2')
  exclusion = orm.SuperBooleanProperty('3', required=True, default=False)
  address_type = orm.SuperStringProperty('4', required=True, default='billing', choices=['billing', 'shipping'])
  locations = orm.SuperLocalStructuredProperty(Location, '5', repeated=True)
  carriers = orm.SuperKeyProperty('6', repeated=True)  # @todo This is not possible anymore!
  product_categories = orm.SuperKeyProperty('7', kind='17', repeated=True)  # @todo This is not possible anymore!
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    allowed = self.validate_tax(entry)
    for line in entry._lines:
      if self.carriers:
        if self.carriers.count(line.carrier_reference):  # @todo Have to check if all lines have carrier_reference proeprty??
          if not allowed:
            del line.taxes[self.key.urlsafe()]  # @todo This is not possible anymore!
          elif allowed:
            line.taxes[self.key.urlsafe()] = {'name': self.name, 'formula': self.formula}  # @todo This is not possible anymore! We are using JSON structure here, instead structured proeprty (has to be discussed)!
      elif self.product_categories:
        if self.product_categories.count(line.product_category):
          if not (allowed):
            del line.taxes[self.key.urlsafe()]  # @todo This is not possible anymore!
          elif allowed:
            line.taxes[self.key.urlsafe()] = {'name': self.name, 'formula': self.formula}  # @todo This is not possible anymore! We are using JSON structure here, instead structured proeprty (has to be discussed)!
  
  def validate_tax(self, entry):
    address = None
    address_reference_key = '%s_address_reference' % self.address_type
    entry_address_reference = getattr(entry, address_reference_key, None)
    if entry_address_reference is None:  # @todo Is this ok??
      return False
    buyer_addresses = orm.Key('77', entry.partner._id_str, parent=entry.partner).get()
    for buyer_address in buyer_addresses.addresses:
      if buyer_address.internal_id == entry_address_reference:
        address = buyer_address
        break
    if address is None:  # @todo IS this ok??
      return False
    if self.exclusion:
      # Apply only at the following locations.
      allowed = False
    else:
      # Apply everywhere except at the following locations.
      allowed = True
    for loc in self.locations:
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
    # @todo This block need changes!
    if allowed:
      # If tax is configured for carriers then check if the entry references carrier on which the tax applies.
      if self.carriers:
        allowed = False
        if entry.carrier_reference and self.carrieres.count(entry.carrier_reference):
          allowed = True
      # If tax is configured for product categories, then check if the entry contains a line which has product category to which the tax applies.
      elif self.product_categories:
        allowed = False
        for line in entry._lines:
          if self.product_categories.count(line.product_category):
            allowed = True
            break
    return allowed


# This is system plugin, which means end user can not use it!
class TaxSubtotalCalculate(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    Category = context.models['47']
    Line = context.models['51']
    tax_category_key = Category.build_key('121', namespace=context.model.journal._namespace)  # Tax Received (121) account.
    tax_line = False
    tax_total = format_value('0', entry.currency)
    for line in entry._lines:
      if tax_category_key in line.categories:
        tax_line = line
      tax_subtotal = format_value('0', line.uom)
      for tax_key, tax in line.taxes.items():
        if (tax['formula'][0] == 'percent'):
          tax_amount = format_value(tax['formula'][1], line.uom) * format_value('0.01', line.uom)  # or "/ DecTools.form('100')"
          tax_subtotal += line.credit * tax_amount
          tax_total += line.credit * tax_amount
        elif (tax['formula'][0] == 'amount'):
          tax_amount = format_value(tax['formula'][1], line.uom)
          tax_subtotal += tax_amount
          tax_total += tax_amount
      line.tax_subtotal = tax_subtota
    if tax_line:  # @todo Or we can loop entry._lines again and do the math!
      tax_line.debit = format_value('0', tax_line.uom)
      tax_line.credit = tax_total


# Not a plugin!
class CarrierLineRule(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  condition = orm.SuperStringProperty('1', required=True, indexed=False)
  price = orm.SuperStringProperty('2', required=True, indexed=False)
  
  # @todo Do we need __init__ at all!?
  def __init__(self, *args, **kwargs):
    super(CarrierLineRule, self).__init__(**kwargs)
    if len(args):
      condition, price = args
      self.condition = condition
      self.price = price


# Not a plugin!
class CarrierLine(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  exclusion = orm.SuperBooleanProperty('3', required=True, default=False)
  locations = orm.SuperLocalStructuredProperty(Location, '4', repeated=True)
  rules = orm.SuperLocalStructuredProperty(CarrierLineRule, '5', repeated=True)
  
  # @todo Do we need __init__ at all!?
  def __init__(self, *args, **kwargs):
    super(CarrierLine, self).__init__(**kwargs)
    if len(args):
      name, active, exclusion, locations, rules = args
      self.name = name
      self.active = active
      self.exclusion = exclusion
      self.locations = locations
      self.rules = rules


# This plugin is incomplete!
class Carrier(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  lines = orm.SuperLocalStructuredProperty(CarrierLine, '2', repeated=True)
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    valid_lines = []
    for carrier_line in self.lines:
      if self.validate_line(carrier_line, entry):
        valid_lines.append(carrier_line)
    carrier_price = self.calculate_lines(valid_lines, entry)
    if 'carriers' not in context.output:
      context.output['carriers'] = []
    context.output['carriers'].append({'name': self.name,
                                       'price': carrier_price,
                                       'id': self.key.urlsafe()})
  
  def calculate_lines(self, valid_lines, entry):
    weight_uom = uom.get_uom(uom.Unit.build_key('kg'))  # @todo Where is get_uom function? We lost it somewhere! Also, is the key unique without measurement filtering?
    volume_uom = uom.get_uom(uom.Unit.build_key('m3'))  # @todo Where is get_uom function? We lost it somewhere! Also, is the key unique without measurement filtering?
    weight = format_value('0', weight_uom)
    volume = format_value('0', volume_uom)
    for line in entry._lines:
      line_weight = line._weight[0]
      line_weight_uom = uom.get_uom(ndb.Key(urlsafe=line._weight[1]))
      line_volume = line._volume[0]
      line_volume_uom = uom.get_uom(ndb.Key(urlsafe=line._volume[1]))
      weight += convert_value(line_weight, line_weight_uom, weight_uom)
      volume += convert_value(line_volume, line_volume_uom, volume_uom)
      carrier_prices = []
      for carrier_line in valid_lines:
        line_prices = []
        for rule in carrier_line.rules:
          condition = rule.condition
          # @todo This regex needs more work
          condition = self.format_value(condition)
          price = rule.price
          if safe_eval(condition, {'weight': weight, 'volume': volume, 'price': price}):
            price = self.format_value(price)
            price = safe_eval(price, {'weight': weight, 'volume': volume, 'price': price})
            line_prices.append(price)
        carrier_prices.append(min(line_prices))
      return min(carrier_prices)  # Return the lowest price possible of all lines!
  
  def format_value(self, value):
    def run_format(match):
      matches = match.groups()
      return 'Decimal("%s")' % format_value(matches[0], uom.get_uom(ndb.Key(urlsafe=matches[1])))
      # this regex needs more work
    value = re.sub('\((.*)\,(.*)\)', run_format, value)
    return value
  
  def validate_line(self, carrier_line, entry):
    address = None
    entry_address_reference = getattr(entry, 'shipping_address_reference', None)
    if entry_address_reference is None:  # @todo Is this ok??
      return False
    buyer_addresses = orm.Key('77', entry.partner._id_str, parent=entry.partner).get()
    for buyer_address in buyer_addresses.addresses:
      if buyer_address.internal_id == entry_address_reference:
        address = buyer_address
        break
    if address is None:  # @todo IS this ok??
      return False
    if carrier_line.exclusion:
      # Apply only at the following locations.
      allowed = False
    else:
      # Apply everywhere except at the following locations.
      allowed = True
    for loc in carrier_line.locations:
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
      price = entry.amount_total
      weight_uom = uom.get_uom(uom.Unit.build_key('kg', parent=uom.Measurement.build_key('metric')))
      volume_uom = uom.get_uom(uom.Unit.build_key('m3', parent=uom.Measurement.build_key('metric')))
      weight = format_value('0', weight_uom)
      volume = format_value('0', volume_uom)
      for line in entry._lines:
        line_weight = line._weight[0]
        line_weight_uom = uom.get_uom(ndb.Key(urlsafe=line._weight[1]))
        line_volume = line._volume[0]
        line_volume_uom = uom.get_uom(ndb.Key(urlsafe=line._volume[1]))
        weight += uom.convert_value(line_weight, line_weight_uom, weight_uom)
        volume += uom.convert_value(line_volume, line_volume_uom, volume_uom)
      for rule in carrier_line.rules:
        condition = rule.condition
        condition = self.format_value(condition)
        if safe_eval(condition, {'weight': weight, 'volume': volume, 'price': price}):
          allowed = True
          break
    return allowed


# OLD CODE #


class PayPalInit(transaction.Plugin):
  
  # user plugin, saved in datastore
  
  def run(self, journal, context):
    
    ipns = log.Record.query(ndb.GenericProperty('ipn_txn_id') == context.input['txn_id']).fetch()
    if len(ipns):
      for ipn in ipns:
        if (ipn.payment_status == context.input['payment_status']):
          raise PluginValidationError('duplicate_entry')
      entry = ipns[0].parent_entity
      if context.input['custom']:
         if (entry.key.urlsafe() == context.input['custom']):
           
            kwds = {'log_entity' : False}
            kwds.update(dict([('ipn_%s' % key, value) for key,value in context.input.items()])) # prefix
            context.log.entities.append((entry, kwds))
            
         else:
            raise PluginValidationError('invalid_ipn')
      else:
        raise PluginValidationError('invalid_ipn')
      
    else:    
      
      if not context.input['custom']:
        raise PluginValidationError('invalid_ipn')
      else:
        try:
          entry_key = ndb.Key(urlsafe=context.input['custom']) 
          entry = entry_key.get()
        except Exception as e:
          raise PluginValidationError('invalid_ipn')
        
    if not entry:
      raise PluginValidationError('invalid_ipn')
    
    kwds = {'log_entity' : False}
    kwds.update(dict([('ipn_%s' % key, value) for key,value in context.input.items()])) # prefix
    context.log.entities.append((entry, kwds))
    
    if not context.transaction.group:
       context.transaction.group = entry.parent_entity
       
    context.transaction.entities[journal.key.id()] = entry
    
    if not self.validate_entry(entry, context):
       raise PluginValidationError('fraud_check')
     
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


class Write(transaction.Plugin):
  
  def run(self, journal, context):
    
    @ndb.transactional(xg=True)
    def transaction():
        group = context.transaction.group
        if not group:
           group = Group(namespace=context.auth.domain.key.urlsafe()) # ?
           group.put()
        
        group_key = group.key # - put main key
        for key, entry in context.transaction.entities.items():
            entry.set_key(parent=group_key) # parent key for entry
            entry_key = entry.put()
            
            """
             notice the `_` before `lines` that is because 
             if you set it without underscore it will be considered as new property in expando
             so all operations should use the following paradigm:
             entry._lines = []
             entry._lines.append(Line(...))
             etc..
            """
            lines = []
            
            for line in entry._lines:
                line.journal = entry.journal
                line.company = entry.company
                line.state = entry.state
                line.date = entry.date
                line.set_key(parent=entry_key) # parent key for line, and if posible, sequence value should be key.id
                lines.append(line)
            
            ndb.put_multi(lines)
            
    transaction()
