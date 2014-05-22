# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import time
import hashlib
import copy

from app import ndb, settings, memcache, util
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


def generate_internal_id(address):
  internal_id = '%s-%s-%s-%s-%s-%s-%s-%s' % (str(time.time()), util.random_chars(10),
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
    if entity.addresses and len(entity.addresses):
      
      @ndb.tasklet
      def async(address):
        if address.country:
          country = yield address.country.get_async()
          address._country = country.name
        if address.region:
          region = yield address.region.get_async()
          address._region = region.name
        raise ndb.Return(address)
      
      @ndb.tasklet
      def helper(addresses):
        addresses = yield map(async, addresses)
        raise ndb.Return(addresses)
      
      entity.addresses = helper(entity.addresses).get_result()
    context.entities[context.model.get_kind()] = entity
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])


class AddressSet(event.Plugin):
  
  def run(self, context):
    if context.values['77'].addresses:
      default_billing = 0
      default_shipping = 0
      for i, address in enumerate(context.values['77'].addresses):
        try:
          # Ensure that the internal id is never changed by the client.
          address.internal_id = context.entities['77'].addresses[i].internal_id
        except IndexError as e:
          # This is a new record, so force-feed it the internal_id.
          generate_internal_id(address)
        if address.default_shipping:
          default_shipping = i
        if address.default_billing:
          default_billing = i
        address.default_shipping = False
        address.default_billing = False
      context.values['77'].addresses[default_shipping].default_shipping = True
      context.values['77'].addresses[default_billing].default_billing = True


class CollectionRead(event.Plugin):
  
  def run(self, context):
    user_key = context.input.get('user')
    user = user_key.get()
    entity_key = context.model.build_key(user.key_id_str, parent=user.key)
    entity = entity_key.get()
    if entity is None:
      entity = context.model(key=entity_key)
    if entity.domains and len(entity.domains):
      entity._domains = ndb.get_multi(entity.domains)
    context.entities[context.model.get_kind()] = entity
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])
