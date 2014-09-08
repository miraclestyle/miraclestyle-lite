# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import time
import hashlib

from app import orm
from app.util import *


class AddressesUpdateSet(orm.BaseModel):
  
  def run(self, context):
    addresses = context._addresses.addresses.value
    if addresses:
      default_billing = 0
      default_shipping = 0
      for i, address in enumerate(addresses):
        if address.default_shipping:
          default_shipping = i
        if address.default_billing:
          default_billing = i
        address.default_shipping = False
        address.default_billing = False
      addresses[default_shipping].default_shipping = True
      addresses[default_billing].default_billing = True
