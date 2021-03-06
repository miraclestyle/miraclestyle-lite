# -*- coding: utf-8 -*-
'''
Created on Aug 25, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime
import copy
from decimal import Decimal, ROUND_DOWN
import os

from google.appengine.api import urlfetch

import orm
import errors
import tools
from models.location import *
from models.unit import *

import stripe


def find_payment_plugin(order):
  payment_plugin = None
  seller = order.seller_reference.get()
  seller.read({'_plugin_group': {'plugins': {}}})  # read plugin container
  plugin_container = seller._plugin_group.value
  if plugin_container:
    for plugin in seller._plugin_group.value.plugins:
      if isinstance(plugin, OrderPaymentMethodPlugin):
        if ((order.payment_method == plugin._get_system_name()) and (plugin.active)):
          payment_plugin = plugin
  if not payment_plugin:
    raise PluginError('no_payment_method_supplied')
  return payment_plugin


class PluginError(errors.BaseKeyValueError):

  KEY = 'plugin_error'


# This is system plugin, which means end user can not use it!
class OrderCronNotify(orm.BaseModel):

  cfg = orm.SuperJsonProperty(default={})

  def run(self, context):
    '''
      Cron is run every x.
      First cron initialization will get first tracker it finds and process it in transaction.
      If there are more trackers, it will keep scheduling them with taskqueue until they are all sent.
      It would be ideal if the cron was run every 6 hours or something.
    '''
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    OrderNotifyTracker = context.models['136']
    OrderMessage = context.models['35']
    page_size = self.cfg.get('page_size', 10)
    static_values = self.cfg.get('s', {})
    dynamic_values = self.cfg.get('d', {})
    minutes = self.cfg.get('minutes', 0)
    seconds = self.cfg.get('seconds', 30)
    hours = self.cfg.get('hours', 0)
    values = {'account': context.account, 'input': context.input, 'action': context.action}
    values.update(static_values)
    for key, value in dynamic_values.iteritems():
      values[key] = tools.get_attr(context, value)
    # query all trackers that pass the timeout, meaning that none touched the log_message of the order
    trackers = OrderNotifyTracker.query(OrderNotifyTracker.timeout < datetime.datetime.now()).fetch(page_size)
    tracker_count = OrderNotifyTracker.query(OrderNotifyTracker.timeout < datetime.datetime.now()).count(page_size + 2) # test if there is more than 2 after this one to allow `continue` workload
    delete_trackers = []
    notifications = []
    def delete_tracker(reason, tracker):
      delete_trackers.append((reason, tracker.key))
    for tracker in trackers:
      order_key = orm.Key(urlsafe=tracker.key_id_str)
      message_count = 0
      if not any([tracker.buyer, tracker.seller]):
        # if the buyer or seller do not need any notifications, delete the tracker
        delete_tracker('buyer and seller is both false', tracker)
        continue
      order = order_key.get()
      if not order:
        # this notifier does not have order, delete it
        delete_tracker('order not found', tracker)
        continue
      timeout = (tracker.timeout - datetime.timedelta(minutes=minutes, seconds=seconds, hours=hours))
      tools.log.debug('timeout %s' % timeout)
      message_count = OrderMessage.query(OrderMessage.created >= timeout, ancestor=order_key).count()
      if not message_count:
        # this tracker will be deleted because it does not have any messages that need sending
        delete_tracker('no messages found', tracker)
        continue
      notifications.append((tracker, message_count, order))
    if delete_trackers:
      tools.log.debug('Delete %s trackers' % delete_trackers)
      orm.transaction(lambda: orm.delete_multi([key for reason, key in delete_trackers]), xg=True)
    def send_in_transaciton(tracker, data): # @note, this is slow, but only way to ensure that mail is 100% sent - app engine has tendency to "stop working" so we have to do this
      tracker.key.delete() # if it fails, it wont send mail
      tools.mail_send(data, render=False) # if this fails, it will not delete the entity and it will re-try again sometime
    tools.log.debug('Sending %s trackers' % len(notifications))
    for notification in notifications:
      tracker, message_count, order = notification
      order.read() # will autoload stuff
      buyer = order.key_root.get()
      seller = order.seller_reference._root.get()
      recipient = None
      account = None
      for_seller = False
      if tracker.buyer:
        buyer.read()
        recipient = buyer._primary_email
        account = seller
      if tracker.seller:
        seller.read()
        recipient = seller._primary_email
        account = buyer
        for_seller = True
      data = {}
      data.update(values)
      data.update({'recipient': recipient, 'account': account, 'for_seller': for_seller, 'message_count': message_count, 'entity': order})
      tools.log.debug(data)
      tools.render_subject_and_body_templates(data) # avoid reads in transaction - this might happen if template has .foo.bar.read() stuff
      orm.transaction(lambda: send_in_transaciton(tracker, data), xg=True)
    if tracker_count > (page_size + 1):
      # schedule another task to handle the next order
      data = {'action_id': 'cron_notify',
              'action_model': '34'}
      context._callbacks.append(('callback', data))


# This is system plugin, which means end user can not use it!
class OrderNotifyTrackerSeen(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    # at this moment it will set timeout of 10 minutes
    OrderNotifyTracker = context.models['136']
    key = OrderNotifyTracker.build_key(context._order.key.urlsafe())
    tracker = key.get()
    is_buyer = context.account.key == context._order.key._root
    is_seller = context.account.key == context._order.seller_reference._root
    if tracker and ((is_buyer and tracker.buyer) or (is_seller and tracker.seller)):
      tracker.key.delete()


# This is system plugin, which means end user can not use it!
class OrderNotifyTrackerSet(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    # at this moment it will set timeout of 10 minutes
    OrderNotifyTracker = context.models['136']
    minutes = self.cfg.get('minutes', 0)
    seconds = self.cfg.get('seconds', 30)
    hours = self.cfg.get('hours', 0)
    created = context._order._messages.value[-1].created
    key = OrderNotifyTracker.build_key(context._order.key.urlsafe())
    tracker = key.get()
    is_buyer = context.account.key == context._order.key._root
    is_seller = context.account.key == context._order.seller_reference._root
    seller = None
    buyer = None
    if is_buyer:
      buyer = False
      seller = True
      if not (tracker and tracker.seller):
        tracker = None
    elif is_seller:
      buyer = True
      seller = False
      if not (tracker and tracker.buyer):
        tracker = None
    if not tracker:
      new_tracker = OrderNotifyTracker(id=context._order.key.urlsafe(), timeout=created + datetime.timedelta(minutes=minutes, seconds=seconds, hours=hours), buyer=buyer, seller=seller)
      new_tracker.put()


# This is system plugin, which means end user can not use it!
class OrderCronDelete(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    limit = self.cfg.get('page', 10)
    cart_life = self.cfg.get('cart_life', 15)
    unpaid_order_life = self.cfg.get('unpaid_order_life', 30)
    Order = context.models['34']
    orders = []
    orders.extend(Order.query(Order.state == 'cart',
                               Order.created < (datetime.datetime.now() - datetime.timedelta(days=cart_life))).fetch(limit=limit))
    orders.extend(Order.query(Order.state == 'order',
                               Order.payment_status == None,
                               Order.date < (datetime.datetime.now() - datetime.timedelta(days=unpaid_order_life))).fetch(limit=limit))
    for order in orders:
      data = {'action_id': 'delete',
              'action_model': '34',
              'key': order.key.urlsafe()}
      context._callbacks.append(('callback', data))


# This is system plugin, which means end user can not use it!
class OrderInit(orm.BaseModel):

  def run(self, context):
    Order = context.models['34']
    seller_key = context.input.get('seller')
    if not seller_key:
      product_key = context.input.get('product')
      if not product_key:
        raise PluginError('seller_missing')
      seller_key = product_key.parent().parent()  # go 3 levels up, account->seller->catalog->product
    order = Order.query(Order.seller_reference == seller_key,
                        Order.state == 'cart',
                        ancestor=context.input.get('buyer')).get()  # we will need composite index for this
    if order is None:
      order = Order(parent=context.input.get('buyer'))
      order.state = 'cart'
      order.seller_reference = seller_key
      order._seller.read() # read for output
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

  def run(self, context):
    order = context._order
    product_key = context.input.get('product')
    quantity = context.input.get('quantity')
    if order.state != 'cart':
      raise PluginError('order_not_in_cart_state')
    line_exists = False
    for line in order._lines.value:
      product = line.product.value
      if product and product.reference == product_key:
        line._state = 'modified'
        product.quantity = tools.format_value(quantity, Unit.build_key('unit').get())
        line_exists = True
        break
    if not line_exists:
      OrderProduct = context.models['125']
      Line = context.models['33']
      product = product_key.get()
      if product is not None:
        new_line = Line()
        order_product = OrderProduct()
        order_product.reference = product_key
        order_product.name = product.name
        order_product.code = product.code
        order_product.description = product.description
        order_product.unit_price = tools.format_value(product.unit_price, order.currency.value)
        order_product.mass = None
        order_product.volume = None
        if product.mass is not None:
          order_product.mass = product.mass
        if product.volume is not None:
          order_product.volume = product.volume
        order_product.quantity = tools.format_value(quantity, Unit.build_key('unit').get())
        new_line.product = order_product
        new_line.discount = tools.format_value('0', Unit(digits=2))
        lines = order._lines.value
        if lines is None:
          lines = []
        lines.append(new_line)
        order._lines = lines


# This is system plugin, which means end user can not use it!
class OrderStockManagement(orm.BaseModel):

  def run(self, context):
    context.output['line_deleted_out_of_stock'] = []
    OrderProduct = context.models['125']

    def delete_line(line):
      line._state = 'deleted'
      context.output['line_deleted_out_of_stock'].append(line.key)

    @orm.tasklet
    def get_products():
      for line in context._order._lines.value:
        product = line.product.value
        if line._state == 'deleted' or not product:
          continue
        line._product = yield product.reference.get_async()
    get_products().get_result()

    for line in context._order._lines.value:
      if not hasattr(line, '_product'):
        line._state = 'deleted'
        continue
      if not line._product or (line._product.availability == 'out of stock'):
        delete_line(line)


# This is system plugin, which means end user can not use it!
class OrderProductSpecsFormat(orm.BaseModel):

  def run(self, context):
    order = context._order
    mass_uom = Unit.build_key('kilogram').get()
    volume_uom = Unit.build_key('liter').get()
    total_mass = tools.format_value('0', mass_uom)
    total_volume = tools.format_value('0', volume_uom)
    for line in order._lines.value:
      if line._state == 'deleted':
        continue
      product = line.product.value
      if product.mass is not None:
        product_total_mass = tools.format_value((product.mass * product.quantity), mass_uom)
        total_mass = tools.format_value((total_mass + product_total_mass), mass_uom)
      if product.volume is not None:
        product_total_volume = tools.format_value((product.volume * product.quantity), volume_uom)
        total_volume = tools.format_value((total_volume + product_total_volume), volume_uom)
    order._total_mass = total_mass
    order._total_volume = total_volume


# This is system plugin, which means end user can not use it!
class OrderLineFormat(orm.BaseModel):

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
        discount_subtotal = tools.format_value('0', order.currency.value)
        if line.discount is not None:
          discount_formated = tools.format_value(line.discount, Unit(digits=2)) * tools.format_value('0.01', Unit(digits=2))  # or "/ tools.format_value('100', Unit(digits=2))"
          discount_amount = tools.format_value((line.subtotal * discount_formated), order.currency.value)
          discount_subtotal = tools.format_value((line.subtotal - discount_amount), order.currency.value)
        line.discount_subtotal = discount_subtotal
        tax_subtotal = tools.format_value('0', order.currency.value)
        if line.taxes.value:
          for tax in line.taxes.value:
            if tax.type == 'proportional':
              tax_formated = tools.format_value(tax.amount, Unit(digits=2)) * tools.format_value('0.01', Unit(digits=2))  # or "/ tools.format_value('100', Unit(digits=2))"  @note Using fixed formating here, since it's the percentage value, such as 17.00%.
              tax_amount = tools.format_value((line.discount_subtotal * tax_formated), order.currency.value)
              tax_subtotal = tools.format_value((tax_subtotal + tax_amount), order.currency.value)
            elif tax.type == 'fixed':
              tax_amount = tools.format_value(tax.amount, order.currency.value)
              tax_subtotal = tools.format_value((tax_subtotal + tax_amount), order.currency.value)
        line.tax_subtotal = tax_subtotal
        line.total = tools.format_value((line.discount_subtotal + line.tax_subtotal), order.currency.value)


# This is system plugin, which means end user can not use it!
class OrderCarrierFormat(orm.BaseModel):

  def run(self, context):
    order = context._order
    carrier = order.carrier.value
    if carrier:
      carrier.subtotal = tools.format_value(carrier.unit_price, order.currency.value)
      tax_subtotal = tools.format_value('0', order.currency.value)
      if carrier.taxes.value:
        for tax in carrier.taxes.value:
          if tax.type == 'proportional':
            tax_formated = tools.format_value(tax.amount, Unit(digits=2)) * tools.format_value('0.01', Unit(digits=2))
            tax_amount = tools.format_value((carrier.subtotal * tax_formated), order.currency.value)
            tax_subtotal = tools.format_value((tax_subtotal + tax_amount), order.currency.value)
          elif tax.type == 'fixed':
            tax_amount = tools.format_value(tax.amount, order.currency.value)
            tax_subtotal = tools.format_value((tax_subtotal + tax_amount), order.currency.value)
      carrier.tax_subtotal = tax_subtotal
      carrier.total = tools.format_value((carrier.subtotal + carrier.tax_subtotal), order.currency.value)


# This is system plugin, which means end user can not use it!
class OrderFormat(orm.BaseModel):

  def run(self, context):
    order = context._order
    order.date = datetime.datetime.now()
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
        untaxed_amount = tools.format_value((untaxed_amount + line.discount_subtotal), order.currency.value)
        tax_amount = tools.format_value((tax_amount + line.tax_subtotal), order.currency.value)
        total_amount = tools.format_value((total_amount + line.total), order.currency.value)
    carrier = order.carrier.value
    if carrier:
      # untaxed_amount = tools.format_value((untaxed_amount + carrier.subtotal), order.currency.value)  # We will use this amount for carrier caluculations.
      tax_amount = tools.format_value((tax_amount + carrier.tax_subtotal), order.currency.value)
      total_amount = tools.format_value((total_amount + carrier.total), order.currency.value)
    order.untaxed_amount = untaxed_amount
    order.tax_amount = tax_amount
    order.total_amount = total_amount


# This is system plugin, which means end user can not use it!
class OrderLineRemove(orm.BaseModel):

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

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    OrderMessage = context.models['35']
    # this could be extended to allow params
    order_message = {}
    default_values = {}
    default_values['agent'] = self.cfg.get('agent', 'account.key')
    default_values['_agent'] = self.cfg.get('_agent', 'account')
    default_values['body'] = self.cfg.get('body', 'input.message')
    default_values['action'] = self.cfg.get('action', 'action.key')
    expando_values = self.cfg.get('expando_values')
    expando_fields = self.cfg.get('expando_fields')
    if expando_values:
      expando_values = tools.get_attr(context, expando_values)
    if expando_fields:
      expando_fields = tools.get_attr(context, expando_fields)
    for key, value in default_values.iteritems():
      order_message[key] = tools.get_attr(context, value)
    if not expando_fields:
      if expando_values:
        for key, value in expando_values.iteritems():
          order_message[key] = value
      new_order_message = OrderMessage(**order_message)
    else:
      order_message_expando_fields = {}
      for key, value in expando_fields.iteritems():
        order_message_expando_fields[key] = value
      order_message_expando_values = {}
      for key, value in expando_values.iteritems():
        order_message_expando_values[key] = value
      new_order_message = OrderMessage(**order_message)
      new_order_message._clone_properties()
      new_order_message._properties.update(order_message_expando_fields)
      for key, value in order_message_expando_fields.iteritems():
        value._set_value(new_order_message, order_message_expando_values.pop(key))
      new_order_message.populate(**order_message_expando_values)
    context._order._messages = [new_order_message]


# This is system plugin, which means end user can not use it!
class OrderNotify(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    ip_address = tools.get_remote_addr()
    requested_payment_method = context.input.get('payment_method')
    request = context.input.get('request')
    order_key = getattr(self, 'find_order_key_%s' % requested_payment_method)(context)  # will throw an error if the payment method does not exist
    order = order_key.get()
    if not order or order.state != 'order':
      tools.log.error('Order not found! request: %s, ip: %s' % (request, ip_address))
      raise orm.TerminateAction('order_not_found')
    order.read({'_lines': {'config': {'search': {'options': {'limit': 0}}}}})
    if order.payment_method != requested_payment_method:
      tools.log.error('Payment mismatch. order_payment_method: %s, requested_payment_method: %s, ip: %s' % (order.payment_method, requested_payment_method, ip_address))
      raise orm.TerminateAction('payment_method_mismatch')
    context._order = order
    payment_plugin = find_payment_plugin(order)
    # payment_plugin => Instance of PaypalPayment for example.
    payment_plugin.notify(context)

  def find_order_key_paypal(self, context):
    url = tools.get_attr(self.cfg, 'options.paypal.webscr')
    ip_address = tools.get_remote_addr()
    request = context.input.get('request')
    ipn = request['ipn']
    result_content = None
    tools.log.debug('IPN: %s' % (ipn))  # We will keep this for some time, we have it recorded in OrderMessage, however, this is easier to access.
    try:
      result = urlfetch.fetch(url=url,
                              payload='cmd=_notify-validate&%s' % request['body'],
                              method=urlfetch.POST,
                              deadline=60,
                              headers={'Content-Type': 'application/x-www-form-urlencoded', 'Connection': 'Close'})
      result_content = result.content
    except Exception as e:
      tools.log.error('%s, ipn: %s, content: %s, ip: %s' % (e, ipn, result_content, ip_address))
    if result_content != 'VERIFIED':
        tools.log.error('Paypal ipn message not valid. ipn: %s, content: %s, ip: %s' % (ipn, result_content, ip_address))
        raise orm.TerminateAction('invalid_ipn')
    if 'custom' not in ipn:
      tools.log.debug('PayPal Event. ipn: %s, ip: %s' % (ipn, ip_address))
      raise orm.TerminateAction('irrelevant_event')
    return orm.SuperKeyProperty(kind='34').value_format(ipn['custom'])
  
  def find_order_key_stripe(self, context):
    ip_address = tools.get_remote_addr()
    request = context.input.get('request')
    event_object = tools.get_attr(context.input, 'request.object', '')
    event_type = tools.get_attr(context.input, 'request.type', '')
    charge_id = None
    tools.log.debug('Stripe Event: %s, ip: %s' % (request, ip_address))  # Control point.
    # We make sure untrusted data concerns us.
    supported_events = ['charge.refunded', 'charge.dispute.closed',
                        'charge.dispute.created', 'charge.dispute.funds_reinstated',
                        'charge.dispute.funds_withdrawn', 'charge.dispute.updated']
    if (event_object != 'event') or (event_type not in supported_events):
      tools.log.debug('Stripe Event: %s, ip: %s' % (request, ip_address))
      raise orm.TerminateAction('irrelevant_event')
    # We verify the data in notify plugin method.
    if (event_type == 'charge.refunded'):
      charge_id = tools.get_attr(context.input, 'request.data.object.id')
    else:
      charge_id = tools.get_attr(context.input, 'request.data.object.charge')
    if isinstance(charge_id, (str, unicode)) and charge_id.startswith('ch_'):
      OrderMessage = context.models['35']
      order_message = OrderMessage.query(orm.GenericProperty('charge_id') == charge_id).get()
      if isinstance(order_message, OrderMessage):
        return order_message.key_parent
      else:
        tools.log.error('Order not found! request: %s, ip: %s' % (request, ip_address))
        raise orm.TerminateAction('order_not_found')
    else:
      tools.log.error('Order not found! request: %s, ip: %s' % (request, ip_address))
      raise orm.TerminateAction('order_not_found')


# This is system plugin, which means end user can not use it!
class OrderPay(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    order = context._order
    payment_plugin = find_payment_plugin(order)
    # payment_plugin => Instance of PaypalPayment for example.
    payment_plugin.pay(context)


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
    context._order.payment_method = self._get_system_name()


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
    context._order.payment_method = self._get_system_name()
  
  def pay(self, context):
    pass

  def notify(self, context):
    ip_address = tools.get_remote_addr()
    request = context.input.get('request')
    ipn = request['ipn']
    ipn_payment_status = ipn['payment_status']
    order = context._order
    context.message_body = ''
    shipping_address = order.shipping_address.value
    order_currency = order.currency.value
    
    def duplicate_check():
      OrderMessage = context.models['35']
      order_messages = OrderMessage.query(orm.GenericProperty('ipn_txn_id') == ipn['txn_id']).fetch()
      for order_message in order_messages:
        if order_message.payment_status == ipn_payment_status:
          raise orm.TerminateAction('duplicate_entry')
    
    def new_mismatch(order_value, ipn_value):
      # 'Seller settings receiver e-mail: testA@example.com - Paypal Payment receiver e-mail: testB@example.com'
      new_str = '\nOrder %s: %s - PayPal payment %s: %s' % (order_value[0], order_value[1], ipn_value[0], ipn_value[1])
      context.message_body += new_str
    
    def validate_payment_general():
      reciever_email = self.reciever_email.lower()
      ipn_reciever_email = ipn['receiver_email'].lower()
      if reciever_email != ipn_reciever_email:
        new_mismatch(('seller settings receiver e-mail', self.reciever_email), ('receiver e-mail', ipn['receiver_email']))
      
      if 'business' in ipn:
        business_email = self.business.lower()
        ipn_business_email = ipn['business'].lower()
        if business_email != ipn_business_email:
          new_mismatch(('seller settings business e-mail', self.business), ('business e-mail', ipn['business']))
      
      if order_currency.code != ipn['mc_currency']:
        new_mismatch(('currency', order_currency.code), ('currency', ipn['mc_currency']))
      
      if order.total_amount != tools.format_value(ipn['mc_gross'], order_currency):
        new_mismatch(('total amount', order.total_amount), ('total amount', tools.format_value(ipn['mc_gross'], order_currency)))
      
      if order.tax_amount != tools.format_value(ipn['tax'], order_currency):
        new_mismatch(('tax amount', order.tax_amount), ('tax amount', tools.format_value(ipn['tax'], order_currency)))
      
      if order.carrier.value.subtotal != tools.format_value(ipn['mc_handling'], order_currency):
        new_mismatch(('shipping and handling amount', order.carrier.value.subtotal), ('shipping and handling amount', tools.format_value(ipn['mc_handling'], order_currency)))
      
      if order.key.urlsafe() != ipn['invoice']:
        new_mismatch(('id', order.key.urlsafe()), ('order id', ipn['invoice']))
    
    def validate_payment_shipping_address():
      if shipping_address.country != ipn['address_country']:
        new_mismatch(('shipping address country', shipping_address.country), ('shipping address country', ipn['address_country']))
      
      if shipping_address.country_code != ipn['address_country_code']:
        new_mismatch(('shipping address country code', shipping_address.country_code), ('shipping address country code', ipn['address_country_code']))
      
      if shipping_address.country_code == 'US' and shipping_address.region_code[len(shipping_address.country_code) + 1:] != ipn['address_state']:  # PayPa uses 2 digit ISO codes for US states
        new_mismatch(('shipping address region', shipping_address.region_code[len(shipping_address.country_code) + 1:]), ('shipping address region', ipn['address_state']))
      
      shipping_address_city = shipping_address.city.lower()
      ipn_address_city = ipn['address_city'].lower()
      if shipping_address_city != ipn_address_city:
        new_mismatch(('shipping address city', shipping_address.city), ('shipping address city', ipn['address_city']))
      
      shipping_address_postal_code = shipping_address.postal_code.lower()
      ipn_shipping_address_postal_code = ipn['address_zip'].lower()
      if shipping_address_postal_code != ipn_shipping_address_postal_code:
        new_mismatch(('shipping address postal code', shipping_address.postal_code), ('shipping address postal code', ipn['address_zip']))
      
      shipping_address_street = shipping_address.street.lower()
      ipn_shipping_address_street = ipn['address_street'].lower()
      if shipping_address_street != ipn_shipping_address_street:
        new_mismatch(('shipping address street', shipping_address.street), ('shipping address street', ipn['address_street']))
      
      if shipping_address.name != ipn['address_name']:
        new_mismatch(('shipping address name', shipping_address.name), ('shipping address name', ipn['address_name']))
    
    def validate_payment_lines():
      for line in order._lines.value:
        product = line.product.value
        # our line sequences begin with 0 but should begin with 1 because paypal does not support 0
        if str(line.sequence) != ipn['item_number%s' % line.sequence]:
          new_mismatch(('item #%s sequence' % line.sequence, line.sequence), ('item #%s sequence' % line.sequence, ipn['item_number%s' % line.sequence]))
        
        if product.name != ipn['item_name%s' % line.sequence]:
          new_mismatch(('item #%s name' % line.sequence, product.name), ('item #%s name' % line.sequence, ipn['item_name%s' % line.sequence]))
        
        ipn_line_quantity = tools.format_value(ipn['quantity%s' % line.sequence], Unit.build_key('unit').get())
        if product.quantity != ipn_line_quantity:
          new_mismatch(('item #%s quantity' % line.sequence, product.quantity), ('item #%s quantity' % line.sequence, ipn_line_quantity))
        
        ipn_line_subtotal = tools.format_value(ipn['mc_gross_%s' % line.sequence], order_currency)
        if line.subtotal != ipn_line_subtotal:
          new_mismatch(('item #%s subtotal (before discount)' % line.sequence, line.subtotal), ('item #%s subtotal' % line.sequence, ipn_line_subtotal))
    
    def set_payment_status():
      '''payment_status The status of the payment:
      Canceled_Reversal: A reversal has been canceled. For example, you
      won a dispute with the customer, and the funds for the transaction that was
      reversed have been returned to you.
      Completed: The payment has been completed, and the funds have been
      added successfully to your account balance.
      Created: A German ELV payment is made using Express Checkout.
      Denied: You denied the payment. This happens only if the payment was
      previously pending because of possible reasons described for the
      pending_reason variable or the Fraud_Management_Filters_x
      variable.
      Expired: This authorization has expired and cannot be captured.
      Failed: The payment has failed. This happens only if the payment was
      made from your customer's bank account.
      Pending: The payment is pending. See pending_reason for more
      information.
      Refunded: You refunded the payment.
      Reversed: A payment was reversed due to a chargeback or other type of
      reversal. The funds have been removed from your account balance and
      returned to the buyer. The reason for the reversal is specified in the
      ReasonCode element.
      Processed: A payment has been accepted.
      Voided: This authorization has been voided.'''
      if ipn_payment_status in ['Pending', 'Completed']:
        # Validate payment
        validate_payment_general()
        validate_payment_shipping_address()
        validate_payment_lines()
        if len(context.message_body):
          order.payment_status = 'Mismatched'
          tools.log.error('Found mismatches: %s, ipn: %s, order: %s' % (context.message_body, ipn, order.key))
        else:
          order.payment_status = ipn_payment_status
      elif ipn_payment_status in ['Refunded', 'Reversed']:
        order.payment_status = ipn_payment_status
        context.message_body = '\n%s amount: %s' % (ipn_payment_status, abs(tools.format_value(ipn['mc_gross'], order_currency)))
      else:
        order.payment_status = ipn_payment_status
    
    # Check for ipn duplicates
    duplicate_check()
    
    # Devise course of action based on IPN payment status
    if order.payment_status == ipn_payment_status:
      return None  # nothing to do since the payment status is exactly the same
    else:
      set_payment_status()
    
    # Produce final message
    Account = context.models['11']
    context.new_message = {'ipn_txn_id': ipn['txn_id'],
                           'action': context.action.key,
                           'ancestor': order.key,
                           'agent': Account.build_key('system'),
                           'body': 'Payment %s.%s' % (order.payment_status, context.message_body),
                           'payment_status': order.payment_status,
                           'ipn': request['body']}
    context.new_message_fields = {'ipn': orm.SuperTextProperty(name='ipn', compressed=True, indexed=False)}


class OrderStripePaymentPlugin(OrderPaymentMethodPlugin):

  _kind = 114

  _use_rule_engine = False

  secret_key = orm.SuperStringEncryptedProperty('3', placeholder='invisible', required=True, indexed=False)  # This field needs to be encrypted. Perhaps we should implement property encryption capability?
  publishable_key = orm.SuperStringProperty('4', required=True, indexed=False) # this is public information

  def _get_name(self):
    return 'Stripe'

  def _get_system_name(self):
    return 'stripe'

  def run(self, context):
    if not self.active:
      return
    super(OrderStripePaymentPlugin, self).run(context)
    context._order.payment_method = self._get_system_name()
  
  def pay(self, context):
    token = context.input.get('token') # this could be the request variable but standard action cannot be used see the paypal implementation
    order = context._order
    order.read({'_seller': {}})
    ip_address = tools.get_remote_addr()
    try:
      # https://stripe.com/docs/api#create_charge
      total = order.total_amount * (Decimal('10') ** order.currency.value.digits)  # I think it is better to do it with long(). But here it is, just in case we need it: amount=(order.total_amount * (Decimal('10') ** order.currency.value.digits)).quantize(Decimal('10') ** order.currency.value.digits, rounding=ROUND_DOWN)
      charge = stripe.Charge.create(
          api_key=self.secret_key.decrypted, # apikey must be passed here because you cannot set module level apikey globally
          amount=long(total), # amount in smallest currency unit. https://stripe.com/docs/api#create_charge-amount, casting it into integer
          currency=order.currency.value.code,
          source=token,
          description='MIRACLESTYLE Sales Order #%s' % order.key_id_str,
          statement_descriptor=order._seller.value.name,
          metadata={'origin': tools.absolute_url(''), 'order_reference': order.key_urlsafe, 'order_url': tools.absolute_url('%s/%s/%s' % ('seller', 'order', order.key_urlsafe))}
      )
      tools.log.debug('Stripe Charge: %s, ip: %s' % (charge, ip_address))
      order.state = 'order'
      order.payment_status = 'Completed'
      Account = context.models['11']
      context.new_message = {'charge_id': charge.id,
                             'action': context.action.key,
                             'ancestor': order.key,
                             'agent': Account.build_key('system'),
                             'body': 'Payment %s.' % order.payment_status,
                             'payment_status': order.payment_status,
                             'charge': charge}
      context.new_message_fields = {'charge': orm.SuperPickleProperty(name='charge', compressed=True, indexed=False)}  # Or should it bi json property?
    except stripe.error.APIConnectionError, e:
      tools.log.error('%s. ip: %s' % (e.message, ip_address))
      raise PluginError('api_connection_error')
    except stripe.error.APIError, e:
      tools.log.error('%s. ip: %s' % (e.message, ip_address))
      raise PluginError('api_error')
    except stripe.error.AuthenticationError, e:
      tools.log.error('Authentication with Stripe API failed. ip: %s' %  ip_address)
      raise PluginError('authentication_error')
    except stripe.error.CardError, e:
      tools.log.error('%s. code: %s, ip: %s' % (e.message, e.code, ip_address))
      raise PluginError(e.code)
    except stripe.error.InvalidRequestError, e:
      tools.log.error('%s. ip: %s' % (e.message, ip_address))
      raise PluginError('invalid_request_error')
    except stripe.error.RateLimitError, e:
      tools.log.error('%s. ip: %s' % (e.message, ip_address))
      raise PluginError('rate_limit_error')

  def notify(self, context):
    ip_address = tools.get_remote_addr()
    request = context.input.get('request')
    order = context._order
    context.message_body = ''
    
    def get_event(event_id):
      try:
        return stripe.Event.retrieve(event_id, api_key=self.secret_key.decrypted)
      except stripe.error.APIConnectionError, e:
        tools.log.error('%s. ip: %s' % (e.message, ip_address))
        raise PluginError('api_connection_error')
      except stripe.error.APIError, e:
        tools.log.error('%s. ip: %s' % (e.message, ip_address))
        raise PluginError('api_error')
      except stripe.error.AuthenticationError, e:
        tools.log.error('Authentication with Stripe API failed. ip: %s' %  ip_address)
        raise PluginError('authentication_error')
      except stripe.error.CardError, e:
        tools.log.error('%s. code: %s, ip: %s' % (e.message, e.code, ip_address))
        raise PluginError(e.code)
      except stripe.error.InvalidRequestError, e:
        tools.log.error('%s. ip: %s' % (e.message, ip_address))
        raise PluginError('invalid_request_error')
      except stripe.error.RateLimitError, e:
        tools.log.error('%s. ip: %s' % (e.message, ip_address))
        raise PluginError('rate_limit_error')
    
    def validate_event(event):
      if (request != event):
        tools.log.error('Event Mismatch! event: %s, request: %s, ip: %s' % (event, request, ip_address))
        raise orm.TerminateAction('invalid_event')
      OrderMessage = context.models['35']
      order_messages = OrderMessage.query(orm.GenericProperty('event_id') == event.id).fetch()
      if len(order_messages):
        raise orm.TerminateAction('duplicate_entry')
    
    def set_payment_status(event):
      '''
      Here we deal with the following elements:
      https://stripe.com/docs/api#events
      https://stripe.com/docs/api#event_types
      https://stripe.com/docs/api#charges
      https://stripe.com/docs/api#refunds
      https://stripe.com/docs/api#disputes
      We deal with chrage.refund and charge dispute events ATM.
      '''
      def amount_message(message, amount, currency_code):
        currency_key = Unit.build_key(currency_code)
        currency = currency_key.get()
        if currency:
          reverted_amount = (Decimal(amount) * (Decimal('10') ** -currency.digits)).quantize(Decimal('10') ** -currency.digits, rounding=ROUND_DOWN)
          return '%s %s %s.' % (message, currency.code, reverted_amount)
        else:
          return ''
      
      if event.type == 'charge.refunded':
        charge = event.data.object
        if charge.amount_refunded == charge.amount:
          order.payment_status = 'Refunded'
          message_body = amount_message('\nTotal amount refunded:', charge.amount_refunded, charge.currency)
          context.message_body = 'Payment Refunded.%s' % message_body
        else:
          latest_refund = None
          for refund in charge.refunds.data:
            if (latest_refund is None) or (latest_refund.created < refund.created):
              latest_refund = refund
          order.payment_status = 'Partially Refunded'
          message_body = amount_message('\nAmount refunded:', latest_refund.amount, latest_refund.currency)
          context.message_body = 'Payment Partially Refunded.%s' % message_body
      if event.type in ['charge.dispute.created', 'charge.dispute.closed', 'charge.dispute.funds_reinstated', 'charge.dispute.funds_withdrawn', 'charge.dispute.updated']:
        dispute = event.data.object
        order.payment_status = 'Disputed'
        message_body = ''
        if event.type == 'charge.dispute.created':
          message_body = '\nDispute created.'
        if event.type == 'charge.dispute.closed':
          message_body = '\nDispute closed.'
        if event.type == 'charge.dispute.funds_reinstated':
          message_body = '\nDispute funds reinstated.'
        if event.type == 'charge.dispute.funds_withdrawn':
          message_body = '\nDispute funds withdrawn.'
        if event.type == 'charge.dispute.updated':
          message_body = '\nDispute updated.'
        dispute_message = amount_message('\nAmount disputed:', dispute.amount, dispute.currency)
        context.message_body = 'Payment Disputed.%s%s' % (message_body, dispute_message)
    
    # Ask Stripe for the event object.
    event = get_event(request['id'])
    
    # Verify event is genuine and check for event duplicates.
    validate_event(event)
    
    set_payment_status(event)
    
    # Produce final message
    Account = context.models['11']
    context.new_message = {'event_id': event.id,
                           'action': context.action.key,
                           'ancestor': order.key,
                           'agent': Account.build_key('system'),
                           'body': context.message_body,
                           'payment_status': order.payment_status,
                           'event': event}
    context.new_message_fields = {'event': orm.SuperPickleProperty(name='event', compressed=True, indexed=False)}  # Or should it bi json property? While configured as json, this field reported an error when trying to store event object!


# Not a plugin!
class OrderAddressLocation(orm.BaseModel):

  _kind = 106

  _use_rule_engine = False

  country = orm.SuperKeyProperty('1', kind='12', required=True, indexed=False)
  region = orm.SuperKeyProperty('2', kind='13', indexed=False)
  postal_codes = orm.SuperStringProperty('3', indexed=False, repeated=True)

  _virtual_fields = {
      '_country': orm.SuperReferenceProperty(autoload=True, target_field='country'),
      '_region': orm.SuperReferenceProperty(autoload=True, target_field='region')
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


class OrderTaxPlugin(orm.BaseModel):

  _kind = 109

  _use_rule_engine = False

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  type = orm.SuperStringProperty('3', required=True, default='proportional', choices=('proportional', 'fixed'), indexed=False)
  amount = orm.SuperDecimalProperty('4', required=True, indexed=False)
  carriers = orm.SuperVirtualKeyProperty('5', kind='113', repeated=True, indexed=False)
  address_type = orm.SuperStringProperty('6', required=True, default='billing', choices=('billing', 'shipping'), indexed=False)
  exclusion = orm.SuperBooleanProperty('7', required=True, default=False, indexed=False)
  product_codes = orm.SuperStringProperty('8', repeated=True, indexed=False)
  locations = orm.SuperLocalStructuredProperty(OrderAddressLocation, '9', repeated=True)

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
      if (self.product_codes and self.product_codes.count(product.code)) or not self.product_codes # If user wants to bypass product taxes and apply only carrier he can do so by specifying rogue code
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
      # If tax is configured for product codes, then check if the order contains a line which has product code to which the tax applies.
      elif self.product_codes:
        allowed = False
        for line in order._lines.value:
          if line._state == 'deleted':
            continue
          product = line.product.value
          if self.product_codes.count(product.code):
            allowed = True
            break
    return allowed


# Not a plugin!
class OrderCarrierLinePrice(orm.BaseModel):

  _kind = 111

  _use_rule_engine = False

  condition_type = orm.SuperStringProperty('1', required=True, default='mass', choices=('mass', 'volume', 'mass*volume', 'price'), indexed=False)
  condition_operator = orm.SuperStringProperty('2', required=True, default='==', choices=('==', '!=', '>', '<', '>=', '<='), indexed=False)
  condition_value = orm.SuperDecimalProperty('3', required=True, indexed=False)
  price_type = orm.SuperStringProperty('4', required=True, default='fixed', choices=('fixed', 'variable'), indexed=False)
  price_operator = orm.SuperStringProperty('5', required=True, default='mass', choices=('mass', 'volume', 'mass*volume', 'price'), indexed=False)
  price_value = orm.SuperDecimalProperty('6', required=True, indexed=False)

  def evaluate_condition(self, data):
    value = None
    op = self.condition_operator
    if self.condition_type == 'mass*volume':
      value = data['mass'] * data['volume']
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
      if self.price_operator == 'mass*volume':
        value = data['mass'] * data['volume']
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
    OrderCarrier = context.models['123']
    carrier = context.input.get('carrier')
    order = context._order
    order_carrier = order.carrier.value
    carrier_price = Decimal('0')
    if self.lines.value:
      for carrier_line in self.lines.value:
        if not carrier_line.active:
          continue  # inactive carrier line
        if self.validate_line(carrier_line, order):
          carrier_price = self.calculate_price(carrier_line, order)
          break
    if not order_carrier or (carrier and carrier == self.key):
      order.carrier = OrderCarrier(description=self.name, unit_price=carrier_price, reference=self.key)
    if 'carriers' not in context.output:
      context.output['carriers'] = []
    context.output['carriers'].append({'name': self.name,
                                       'price': carrier_price,
                                       'key': self.key})

  def calculate_price(self, carrier_line, order):
    zero = Decimal('0')
    if not order._lines.value:
      return zero  # if no lines are present return 0
    data = {
        'mass': order._total_mass,
        'volume': order._total_volume,
        'price': order.untaxed_amount  # Using order.total_amount is causing specific cases issue. The most reasonable option is to use pre-tax & pre-carrier amount.
    }
    line_prices = []
    carrier_line_prices = carrier_line.prices.value
    if carrier_line_prices:
      for price in carrier_line_prices:
        if price.evaluate_condition(data):
          line_prices.append(price.calculate_price(data))
    if not line_prices:
      return zero
    return min(line_prices)

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
        data = {
            'mass': order._total_mass,
            'volume': order._total_volume,
            'price': order.untaxed_amount  # Using order.total_amount is causing specific cases issue. The most reasonable option is to use pre-tax & pre-carrier amount.
        }
        for price in carrier_line.prices.value:
          if price.evaluate_condition(data):
            allowed = True
            break
      else:
        allowed = True  # if no rules were provided, its considered truthly
    return allowed


# Not a plugin!
class OrderDiscountLine(orm.BaseModel):

  _kind = 124

  _use_rule_engine = False

  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  discount_value = orm.SuperDecimalProperty('3', required=True, indexed=False)
  condition_type = orm.SuperStringProperty('4', required=True, default='quantity', choices=('price', 'quantity'), indexed=False)
  condition_operator = orm.SuperStringProperty('5', required=True, default='==', choices=('==', '!=', '>', '<', '>=', '<='), indexed=False)
  condition_value = orm.SuperDecimalProperty('6', required=True, indexed=False)
  product_codes = orm.SuperStringProperty('7', repeated=True, indexed=False)

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
          if not discount_line.active:
            continue  # inactive discount line
          validate = not discount_line.product_codes or (product.code in discount_line.product_codes)
          if validate:
            price_data = {
                'quantity': product.quantity,
                'price': tools.format_value((product.unit_price * product.quantity), order.currency.value)
            }
            if discount_line.evaluate_condition(price_data):
              line.discount = tools.format_value(discount_line.discount_value, Unit(digits=2))
              break


class FailTransaction(orm.BaseModel):
  
  def run(self, context):
    new_var = None
    new_var.call(context)