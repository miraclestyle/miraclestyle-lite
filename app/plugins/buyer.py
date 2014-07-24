# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import time
import hashlib

from app import orm
from app.util import *


def generate_internal_id(address):
  internal_id = u'%s-%s-%s-%s-%s-%s-%s-%s' % (str(time.time()), random_chars(10),
                                              address.name, address.city, address.postal_code,
                                              address.street, address.default_shipping, address.default_billing)
  address.internal_id = hashlib.md5(internal_id.encode('utf8')).hexdigest()


class AddressesUpdateSet(orm.BaseModel):
  
  def run(self, context):
    if context._addresses.addresses:
      default_billing = 0
      default_shipping = 0
      for i, address in enumerate(context._addresses.addresses):
        try:
          # Ensure that the internal id is never changed by the client.
          address.internal_id = context._addresses._original.addresses[i].internal_id
        except IndexError as e:
          # This is a new record, so force-feed it the internal_id.
          generate_internal_id(address)
        if address.default_shipping:
          default_shipping = i
        if address.default_billing:
          default_billing = i
        address.default_shipping = False
        address.default_billing = False
      context._addresses.addresses[default_shipping].default_shipping = True
      context._addresses.addresses[default_billing].default_billing = True
