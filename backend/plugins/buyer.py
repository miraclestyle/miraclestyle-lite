# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import orm
from util import *


class BuyerUpdateSet(orm.BaseModel):
  
  def run(self, context):
    original_addresses = context._buyer._original.addresses.value
    addresses = context._buyer.addresses.value
    if addresses:
      default_billing = None
      default_shipping = None
      original_default_billing = None
      original_default_shipping = None
      for i, address in enumerate(addresses):
        if address._state != 'deleted':
          original_address = get_attr(original_addresses, i)
          if original_address and original_address.default_billing:
            original_default_billing = i
          if original_address and original_address.default_shipping:
            original_default_shipping = i
          if address.default_billing:
            default_billing = i
          if address.default_shipping:
            default_shipping = i
        address.default_billing = False
        address.default_shipping = False
      if (default_billing is not None):
        addresses[default_billing].default_billing = True
      elif (original_default_billing is not None):
        addresses[original_default_billing].default_billing = True
      else:
        for address in addresses:
          if address._state != 'deleted':
            address.default_billing = True
            break
      if (default_shipping is not None):
        addresses[default_shipping].default_shipping = True
      elif (original_default_shipping is not None):
        addresses[original_default_shipping].default_shipping = True
      else:
        for address in addresses:
          if address._state != 'deleted':
            address.default_shipping = True
            break
