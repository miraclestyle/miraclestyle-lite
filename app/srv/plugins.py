# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import datetime
import collections
import re
 
from app import ndb
from app.srv import transaction, rule, uom, location, log
from app.lib.safe_eval import safe_eval
 
class PluginValidationError(Exception):
  pass
  
class Location:
  
  def __init__(self, country, region=None, postal_code_from=None, postal_code_to=None, city=None):
    self.country = country
    self.region = region
    self.postal_code_from = postal_code_from
    self.postal_code_to = postal_code_to
    self.city = city
    
class AddressRule(transaction.Plugin):
  
  _kind = 54
  
  exclusion = ndb.SuperBooleanProperty('5', default=False)
  address_type = ndb.SuperStringProperty('6')
  locations = ndb.SuperPickleProperty('7')
  
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
 
    valid_addresses = collections.OrderedDict()
    default_address = None
    address_reference_key = '%s_address_reference' % self.address_type
    address_key = '%s_address' % self.address_type
    addresses_key = '%s_addresses' % self.address_type
    default_address_key = 'default_%s' % self.address_type
    
    input_address_reference = context.args.get(address_reference_key)
    entry_address_reference = getattr(entry, address_reference_key, None)
    entry_address = getattr(entry, address_key, None)
    
    from app.opt import buyer
      
    buyer_addresses = buyer.Address.query(ancestor=entry.partner).fetch()
    
    if not len(buyer_addresses):
       raise PluginValidationError('no_address')
    
    for buyer_address in buyer_addresses:
      if self.validate_address(buyer_address):
         valid_addresses[buyer_address.key.urlsafe()] = buyer_address
         if getattr(buyer_address, default_address_key):
             default_address = buyer_address
             
    if not len(valid_addresses):
       raise PluginValidationError('no_valid_address')
    
    context.response[addresses_key] = valid_addresses
    
    if not default_address and valid_addresses:
      default_address = valid_addresses.values()[0]
    
    if input_address_reference and input_address_reference.urlsafe() in valid_addresses:
       default_address = input_address_reference.get()
    elif entry_address_reference and entry_address_reference.urlsafe() in valid_addresses:
       default_address = entry_address_reference.get()
    
    if default_address:
 
      setattr(entry, address_reference_key, default_address.key)
      setattr(entry, address_key, location.get_location(default_address))
      
      context.response[default_address_key] = default_address
    else:
      raise PluginValidationError('no_address_found')
 
  def validate_address(self, address):
    
    # Shipping everywhere except at the following locations
    if not (self.exclusion):
      allowed = True
      for loc in self.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = False
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = False
            break
        elif not (loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
            allowed = False
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
            allowed = False
            break
    # Shipping only at the following locations
    else:
      allowed = False
      for loc in self.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = True
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = True
            break
        elif not (loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
            allowed = True
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
            allowed = True
            break
    return allowed
 
 
class CartInit(transaction.Plugin):
  
  _kind = 55
  
  def run(self, journal, context):
    # ucitaj postojeci entry na kojem ce se raditi write
    catalog_key = context.args.get('catalog')
    user_key = context.auth.user.key
    catalog = catalog_key.get()
    company = catalog.company.get()
    company_key = company.key
    journal_key = journal.get_key(journal.key.id(), namespace=catalog.key.namespace())
     
    Entry = transaction.Entry
  
    entry = Entry.query(Entry.journal == journal_key, 
                        Entry.company == company_key, Entry.state.IN(['cart', 'checkout', 'processing']),
                        Entry.party == user_key
                        ).get()
    # ako entry ne postoji onda ne pravimo novi entry na kojem ce se raditi write

    if not entry:
       if context.action.operation == 'write':
          entry = Entry()
          entry.journal = journal_key
          entry.company = company_key
          entry.company_address = location.get_location(company)
          entry.state = 'cart'
          entry.date = datetime.datetime.today()
          entry.party = user_key
          # accounts recieveable
          entry._lines = []
       else:
          raise PluginValidationError('not_found')
 
    # proveravamo da li je entry u state-u 'cart'
    journal.set_entry_global_role(entry)
 
    context.rule.entity = entry
    rule.Engine.run(context)
    
    if not rule.executable(context):
      # ukoliko je entry u drugom state-u od 'cart' satate-a, onda abortirati pravljenje entry-ja
      # taj abortus bi trebala da verovatno da bude neka "error" class-a koju client moze da interpretira useru
      raise PluginValidationError('entry_not_in_cart_state')
    else:
      if entry.key:
         if not context.transaction.group:
            context.transaction.group = entry.parent_entity
         entry._lines = transaction.Line.query(ancestor=entry.key).fetch(-transaction.Line.sequence)
      context.transaction.entities[journal.key.id()] = entry
      

class AccountsReceivable(transaction.Plugin):
  
   def run(self, journal, context):
     
       entry = context.transaction.entities[journal.key.id()]
       
       if not entry._lines:
          entry._lines.append(transaction.Line(sequence=0, uom=entry.currency, 
                                           credit=uom.format_value('0', entry.currency), debit=uom.format_value('0', entry.currency),
                                           categories=[transaction.Category.build_key('key')]))
      

class ProductToLine(transaction.Plugin):
    
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
   
    catalog_pricetag_key = context.args.get('catalog_pricetag')
    product_template_key = context.args.get('product_template')
    product_instance_key = context.args.get('product_instance')
    variant_signature = context.args.get('variant_signature')
    custom_variants = context.args.get('custom_variants')
 
    # svaka komponenta mora postovati pravila koja su odredjena u journal-u
    # izmene na postojecim entry.lines ili dodavanje novog entry.line zavise od state-a 
    line_exists = False
    
    for line in entry._lines:
        if (hasattr(line, 'catalog_pricetag_reference')
            and catalog_pricetag_key == line.catalog_pricetag_reference
            and hasattr(line, 'product_instance_reference')
            and product_instance_key == line.product_instance_reference):
          line.quantity = line.quantity + uom.format_value('1', line.product_uom) # decmail formating required
          line_exists = True
          break
      
    if not (line_exists):
      product_template = product_template_key.get()
      product_instance = product_instance_key.get()
      product_category = product_template.product_category.get()
      product_category_complete_name = product_category.complete_name
 
      new_line = transaction.Line()
 
      new_line.sequence = entry._lines[-1].sequence + 1
         
      new_line.categories.append(transaction.Category.build_key('key')) # ovde ide ndb.Key('Category', 'key')
 
      new_line.description = product_template.name
      
      if (hasattr(product_template, 'product_instance_count') and product_template.product_instance_count > 1000):
        new_line.description += '\n %s' % variant_signature
      else:
        if (custom_variants):
          new_line.description += '\n %s' % variant_signature
      
      new_line.uom = entry.currency
      new_line.product_uom = uom.get_uom(product_template.product_uom)
      
      if hasattr(product_template, 'weight'):
         new_line._weight = product_template.weight
      
      if hasattr(product_template, 'volume'):   
         new_line._volume = product_template.volume
      
      new_line.product_category_complete_name = product_category_complete_name
      new_line.product_category_reference = product_template.product_category
      new_line.catalog_pricetag_reference = catalog_pricetag_key
      new_line.product_instance_reference = product_instance_key
 
      if hasattr(product_instance, 'unit_price'):
        new_line.unit_price = product_instance.unit_price
      else:
        new_line.unit_price = product_template.unit_price
      
      new_line.quantity = uom.format_value('1', new_line.product_uom) # decimal formating required
      new_line.discount = uom.format_value('0', uom.UOM(digits=4)) # decimal formating required
      entry._lines.append(new_line)

      
class ProductSubtotalCalculate(transaction.Plugin):
  
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
    
    for line in entry._lines:
      if hasattr(line, 'product_instance_reference'):
        
        line.subtotal = line.unit_price * line.quantity # decimal formating required
        line.discount_subtotal = line.subtotal - (line.subtotal * line.discount) # decimal formating required
       
        line.debit = uom.format_value('0', line.uom) # decimal formating required
        line.credit = line.discount_subtotal # decimal formating required
        
        
class PayPalPayment(transaction.Plugin):
  # ovaj plugin ce biti subscribed na mnostvo akcija, medju kojima je i add_to_cart
  
  currency = ndb.SuperKeyProperty('5', kind=uom.Unit)
  reciever_email = ndb.SuperStringProperty('6')
  business = ndb.SuperStringProperty('7')
  
  def run(self, journal, context):
    # u contextu add_to_cart akcije ova funkcija radi sledece:
    
    entry = context.transaction.entities[journal.key.id()]
    
    entry.currency = uom.get_uom(self.currency)
    entry.paypal_reciever_email = self.reciever_email
    entry.paypal_business = self.business
    
    
class OrderTotalCalculate(transaction.Plugin):
  
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
    
    untaxed_amount = uom.format_value('0', entry.currency) # decimal formating required
    tax_amount = uom.format_value('0', entry.currency) # decimal formating required
    total_amount = uom.format_value('0', entry.currency) # decimal formating required
    
    for line in entry._lines:
      if hasattr(line, 'product_instance_reference'):
        untaxed_amount += line.subtotal
        tax_amount += line.tax_subtotal
        total_amount += line.subtotal + line.tax_subtotal
    
    entry.untaxed_amount = untaxed_amount
    entry.tax_amount = tax_amount
    entry.total_amount = total_amount

class LineTax():
  
  def __init__(self, name, formula):
     self.name = name
     self.formula = formula

class Tax(transaction.Plugin):
  
  name = ndb.SuperStringProperty('5')
  formula = ndb.SuperPickleProperty('6')
  exclusion = ndb.SuperBooleanProperty('7', default=False)
  address_type = ndb.SuperStringProperty('8')
  locations = ndb.SuperPickleProperty('9')
  carriers = ndb.SuperKeyProperty('10', repeated=True)
  product_categories = ndb.SuperKeyProperty('11', kind='17', repeated=True)
  
  
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
    
    allowed = self.validate_tax(entry)
    
    for line in entry._lines:
      if (self.carriers):
        if (self.carriers.count(line.carrier_reference)):
            if not (allowed):
              del line.taxes[self.key.urlsafe()]
            elif allowed:
              line.taxes[self.key.urlsafe()] = LineTax(self.name, self.formula)
              
      elif (self.product_categories):
        if (self.product_categories.count(line.product_category)):
          if not (allowed):
              del line.taxes[self.key.urlsafe()]
          elif allowed:
              line.taxes[self.key.urlsafe()] = LineTax(self.name, self.formula)
  
  def validate_tax(self, entry):
 
    address_key = '%s_address' % self.address_type
    address = getattr(entry, address_key) 
  
    if not (self.exclusion):
      allowed = True
      for loc in self.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = False
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = False
            break
        elif not (loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
            allowed = False
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
            allowed = False
            break
    # Shipping only at the following locations
    else:
      allowed = False
      for loc in self.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = True
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = True
            break
        elif not (loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
            allowed = True
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
            allowed = True
            break


    if (allowed):
      # ako je taxa konfigurisana za carriers onda se proverava da li entry ima carrier na kojeg se taxa odnosi
      if (self.carriers):
        allowed = False
        if ((entry.carrier_reference) and (self.carrieres.count(entry.carrier_reference))):
          allowed = True
          break
      # ako je taxa konfigurisana za kategorije proizvoda onda se proverava da li entry ima liniju na koju se taxa odnosi
      elif (self.product_categories):
        allowed = False
        for line in entry._lines:
          if (self.product_categories.count(line.product_category)):
            allowed = True
            break
          
    return allowed
  
class TaxSubtotalCalculate(transaction.Plugin):
  
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
    tax_line = False
    tax_total = uom.format_value('0', entry.currency)
    
    for line in entry._lines:
      
      # 'key' key needs to be something else
      if transaction.Category.build_key('key') in line.categories:
         tax_line = line
      
      tax_subtotal = uom.format_value('0', line.uom)
      for tax_key, tax in line.taxes.items():
          if (tax.formula[0] == 'percent'):
              tax_amount = uom.format_value(tax.formula[1], line.uom) * uom.format_value('0.01', line.uom) # moze i "/ DecTools.form('100')"
              tax_subtotal += line.credit * tax_amount
              tax_total += line.credit * tax_amount
          elif (tax.formula[0] == 'amount'):
              tax_amount = uom.format_value(tax.formula[1], line.uom)
              tax_subtotal += tax_amount
              tax_total += tax_amount
              
      line.tax_subtotal = tax_subtotal
       
    if tax_line:
       tax_line.debit = uom.format_value('0', line.uom)
       tax_line.credit = tax_total
    else:
       tax_line = transaction.Line()
       tax_line.categories.append(transaction.Category.build_key('key'))
       tax_line.description = 'Sales Tax'
       tax_line.line_uom = entry.currency
       tax_line.debit = uom.format_value('0', entry.currency)
       tax_line.credit = tax_total 
       tax_line.sequence = entry._lines[-1].sequence + 1
       entry._lines.append(tax_line)
      
    

class Field:
  
  def __init__(self, name, value):
    
    self.name = name
    self.value = value
    

class EntryFieldAutoUpdate(transaction.Plugin):
  
  fields = ndb.SuperPickleProperty('5')
  
  
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
 
    for field in self.fields:
      if field.name not in ['name', 'company', 'journal', 'created', 'updated']:
         # control required
         setattr(entry, field.name, field.value)
 
class CarrierLine:
  
  def __init__(self, name, exclusion=False, active=True, locations=None, rules=None):
    self.name = name
    self.exclusion = exclusion
    self.active = active
    self.locations = locations
    self.rules = rules
  
class CarrierLineRule:
  
  def __init__(self, condition, price):
    self.condition = condition
    self.price = price


class Carrier(transaction.Plugin):
  
  name = ndb.SuperStringProperty('5')
  lines = ndb.SuperPickleProperty('6')
  
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
    valid_lines = []
    
    for carrier_line in self.lines:
      if self.validate_line(carrier_line, entry):
         valid_lines.append(carrier_line)
      
    carrier_price = self.calculate_lines(valid_lines, entry)
    
    if 'carriers' not in context.response:
        context.response['carriers'] = []
    
    context.response['carriers'].append({
                                     'name' : self.name,
                                     'price': carrier_price,
                                     'id' : self.key.urlsafe(),
                                  })
    
    
  def calculate_lines(self, valid_lines, entry):
  
      weight_uom = uom.get_uom(uom.Unit.build_key('kg', parent=uom.Measurement.build_key('metric')))
      volume_uom = uom.get_uom(uom.Unit.build_key('m3', parent=uom.Measurement.build_key('metric')))
     
      weight = uom.format_value('0', weight_uom)
      volume = uom.format_value('0', volume_uom)
     
     
      for line in entry._lines:
        
        line_weight = line._weight[0]
        line_weight_uom = uom.get_uom(ndb.Key(urlsafe=line._weight[1]))
       
        line_volume = line._volume[0]
        line_volume_uom = uom.get_uom(ndb.Key(urlsafe=line._volume[1]))
       
        weight += uom.convert_value(line_weight, line_weight_uom, weight_uom)
        volume += uom.convert_value(line_volume, line_volume_uom, volume_uom)
       
      carrier_prices = []
               
      for carrier_line in valid_lines:
        line_prices = []
        for rule in carrier_line.rules:
          condition = rule.condition
          # this regex needs more work
          condition = self.format_value(condition)
          price = rule.price
         
          if safe_eval(condition, {'weight' : weight, 'volume' : volume, 'price' : price}):
            price = self.format_value(price)
            price = safe_eval(price, {'weight' : weight, 'volume' : volume, 'price' : price})
            line_prices.append(price)
          
        carrier_prices.append(min(line_prices))
        
      # lowest price possible from all lines
      return min(carrier_prices)
          
  def format_value(self, value):
    
    def run_format(match):
         matches = match.groups()
         return "Decimal('%s')" % uom.format_value(matches[0], uom.get_uom(ndb.Key(urlsafe=matches[1])))            
          # this regex needs more work
    value = re.sub('\((.*)\,(.*)\)', run_format, value)
    
    return value
          
          
    
  def validate_line(self, carrier_line, entry):
 
    address_key = '%s_address' % self.address_type
    address = getattr(entry, address_key) 
    
    # Shipping everywhere except at the following locations
    if not (carrier_line.exclusion):
      allowed = True
      for loc in carrier_line.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = False
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = False
            break
        elif not (loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
            allowed = False
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
            allowed = False
            break
    # Shipping only at the following locations
    else:
      allowed = False
      for loc in self.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = True
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = True
            break
        elif not (loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
            allowed = True
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
            allowed = True
            break


    if (allowed):
      
      allowed = False
      price = entry.amount_total
      
      weight_uom = uom.get_uom(uom.Unit.build_key('kg', parent=uom.Measurement.build_key('metric')))
      volume_uom = uom.get_uom(uom.Unit.build_key('m3', parent=uom.Measurement.build_key('metric')))
      
      weight = uom.format_value('0', weight_uom)
      volume = uom.format_value('0', volume_uom)
       
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
   
          if safe_eval(condition, {'weight' : weight, 'volume' : volume, 'price' : price}):
             allowed = True
             break
  
    return allowed
  
class UpdateProductLine(transaction.Plugin):
   
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
  
    i = 0
    for line in entry._lines:
      if hasattr(line, 'catalog_pricetag_reference') and hasattr(line, 'product_instance_reference'):
        if context.args.get('quantity')[i] <= 0:
            entry._lines.pop(i)
        else:
            line.quantity = uom.format_value(context.args.get('quantity')[i], line.product_uom)
        line.discount = uom.format_value(context.args.get('discount')[i], uom.UOM(digits=4))
      i += 1
      
class PayPalInit(transaction.Plugin):
  
  # user plugin, saved in datastore
  
  def run(self, journal, context):
    
    ipns = log.Record.query(log.Record.ipn_txn_id == context.args['txn_id']).fetch()
    if len(ipns):
      for ipn in ipns:
        if (ipn.payment_status == context.args['payment_status']):
          raise PluginValidationError('duplicate_entry')
      entry = ipns[0].parent_entity
      if context.args['custom']:
         if (entry.key.urlsafe() == context.args['custom']):
           
            kwds = {'log_entity' : False}
            kwds.update(dict([('ipn_%s' % key, value) for key,value in context.args.items()])) # prefix
            context.log.entities.append((entry, kwds))
            
         else:
            raise PluginValidationError('invalid_ipn')
      else:
        raise PluginValidationError('invalid_ipn')
      
    else:    
      
      if not context.args['custom']:
        raise PluginValidationError('invalid_ipn')
      else:
        try:
          entry_key = ndb.Key(urlsafe=context.args['custom']) 
          entry = entry_key.get()
        except Exception as e:
          raise PluginValidationError('invalid_ipn')
        
    if not entry:
      raise PluginValidationError('invalid_ipn')
    
    kwds = {'log_entity' : False}
    kwds.update(dict([('ipn_%s' % key, value) for key,value in context.args.items()])) # prefix
    context.log.entities.append((entry, kwds))
    
    if not context.transaction.group:
       context.transaction.group = entry.parent_entity
       
    context.transaction.entities[journal.key.id()] = entry
    
    if not self.validate_entry(entry, context):
       raise PluginValidationError('fraud_check')
    
  def validate_entry(self, entry, context):
      
      mismatches = []
      ipn = context.args
      shipping_address = entry.shipping_address.get()
      shipping_address_country, shipping_address_region = ndb.get_multi([shipping_address.country, shipping_address.region])
    
      if (entry.paypal_email != ipn['receiver_email']) or (entry.paypal_email != ipn['business']):
          mismatches.append('receiver_email_or_business')
      if (entry.currency.code != ipn['mc_currency']):
          mismatches.append('mc_currency')
      if (entry.total_amount != uom.format_value(ipn['mc_gross'], entry.currency)):
          mismatches.append('mc_gross')
      if (entry.tax_amount != uom.format_value(ipn['tax'], entry.currency)):
          mismatches.append('tax')
          
      if (entry.reference != ipn['invoice']): # entry.reference bi mozda mogao da bude user.key.id-entry.key.id ili mozda entry.key.id ?
          mismatches.append('invoice')
      
      if (shipping_address_country.name != ipn['address_country']):
          mismatches.append('address_country')    
      if (shipping_address_country.code != ipn['address_country_code']):
          mismatches.append('address_country_code')
      if (shipping_address.city != ipn['address_city']):
          mismatches.append('address_city')
      if (shipping_address.name != ipn['address_name']):
          mismatches.append('address_name')
      
      state = shipping_address_region.name # po defaultu sve ostale drzave koriste name? ili i one isto kod?
      if shipping_address_country.code == 'US': # paypal za ameriku koristi 2 digit iso standard kodove za njegove stateove
         state = shipping_address_region.code
         
      if (state != ipn['address_state']):
          mismatches.append('address_state')
      if (shipping_address.address != ipn['address_street']): 
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
    
    