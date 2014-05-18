# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

import time
import hashlib
import copy

from app import ndb, util
from app.srv import event

def generate_internal_id(address):
  internal_id = '%s-%s-%s-%s-%s-%s-%s-%s' %  (str(time.time()), util.random_chars(10),
                                              address.name, address.city, address.postal_code,
                                              address.street, address.default_shipping, address.default_billing)
  address.internal_id = hashlib.md5(internal_id).hexdigest()

class AddressRead(event.Plugin):
  
  def run(self, context):
    user_key = context.input.get('user')
    user = user_key.get()
    entity_key = context.model.build_key(user.key_id_str, parent=user.key)
    entity = entity_key.get()
    if entity is None:
      entity = context.model(key=entity_key)
 
    context.entities[context.model.get_kind()] = entity
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])

class AddressUpdate(event.Plugin):
  
  def run(self, context):
    supplied = context.input.get('addresses')
    if supplied:
      shipping = True
      billing = True
      default_billing = 0
      default_shipping = 0
      for i,addr in enumerate(supplied):
        try:
          existing = context.values['77'].addresses[i]
          addr.internal_id = existing.internal_id # ensure that the internal id will never be changed by the client
          # we cant use the rule engine here cuz we need to allow user to remove/append the addresses
        except IndexError as e:
          generate_internal_id(addr) # this is a new record so force-feed him the internal_id
        
        if addr.default_shipping:
          default_shipping = i
        if addr.default_billing:
          default_billing = i
             
        addr.default_shipping = False
        addr.default_billing = False
           
      supplied[default_shipping].default_shipping = True
      supplied[default_billing].default_billing = True
           
    context.values['77'].addresses = supplied  
    
# @todo AddressRead is indentical should we merge this?    
class CollectionRead(event.Plugin):
  
  def run(self, context):
    user_key = context.input.get('user')
    user = user_key.get()
    entity_key = context.model.build_key(user.key_id_str, parent=user.key)
    entity = entity_key.get()
    if entity is None:
      entity = context.model(key=entity_key)
    context.entities[context.model.get_kind()] = entity
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])