# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm
from app.util import *


class BuyerUpdateSet(orm.BaseModel):
  
  def run(self, context):
    original_addresses = context._buyer._original.addresses.value
    addresses = context._buyer.addresses.value
    if addresses:
      default_billing = 0
      default_shipping = 0
      for i, address in enumerate(addresses):
        original_address = get_attr(original_addresses, i)
        if ((original_address is None) or (original_address and not original_address.default_shipping)) and address.default_shipping:
          default_shipping = i
        if ((original_address is None) or (original_address and not original_address.default_billing)) and address.default_billing:
          default_billing = i
        address.default_shipping = False
        address.default_billing = False
      addresses[default_shipping].default_shipping = True
      addresses[default_billing].default_billing = True
