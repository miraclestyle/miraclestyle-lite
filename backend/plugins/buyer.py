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
      initial_default_billing = 0
      initial_default_shipping = 0
      for i, address in enumerate(addresses):
        original_address = get_attr(original_addresses, i)
        if (original_address and original_address.default_billing):
          initial_default_billing = i
        if (original_address and original_address.default_shipping):
          initial_default_shipping = i
        if address.default_shipping:
          default_shipping = i
        if address.default_billing:
          default_billing = i
        address.default_shipping = False
        address.default_billing = False
      if (default_billing is not None):
        addresses[default_billing].default_billing = True
      else:
        addresses[initial_default_billing].default_billing = True
      if (default_shipping is not None):
        addresses[default_shipping].default_shipping = True
      else:
        addresses[initial_default_shipping].default_shipping = True
