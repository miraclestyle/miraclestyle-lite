# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import datetime

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
    

class Base:
  'Base class for plugins'
  
  category = ''
  
  
class Location:
  
  def __init__(self, country, region=None, postal_code_from=None, postal_code_to=None, city=None):
    self.country = country
    self.region = region
    self.postal_code_from = postal_code_from
    self.postal_code_to = postal_code_to
    self.city = city
    


class AddressRule:
  
  def __init__(self, exclusion, address_type, locations, allowed_states=None):
    self.exclusion = exclusion
    self.address_type = address_type
    self.locations = locations
    self.allowed_states = allowed_states
  
  def run(self, entry):
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
      return entry
    else:
      return 'ABORT'
     
  
  def validate_address(self, address):
    allowed = False
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
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code_from >= loc.postal_code_from and address.postal_code_to <= loc.postal_code_to)):
            allowed = False
            break
    # Shipping only at the following locations
    else:
      for loc in self.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = True
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = True
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code_from >= loc.postal_code_from and address.postal_code_to <= loc.postal_code_to)):
            allowed = True
            break
    return allowed

  
  
class CartInit(Base):
  
  category = 'sys_cart_init'
  
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
      context.entries[entry.journal.code] = entry
