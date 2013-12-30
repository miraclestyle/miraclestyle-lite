# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import decimal
import datetime

from app import ndb
from app.srv import transaction
from app.srv import rule

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
  locations = ndb.PickleProperty('7')
  
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
         entry.billing_address = transaction.Address(
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
                                  )
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
      entry = Entry()
      entry.journal = journal_key
      entry.company = company_key
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
        line.quantity = line.quantity + decimal.Decimal('1') # decmail formating required
        line_exists = True
        break
      
    if not (line_exists):
      product_template = product_template_key.get()
      product_instance = product_instance_key.get()
      product_category = product_template.product_category.get()
      product_category_complete_name = product_category.complete_name
      product_uom = product_template.product_uom.get()
      product_uom_category = product_uom.key.parent().get()
      
      new_line = transaction.Line()
      new_line.sequence = entry.lines[-1].sequence + decimal.Decimal('1')
      new_line.categories.append(transaction.Category.build_key('key')) # ovde ide ndb.Key('Category', 'key')
      new_line.description = product_template.name
      if (hasattr(product_template, 'product_instance_count') and product_template.product_instance_count > 1000):
        new_line.description += '\n %s' % variant_signature
      else:
        if (custom_variants):
          new_line.description += '\n %s' % variant_signature
          
      new_line.uom = transaction.UOM(
                             category=product_uom_category.name, 
                             name=product_uom_category.name, 
                             symbol=product_uom_category.symbol, 
                             rounding=product_uom_category.rounding, 
                             digits=product_uom_category.digits
                             ) # currency uom!!
      
      new_line.product_uom = transaction.UOM(
                                     category=product_uom_category.name, 
                                     name=product_uom.name, 
                                     symbol=product_uom.symbol, 
                                     rounding=product_uom.rounding, 
                                     digits=product_uom.digits
                                     )
      
      new_line.product_category_complete_name = product_category_complete_name
      new_line.product_category_reference = product_template.product_category
      new_line.catalog_pricetag_reference = catalog_pricetag_key
      new_line.product_instance_reference = product_instance_key
      if ('unit_price' in product_instance._properties):
        new_line.unit_price = product_instance.unit_price
      else:
        new_line.unit_price = product_template.unit_price
      new_line.quantity = decimal.Decimal('1') # decimal formating required
      new_line.discount = decimal.Decimal('0.0') # decimal formating required
      entry._lines.append(new_line)

      
class ProductSubtotalCalculate(transaction.Plugin):
  
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
    
    for line in entry._lines:
      if hasattr(line, 'product_instance_reference'):
        line.subtotal = line.unit_price * line.quantity # decimal formating required
        line.discount_subtotal = line.subtotal - (line.subtotal * line.discount) # decimal formating required
        line.debit = decimal.Decimal('0.0') # decimal formating required
        line.credit = line.discount_subtotal # decimal formating required
