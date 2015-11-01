# -*- coding: utf-8 -*-
'''
Created on Aug 25, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime
import copy
from decimal import Decimal

from google.appengine.api import urlfetch

import orm
import errors
import tools
from models.location import *
from models.unit import *


class PluginError(errors.BaseKeyValueError):

  KEY = 'plugin_error'


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
      seller_key = product.parent().parent().parent()  # go 3 levels up, account->seller->catalog->pricetag->product
    order = Order.query(Order.seller_reference == seller_key,
                        Order.state.IN(['cart', 'checkout']),
                        ancestor=context.input.get('buyer')).get()  # we will need composite index for this
    if order is None:
      order = Order(parent=context.input.get('buyer'))
      order.state = 'cart'
      order.date = datetime.datetime.now()
      order.seller_reference = seller_key
      order.make_original()
      order._lines = []
    else:
      defaults = {'_lines': {'config': {'search': {'options': {'limit': 0}}}}}
      if 'read_arguments' in context.input:
        tools.override_dict(defaults, context.input.get('read_arguments'))
      order.read(defaults)
    context._order = order


# This is system plugin, which means end user can not use it!
class OrderPluginExec(orm.BaseModel):

  _kind = 114

  _use_rule_engine = False

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    plugin_kinds = self.cfg.get('kinds')  # this is the flexibility we need, just to specify which plugin kinds to execute
    order = context._order
    seller = order.seller_reference.get()
    seller.read({'_plugin_group': {'plugins': {}}})  # read plugin container
    plugin_container = seller._plugin_group.value
    if plugin_container:
      for plugin in seller._plugin_group.value.plugins:
        if plugin_kinds is not None and plugin.get_kind() not in plugin_kinds:
          continue
        plugin.run(context)


# This is system plugin, which means end user can not use it!
class OrderUpdateLine(orm.BaseModel):

  _kind = 101

  _use_rule_engine = False

  def run(self, context):
    OrderProduct = context.models['125']
    CatalogProduct = context.models['28']
    order = context._order
    product_key = context.input.get('product')
    variant_signature = context.input.get('variant_signature')
    plucked_variant_signature = None
    image_key = context.input.get('image')
    quantity = context.input.get('quantity')
    if order.state != 'cart':
      raise PluginError('order_not_in_cart_state')
    line_exists = False
    for line in order._lines.value:
      product = line.product.value
      real_product_key = OrderProduct.get_partial_reference_key_path(product.reference)
      if product and real_product_key == product_key \
              and product.variant_signature == variant_signature:
        line._state = 'modified'
        product.quantity = tools.format_value(quantity, product.uom.value)
        line_exists = True
        break
    if not line_exists:
      ProductInstance = context.models['27']
      Line = context.models['33']
      product = product_key.get()
      product_instance = None
      product.read({'_category': {}})  # more fields probably need to be specified
      stocks = None
      out_of_stock = False
      if product._stock.value and product._stock.value.stocks.value: # if user defined any stocks
        stocks = product._stock.value.stocks.value
      if variant_signature:
        plucked_variant_signature = variant_signature[:]
        plucked_variant_signature_map = dict((i, v) for i, v in enumerate(plucked_variant_signature))
        # remove all allow_custom_value's from spec
        for i, variant in enumerate(product.variants.value):
          if variant.allow_custom_value:
            plucked_variant_signature.remove(plucked_variant_signature_map[i])
        if stocks:
          skip_additional_stock_checks = False
          for stock in stocks:
            if stock.variant_signature == plucked_variant_signature:
              out_of_stock = stock.availability == 'out of stock'
              skip_additional_stock_checks = True
              break # we found complete match, this product combination is definitely out of stock
          if not skip_additional_stock_checks: # no matches for out of stock found
            # try to find those with ***Any*** because they might match out of stock
            for stock in stocks:
              maybe = []
              for i, part in enumerate(plucked_variant_signature): # [{'Color': 'Red'}, {'Size': 'XL'}]
                part = part.iteritems().next() # ('Color', 'Red')
                try:
                  item = stock.variant_signature[i].iteritems().next() # ('Color', 'Red')
                  passes = item == part or item[1] == '***Any***'
                except IndexError as e:
                  # this is when user did not configure stock improperly
                  passes = False
                if passes:
                  maybe.append(True)
                else:
                  maybe.append(False)
              if all(maybe) and stock.availability == 'out of stock':
                out_of_stock = True
                break
        if out_of_stock:
          raise PluginError('product_out_of_stock') # stop the code so it doesnt issue another query for no reason
        q = ProductInstance.query()
        for variant in plucked_variant_signature:
          item = variant.iteritems().next()
          q = q.filter(ProductInstance.variant_options == '%s: %s' % (item[0], item[1]))
        product_instance = q.get()
      else: # if the product did not specify any product signature, find stock without variant_signature and see if there's any that has no stock
        for stock in stocks:
          if not stock.variant_signature and stock.availability == 'out of stock':
            out_of_stock = True
      if out_of_stock:
        raise PluginError('product_out_of_stock')
      new_line = Line()
      order_product = OrderProduct()
      order_product.name = product.name
      modified_product_key = CatalogProduct.get_complete_key_path(image_key, product_key)
      order_product.reference = modified_product_key
      order_product.variant_signature = variant_signature
      order_product.category = copy.deepcopy(product._category.value)
      order_product.code = product.code
      order_product.unit_price = tools.format_value(product.unit_price, order.currency.value)
      order_product.uom = copy.deepcopy(product.uom.get())
      if product_instance is not None:
        if hasattr(product_instance, 'unit_price') and product_instance.unit_price is not None:
          order_product.unit_price = product_instance.unit_price
        if hasattr(product_instance, 'code') and product_instance.code is not None:
          order_product.code = product_instance.code
      order_product.weight = None
      order_product.volume = None
      if product.weight is not None:
        order_product.weight = product.weight
      if product.volume is not None:
        order_product.volume = product.volume
      if product_instance is not None:
        if hasattr(product_instance, 'weight') and product_instance.weight is not None:
          order_product.weight = product_instance.weight
        if hasattr(product_instance, 'volume') and product_instance.volume is not None:
          order_product.volume = product_instance.volume
      order_product.quantity = tools.format_value(quantity, order_product.uom.value)
      new_line.product = order_product
      new_line.discount = tools.format_value('0', Unit(digits=2))
      lines = order._lines.value
      if lines is None:
        lines = []
      lines.append(new_line)
      order._lines = lines


# This is system plugin, which means end user can not use it!
class OrderProductSpecsFormat(orm.BaseModel):

  _kind = 115

  _use_rule_engine = False

  def run(self, context):
    ProductInstance = context.models['27']
    order = context._order
    weight_uom = Unit.build_key('kilogram').get()
    volume_uom = Unit.build_key('liter').get()
    total_weight = tools.format_value('0', weight_uom)
    total_volume = tools.format_value('0', volume_uom)
    for line in order._lines.value:
      if line._state == 'deleted':
        continue
      product = line.product.value
      if product.weight is not None:
        total_weight = total_weight + (product.weight * product.quantity)
      if product.volume is not None:
        total_volume = total_volume + (product.volume * product.quantity)
    order._total_weight = total_weight
    order._total_volume = total_volume


# This is system plugin, which means end user can not use it!
class OrderLineFormat(orm.BaseModel):

  _kind = 104

  _use_rule_engine = False

  def run(self, context):
    order = context._order
    for line in order._lines.value:
      if line._state == 'deleted':
        continue
      product = line.product.value
      if product:
        if order.seller_reference._root != product.reference._root:
          raise PluginError('product_does_not_bellong_to_seller')
        product.quantity = tools.format_value(product.quantity, product.uom.value)
        line.subtotal = tools.format_value((product.unit_price * product.quantity), order.currency.value)
        line.discount = tools.format_value(line.discount, Unit(digits=2))
        if line.discount is not None:
          discount = line.discount * tools.format_value('0.01', Unit(digits=2))  # or "/ tools.format_value('100', Unit(digits=2))"
          line.discount_subtotal = tools.format_value((line.subtotal - (line.subtotal * discount)), order.currency.value)
        else:
          line.discount_subtotal = tools.format_value('0', Unit(digits=2))
        tax_subtotal = tools.format_value('0', order.currency.value)
        if line.taxes.value:
          for tax in line.taxes.value:
            if tax.type == 'proportional':
              tax_amount = tools.format_value(tax.amount, Unit(digits=2)) * tools.format_value('0.01', Unit(digits=2))  # or "/ tools.format_value('100', Unit(digits=2))"  @note Using fixed formating here, since it's the percentage value, such as 17.00%.
              tax_subtotal = tax_subtotal + (line.discount_subtotal * tax_amount)
            elif tax.type == 'fixed':
              tax_amount = tools.format_value(tax.amount, order.currency.value)
              tax_subtotal = tax_subtotal + tax_amount
        line.tax_subtotal = tax_subtotal
        line.total = tools.format_value(line.discount_subtotal + line.tax_subtotal, order.currency.value)


# This is system plugin, which means end user can not use it!
class OrderCarrierFormat(orm.BaseModel):

  _kind = 122

  _use_rule_engine = False

  def run(self, context):
    order = context._order
    carrier = order.carrier.value
    if carrier:
      carrier.subtotal = tools.format_value(carrier.unit_price, order.currency.value)
      tax_subtotal = tools.format_value('0', order.currency.value)
      if carrier.taxes.value:
        for tax in carrier.taxes.value:
          if tax.type == 'proportional':
            tax_amount = tools.format_value(tax.amount, Unit(digits=2)) * tools.format_value('0.01', Unit(digits=2))
            tax_subtotal = tax_subtotal + (carrier.subtotal * tax_amount)
          elif tax.type == 'fixed':
            tax_amount = tools.format_value(tax.amount, order.currency.value)
            tax_subtotal = tax_subtotal + tax_amount
      carrier.tax_subtotal = tax_subtotal
      carrier.total = tools.format_value(carrier.subtotal + carrier.tax_subtotal, order.currency.value)


# This is system plugin, which means end user can not use it!
class OrderFormat(orm.BaseModel):

  _kind = 105

  _use_rule_engine = False

  def run(self, context):
    order = context._order
    untaxed_amount = tools.format_value('0', order.currency.value)
    tax_amount = tools.format_value('0', order.currency.value)
    total_amount = tools.format_value('0', order.currency.value)
    i = 0
    for line in order._lines.value:
      if line._state == 'deleted':
        continue
      i += 1
      line.sequence = i
      product = line.product.value
      if product:
        untaxed_amount = untaxed_amount + line.discount_subtotal
        tax_amount = tax_amount + line.tax_subtotal
        total_amount = total_amount + (line.discount_subtotal + line.tax_subtotal)  # we cannot use += for decimal its not supported
    carrier = order.carrier.value
    if carrier:
      untaxed_amount = untaxed_amount + carrier.subtotal
      tax_amount = tax_amount + carrier.tax_subtotal
      total_amount = total_amount + (carrier.subtotal + carrier.tax_subtotal)
    order.untaxed_amount = tools.format_value(untaxed_amount, order.currency.value)
    order.tax_amount = tools.format_value(tax_amount, order.currency.value)
    order.total_amount = tools.format_value(total_amount, order.currency.value)


# This is system plugin, which means end user can not use it!
class OrderLineRemove(orm.BaseModel):

  _kind = 127

  _use_rule_engine = False

  def run(self, context):
    order = context._order
    lines = order._lines.value
    if lines:
      for line in lines:
        product = line.product.value
        if product.quantity <= Decimal('0'):
          line._state = 'deleted'


# This is system plugin, which means end user can not use it!
class OrderSetMessage(orm.BaseModel):

  _kind = 119

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    OrderMessage = context.models['35']
    # this could be extended to allow params
    data = dict(agent=context.account.key, _agent=context.account, body=context.input['message'], action=context.action.key)
    for key, value in self.cfg.get('additional', {}).iteritems():
      data[key] = tools.get_attr(context, value)
    context._order._messages = [OrderMessage(**data)]


# This is system plugin, which means end user can not use it!
class OrderProcessPayment(orm.BaseModel):

  _kind = 118

  def run(self, context):
    order = getattr(self, 'find_order_%s' % context.input.get('payment_method'))(context)  # will throw an error if the payment method does not exist
    context._order = order
    order.read({'_lines': {'config': {'search': {'options': {'limit': 0}}}}, '_payment_method': {}})
    payment_plugin = order._payment_method
    if not payment_plugin:
      raise PluginError('no_payment_method_supplied')
    # payment_plugin => Instance of PaypalPayment for example.
    payment_plugin.complete(context)

  def find_order_paypal(self, context):
    ipn = context.input['request']['params']
    order_key = orm.SuperKeyProperty(kind='34').value_format(ipn['custom'])
    return order_key.get()


# Not a plugin!
class OrderAddressLocation(orm.BaseModel):

  _kind = 106

  _use_rule_engine = False

  country = orm.SuperKeyProperty('1', kind='12', required=True, indexed=False)
  region = orm.SuperKeyProperty('2', kind='13', indexed=False)
  postal_codes = orm.SuperStringProperty('3', indexed=False, repeated=True)

  _virtual_fields = {
      '_country': orm.SuperReferenceProperty(target_field='country'),
      '_region': orm.SuperReferenceProperty(target_field='region')
  }


class OrderAddressPlugin(orm.BaseModel):

  _kind = 107

  _use_rule_engine = False

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  address_type = orm.SuperStringProperty('3', required=True, default='billing', choices=('billing', 'shipping'), indexed=False)
  exclusion = orm.SuperBooleanProperty('4', required=True, default=False, indexed=False)
  locations = orm.SuperLocalStructuredProperty(OrderAddressLocation, '5', repeated=True, indexed=False)

  def run(self, context):
    if not self.active:
      return  # inactive plugin
    self.read()  # read locals
    address_key = '%s_address' % self.address_type
    address = context.input.get(address_key)
    if address:
      address = address.get_location()
      if not self.validate_address(address):
        raise PluginError('invalid_address')
      setattr(context._order, address_key, address)

  def validate_address(self, address):
    '''
    @note few problems with postal_code_from and postal_code_to
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
    for location in self.locations.value:
      validate = []
      validate.append(address.country_code == location._country.code)
      if location.region:
        validate.append(address.region_code == location._region.code)
      if location.postal_codes:
        validate.append(address.postal_code in location.postal_codes)
      if all(validate):
        allowed = self.exclusion
        break
    return allowed


class OrderCurrencyPlugin(orm.BaseModel):

  _kind = 117

  _use_rule_engine = False

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  currency = orm.SuperKeyProperty('3', kind=Unit, required=True, indexed=False)

  def run(self, context):
    if not self.active:
      return  # inactive currency
    order = context._order
    # In context of add_to_cart action runner does the following:
    order.currency = copy.deepcopy(self.currency.get())


class OrderPaymentMethodPlugin(orm.BaseModel):

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)

  def _get_name(self):
    return self.__class__.__name__

  def _get_system_name(self):
    return self.__class__.__name__.lower()

  def run(self, context):
    if not self.active:
      return  # inactive payment
    if 'payment_methods' not in context.output:
      context.output['payment_methods'] = []
    context.output['payment_methods'].append({'key': self.key,
                                              'system_name': self._get_system_name(),
                                              'name': self._get_name()})


# This plugin is incomplete!
class OrderPayPalPaymentPlugin(OrderPaymentMethodPlugin):

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
    super(OrderPayPalPaymentPlugin, self).run(context)
    # currently we only support paypal, so its enforced by default
    context._order.payment_method = self.key

  def complete(self, context):
    if not self.active:
      return
    request = context.input['request']
    ipn = request['params']
    order = context._order
    # validate if the request came from ipn
    result = urlfetch.fetch(url='https://www.sandbox.paypal.com/cgi-bin/webscr',
                            payload='cmd=_notify-validate&%s' % request['body'],
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/x-www-form-urlencoded', 'Connection': 'Close'})
    if result.content != 'VERIFIED':
      raise PluginError('invalid_ipn_message')  # log somehow

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
        raise orm.TerminateAction('duplicate_entry')  # ipns that come in with same payment_status are to be rejected
        # by the way, we cannot raise exceptions cause that will cause status code other than 200 and cause that the same
        # ipn will be called again until it reaches 200 status response code
        # ipn will retry for x amount of times till it gives up
        # so we might as well use `return` statement to exit silently
    body = 'Paypal Payment action %s' % ipn_payment_status
    new_order_message = OrderMessage(ipn_txn_id=ipn['txn_id'], action=context.action.key, ancestor=order.key, agent=Account.build_key('system'), body=body, payment_status=ipn_payment_status)
    new_order_message._clone_properties()
    new_order_message._properties['ipn'] = orm.SuperTextProperty(name='ipn', compressed=True)
    new_order_message._properties['ipn']._set_value(new_order_message, request['body'])
    order._messages = [new_order_message]

    if (self.reciever_email != ipn['receiver_email']):
      mismatches.append('receiver_email')
    if 'business' in ipn:
      if (self.business != ipn['business']):
        mismatches.append('business_email')
    if (order_currency.code != ipn['mc_currency']):
      mismatches.append('mc_currency')
    if (order.total_amount != tools.format_value(ipn['mc_gross'], order_currency)):
      mismatches.append('mc_gross')
    if (order.tax_amount != tools.format_value(ipn['tax'], order_currency)):
      mismatches.append('tax')
    if (order.key.urlsafe() != ipn['invoice']):
      mismatches.append('invoice')
    if (shipping_address.country != ipn['address_country']):
      mismatches.append('address_country')
    if (shipping_address.country_code != ipn['address_country_code']):
      mismatches.append('address_country_code')
    if (shipping_address.city != ipn['address_city']):
      mismatches.append('address_city')
    if (shipping_address.name != ipn['address_name']):
      mismatches.append('address_name')
    if shipping_address.country_code == 'US' and shipping_address.region_code[len(shipping_address.country_code) + 1:] != ipn['address_state']:  # paypal za ameriku koristi 2 digit iso standard kodove za njegove stateove
      mismatches.append('address_state')
    if (shipping_address.street != ipn['address_street']):
      mismatches.append('address_street')
    if (shipping_address.postal_code != ipn['address_zip']):
      mismatches.append('address_zip')

    for line in order._lines.value:
      product = line.product.value
      tools.log.debug('Order sequence %s' % line.sequence)
      # our line sequences begin with 0 but should begin with 1 because paypal does not support 0
      if (str(line.sequence) != ipn['item_number%s' % str(line.sequence)]):
        mismatches.append('item_number%s' % str(line.sequence))
      if (product.name != ipn['item_name%s' % str(line.sequence)]):
        mismatches.append('item_name%s' % str(line.sequence))
      if (product.quantity != tools.format_value(ipn['quantity%s' % str(line.sequence)], product.uom.value)):
        mismatches.append('quantity%s' % str(line.sequence))
      if (line.subtotal != tools.format_value(ipn['mc_gross_%s' % str(line.sequence)], order_currency)):
        mismatches.append('mc_gross_%s' % str(line.sequence))
    if not mismatches:
      if order.payment_status == ipn_payment_status:
        return None  # nothing to do since the payment status is exactly the same
      else:
        update_paypal_payment_status = False
        if order.payment_status == 'Pending' or order.payment_status is None:
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
          elif order.state == 'checkout' and ipn_payment_status == 'Denied':
            order.state = 'canceled'
            order.payment_status = ipn_payment_status
          elif order.state == 'completed':
            order.payment_status = ipn_payment_status
    else:
      # log that there were missmatches, where we should log that?
      tools.log.error('Found mismatches=%s with ipn=%s for order=%s' % (mismatches, ipn, order.key))
    tools.log.info('Set Order state %s' % order.state)
    tools.log.info('Set Order payment_status %s' % order.payment_status)


class OrderTaxPlugin(orm.BaseModel):

  _kind = 109

  _use_rule_engine = False

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  type = orm.SuperStringProperty('3', required=True, default='proportional', choices=('proportional', 'fixed'), indexed=False)
  amount = orm.SuperDecimalProperty('4', required=True, indexed=False)
  carriers = orm.SuperVirtualKeyProperty('5', kind='113', repeated=True, indexed=False)
  product_categories = orm.SuperKeyProperty('6', kind='24', repeated=True, indexed=False)
  address_type = orm.SuperStringProperty('7', required=True, default='billing', choices=('billing', 'shipping'), indexed=False)
  exclusion = orm.SuperBooleanProperty('8', required=True, default=False, indexed=False)
  product_codes = orm.SuperStringProperty('9', repeated=True, indexed=False)
  locations = orm.SuperLocalStructuredProperty(OrderAddressLocation, '10', repeated=True)

  def run(self, context):
    if not self.active:
      return  # tax is inactive
    self.read()  # read locals
    OrderTax = context.models['32']
    order = context._order
    allowed = self.validate_tax(order)

    def reset_taxes(taxes):
      if not taxes:
        taxes = []
      for tax in taxes:
        if tax.key_id_str == self.key_id_str:
          tax._state = 'deleted'
      return taxes

    def add_taxes(taxes):
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

    for line in order._lines.value:
      if line._state == 'deleted':
        continue
      product = line.product.value
      taxes = reset_taxes(line.taxes.value)
      if (self.product_categories and self.product_categories.count(product.category.value.key)) \
              or (self.product_codes and self.product_codes.count(product.code)) \
              or (not self.carriers and not self.product_categories and not self.product_codes):
        if allowed:
          add_taxes(taxes)
          line.taxes = taxes
    if self.carriers and order.carrier.value:
      taxes = reset_taxes(order.carrier.value.taxes.value)
      if self.carriers.count(order.carrier.value.reference) and allowed:
        add_taxes(taxes)
        order.carrier.value.taxes = taxes

  def validate_tax(self, order):
    address_key = '%s_address' % self.address_type
    address = getattr(order, address_key)
    address = address.value
    if address is None:
      return False
    if self.exclusion:
      # Apply only at the following locations.
      allowed = False
    else:
      # Apply everywhere except at the following locations.
      allowed = True
    if self.locations.value:
      for location in self.locations.value:
        validate = []
        validate.append(address.country_code == location._country.code)
        if location.region:
          validate.append(address.region_code == location._region.code)
        if location.postal_codes:
          validate.append(address.postal_code in location.postal_codes)
        if all(validate):
          allowed = self.exclusion
          break
    if allowed:
      # If tax is configured for carriers then check if the order references carrier on which the tax applies.
      if self.carriers:
        allowed = False
        if order.carrier.value and order.carrier.value.reference and order.carrier.value.reference in self.carriers:
          allowed = True
      # If tax is configured for product categories, then check if the order contains a line which has product category to which the tax applies.
      elif self.product_categories:
        allowed = False
        for line in order._lines.value:
          if line._state == 'deleted':
            continue
          product = line.product.value
          if self.product_categories.count(product.category.value.key):
            allowed = True
            break
    return allowed


# Not a plugin!
class OrderCarrierLinePrice(orm.BaseModel):

  _kind = 111

  _use_rule_engine = False

  condition_type = orm.SuperStringProperty('1', required=True, default='weight', choices=('weight', 'volume', 'weight*volume', 'price'), indexed=False)
  condition_operator = orm.SuperStringProperty('2', required=True, default='==', choices=('==', '!=', '>', '<', '>=', '<='), indexed=False)
  condition_value = orm.SuperDecimalProperty('3', required=True, indexed=False)
  price_type = orm.SuperStringProperty('4', required=True, default='fixed', choices=('fixed', 'variable'), indexed=False)
  price_operator = orm.SuperStringProperty('5', required=True, default='weight', choices=('weight', 'volume', 'weight*volume', 'price'), indexed=False)
  price_value = orm.SuperDecimalProperty('6', required=True, indexed=False)

  def evaluate_condition(self, data):
    value = None
    op = self.condition_operator
    if self.condition_type == 'weight*volume':
      value = data['weight'] * data['volume']
    else:
      value = data[self.condition_type]
    if op == '==':
      return value == self.condition_value
    elif op == '!=':
      return value != self.condition_value
    elif op == '>':
      return value > self.condition_value
    elif op == '<':
      return value < self.condition_value
    elif op == '>=':
      return value >= self.condition_value
    elif op == '<=':
      return value <= self.condition_value

  def calculate_price(self, data):
    if self.price_type == 'fixed':
      return self.price_value
    if self.price_type == 'variable':
      value = None
      if self.price_operator == 'weight*volume':
        value = data['weight'] * data['volume']
      else:
        value = data[self.price_operator]
      return value * self.price_value


# Not a plugin!
class OrderCarrierLine(orm.BaseModel):

  _kind = 112

  _use_rule_engine = False

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  exclusion = orm.SuperBooleanProperty('3', required=True, default=False)
  locations = orm.SuperLocalStructuredProperty(OrderAddressLocation, '4', repeated=True)
  prices = orm.SuperLocalStructuredProperty(OrderCarrierLinePrice, '5', repeated=True)


class OrderCarrierPlugin(orm.BaseModel):

  _kind = 113

  _use_rule_engine = False

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  lines = orm.SuperLocalStructuredProperty(OrderCarrierLine, '3', repeated=True)

  def run(self, context):
    if not self.active:
      return  # this is not active carrier
    self.read()  # read locals
    ProductInstance = context.models['27']
    OrderCarrier = context.models['123']
    carrier = context.input.get('carrier')
    order = context._order
    order_carrier = order.carrier.value
    valid_lines = []
    for carrier_line in self.lines.value:
      if not carrier_line.active:
        continue  # inactive carrier line
      if self.validate_line(carrier_line, order):
        valid_lines.append(carrier_line)
    if len(valid_lines):
      carrier_price = self.calculate_price(valid_lines, order)
      if not order_carrier or (carrier and carrier == self.key):
        order.carrier = OrderCarrier(description=self.name, unit_price=carrier_price, reference=self.key)
      if 'carriers' not in context.output:
        context.output['carriers'] = []
      context.output['carriers'].append({'name': self.name,
                                         'price': carrier_price,
                                         'key': self.key})

  def calculate_price(self, valid_lines, order):
    zero = Decimal('0')
    if not order._lines.value:
      return zero  # if no lines are present return 0
    prices = []
    for carrier_line in valid_lines:
      line_prices = []
      carrier_line_prices = carrier_line.prices.value
      if carrier_line_prices:
        for price in carrier_line_prices:
          condition_data = {
              'weight': order._total_weight,
              'volume': order._total_volume,
              'price': order.total_amount
          }
          if price.evaluate_condition(condition_data):
            price_data = {
                'weight': order._total_weight,
                'volume': order._total_volume,
                'price': order.total_amount
            }
            line_prices.append(price.calculate_price(price_data))
      else:
        line_prices.append(Decimal('0'))
      prices.append(min(line_prices))
    if not prices:
      return zero
    return min(prices)

  def validate_line(self, carrier_line, order):
    address = getattr(order, 'shipping_address')
    address = address.value
    if address is None:
      return False
    if carrier_line.exclusion:
      # Apply only at the following locations.
      allowed = False
    else:
      # Apply everywhere except at the following locations.
      allowed = True
    if carrier_line.locations.value:
      for location in carrier_line.locations.value:
        validate = []
        validate.append(address.country_code == location._country.code)
        if location.region:
          validate.append(address.region_code == location._region.code)
        if location.postal_codes:
          validate.append(address.postal_code in location.postal_codes)
        if all(validate):
          allowed = carrier_line.exclusion
          break
    if allowed:
      allowed = False
      if carrier_line.prices.value:
        for price in carrier_line.prices.value:
          condition_data = {
              'weight': order._total_weight,
              'volume': order._total_volume,
              'price': order.total_amount
          }
          if price.evaluate_condition(condition_data):
            allowed = True
            break
      else:
        allowed = True  # if no rules were provided, its considered truthly
    return allowed


class OrderDiscountLine(orm.BaseModel):

  _kind = 124

  _use_rule_engine = False

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  discount_value = orm.SuperDecimalProperty('3', required=True, indexed=False)
  product_categories = orm.SuperKeyProperty('4', kind='24', repeated=True, indexed=False)
  condition_type = orm.SuperStringProperty('5', required=True, default='quantity', choices=('price', 'quantity'), indexed=False)
  condition_operator = orm.SuperStringProperty('6', required=True, default='==', choices=('==', '!=', '>', '<', '>=', '<='), indexed=False)
  condition_value = orm.SuperDecimalProperty('7', required=True, indexed=False)
  product_codes = orm.SuperStringProperty('8', repeated=True, indexed=False)

  def evaluate_condition(self, data):
    value = data[self.condition_type]
    op = self.condition_operator
    if op == '==':
      return value == self.condition_value
    elif op == '!=':
      return value != self.condition_value
    elif op == '>':
      return value > self.condition_value
    elif op == '<':
      return value < self.condition_value
    elif op == '>=':
      return value >= self.condition_value
    elif op == '<=':
      return value <= self.condition_value


class OrderDiscountPlugin(orm.BaseModel):

  _kind = 126

  _use_rule_engine = False

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  lines = orm.SuperLocalStructuredProperty(OrderDiscountLine, '3', repeated=True)

  def run(self, context):
    if not self.active:
      return  # is inactive
    order = context._order
    if self.lines.value:
      for line in order._lines.value:
        line.discount = tools.format_value('0', Unit(digits=2))
        if line._state == 'deleted':
          continue
        product = line.product.value
        for discount_line in self.lines.value:
          validate = not discount_line.product_codes and not discount_line.product_categories
          if not validate:
            validate = product.category.value.key in discount_line.product_categories
          if not validate:
            validate = product.code in discount_line.product_codes
          if validate:
            price_data = {
                'quantity': product.quantity,
                'price': product.unit_price
            }
            if discount_line.evaluate_condition(price_data):
              line.discount = tools.format_value(discount_line.discount_value, Unit(digits=2))
              break
