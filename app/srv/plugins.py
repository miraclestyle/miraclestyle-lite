# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import datetime
 
from app import ndb
from app.srv import transaction, rule, uom
  
from app.core import buyer

Entry = transaction.Entry
Journal = transaction.Journal
Context = transaction.Context

class PluginValidationError(Exception):
  pass

__SYSTEM_PLUGINS = []

def get_system_plugins(action=None, journal_code=None):
    # gets registered system journals
    global __SYSTEM_PLUGINS
    
    returns = []
    
    if action:
      for plugin in __SYSTEM_PLUGINS:
          if action in plugin[1] and journal_code == plugin[0]:
             returns.append(plugin[2])
    else:
      returns = [plugin[2] for plugin in __SYSTEM_PLUGINS]
              
    return returns
  
def register_system_plugins(*args):
    global __SYSTEM_PLUGINS
    __SYSTEM_PLUGINS.extend(args)
  
  
class Location:
  
  def __init__(self, country, region=None, postal_code_from=None, postal_code_to=None, city=None):
    self.country = country
    self.region = region
    self.postal_code_from = postal_code_from
    self.postal_code_to = postal_code_to
    self.city = city
    


class AddressRule(transaction.Plugin):
  
  KIND_ID = 54
  
  exclusion = ndb.SuperBooleanProperty('5', default=False)
  address_type = ndb.SuperStringProperty('6')
  locations = ndb.SuperPickleProperty('7')
  
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
    
    buyer_addresses = []
    valid_addresses = []
    default_address = None
    address_reference_key = '%s_address_reference' % self.address_type
    address_key = '%s_address' % self.address_type
    address = getattr(entry, address_key, None)
    address_reference = getattr(entry, address_reference_key, None)
 
    if address_reference is not None:
      buyer_addresses.append(address_reference.get())
    else:
      buyer_addresses = buyer.Address.query(ancestor=entry.partner).fetch()
      
    for buyer_address in buyer_addresses:
      if self.validate_address(buyer_address):
         valid_addresses.append(buyer_address)
         if getattr(buyer_address, 'default_%s' % self.address_type):
             default_address = buyer_address
    
    if not default_address and valid_addresses:
      default_address = valid_addresses[0]
    if default_address:
      if address_reference:
        setattr(entry, address_reference_key, default_address.key)
      if address:
         address_country = default_address.country.get()
         address_region = default_address.region.get()
         setattr(entry, address_key, transaction.Address(
                                  name=address.name, 
                                  country=address_country.name, 
                                  country_code=address_country.code, 
                                  region=address_region.name, 
                                  region_code=address_region.code, 
                                  city=address.city, 
                                  postal_code=address.postal_code, 
                                  street_address=address.street_address, 
                                  street_address2=address.street_address2, 
                                  email=address.email, 
                                  telephone=address.telephone
                                  ))
    
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
  
  KIND_ID = 55
  
  def run(self, journal, context):
    # ucitaj postojeci entry na kojem ce se raditi write
    catalog_key = context.args.get('catalog')
    user_key = context.user.key
    catalog = catalog_key.get()
    company = catalog.company.get()
    company_key = company.key
    journal_key = journal.get_key(journal.code, namespace=catalog.key.namespace())
 
    entry = Entry.query(Entry.journal == journal_key, 
                        Entry.company == company_key, Entry.state.IN(['cart', 'checkout', 'processing']),
                        Entry.party == user_key
                        ).get()
    # ako entry ne postoji onda ne pravimo novi entry na kojem ce se raditi write
    if not (entry):
      
      company_address_country = company.country.get()
      company_address_region = company.region.get()
      
      entry = Entry()
      entry.journal = journal_key
      entry.company = company_key
      entry.company_address = transaction.Address(
                                  name=company.name, 
                                  country=company_address_country.name, 
                                  country_code=company_address_country.code, 
                                  region=company_address_region.name, 
                                  region_code=company_address_region.code, 
                                  city=company.city, 
                                  postal_code=company.postal_code, 
                                  street_address=company.street_address, 
                                  street_address2=company.street_address2, 
                                  email=company.email, 
                                  telephone=company.telephone
                                  )
      entry.state = 'cart'
      entry.date = datetime.datetime.today()
      entry.party = user_key
    # proveravamo da li je entry u state-u 'cart'
    
    context.entity = entry
    rule.Engine.run(context)
    
    if not context.entity._rule_action_permissions[context.action]['executable']:
      # ukoliko je entry u drugom state-u od 'cart' satate-a, onda abortirati pravljenje entry-ja
      # taj abortus bi trebala da verovatno da bude neka "error" class-a koju client moze da interpretira useru
      raise PluginValidationError('entry_not_in_cart_state')
    else:
      context.entries[journal.code] = entry
      

class ProductToLine(transaction.Plugin):
    
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
   
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
    
    entry = context.entries[journal.code]
    
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
    
    entry = context.entries[journal.code]
    
    entry.currency = uom.get_uom(self.currency)
    
    
class OrderTotalCalculate(transaction.Plugin):
  
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
    
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
  product_categories = ndb.SuperKeyProperty('11', kind='app.core.misc.ProductCategory', repeated=True)
  
  
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
    
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
      # ako je taxa konfigurisana za kategorije proizvoda onda se proverava da li entry ima liniju na koju se taxa odnosi
      elif (self.product_categories):
        allowed = False
        for line in entry.lines:
          if (self.product_categories.count(line.product_category)):
            allowed = True
    return allowed
  
class TaxSubtotalCalculate(transaction.Plugin):
  
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
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
    
    entry = context.entries[journal.code]
    context.entity = entry
    rule.Engine.run(context)
    
    if not context.entity._rule_action_permissions[context.action]['executable']:
      raise PluginValidationError('action_forbidden')
    
    for field in self.fields:
      if field.name not in ['name', 'company', 'journal', 'created', 'updated']:
        if context.entity._rule_field_permissions[field.name]['writable']:
          setattr(entry, field.name, field.value)
        else:
          raise PluginValidationError('field_not_writable')

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
    
    entry = context.entries[journal.code]
    valid_lines = []
    
    for carrier_line in self.lines:
      if self.validate_line(carrier_line, entry):
         valid_lines.append(carrier_line)
      
    self.calculate_lines(valid_lines, entry)
    
    
  def calculate_lines(self, valid_lines, entry):
      pass
      
    
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
      weight = uom.format_value('0')
      volume = uom.format_value('0')
      price = entry.amount_total
      for line in entry._lines:
        weight += uom.convert_value(line._product_weight, line._product_weight_uom, x)
        volume += uom.convert_value(line.product_volume, line._product_volume_uom, x)
      
      for rule in carrier_line.rules:
        total_weight = uom.convert_value(weight, x, rule.weight_uom)
        total_volume = uom.convert_value(volume, x, rule.volume_uom)
        total_price = uom.convert_value(price, entry.currency, rule.currecy_uom)
        
      # ako je taxa konfigurisana za carriers onda se proverava da li entry ima carrier na kojeg se taxa odnosi
      if (self.carriers):
        allowed = False
        if ((entry.carrier_reference) and (self.carrieres.count(entry.carrier_reference))):
          allowed = True
      # ako je taxa konfigurisana za kategorije proizvoda onda se proverava da li entry ima liniju na koju se taxa odnosi
      elif (self.product_categories):
        allowed = False
        for line in entry.lines:
          if (self.product_categories.count(line.product_category)):
            allowed = True
    return allowed
  
class UpdateProductLine(transaction.Plugin):
   
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
    context.entity = entry
    rule.Engine.run(context)
    
    if not context.entity._rule_action_permissions[context.action]['executable']:
      raise PluginValidationError('action_forbidden')
    
    i = 0
    for line in entry._lines:
      if hasattr(line, 'catalog_pricetag_reference') and hasattr(line, 'product_instance_reference'):
        if context.entity._rule_field_permissions['quantity']['writable']:
          if context.args.get('quantity')[i] <= 0:
            entry._lines.pop(i)
          else:
            line.quantity = uom.format_value(context.args.get('quantity')[i], line.product_uom)
        if context.entity._rule_field_permissions['discount']['writable']:
          line.discount = uom.format_value(context.args.get('discount')[i], uom.UOM(digits=4))
      i += 1
      