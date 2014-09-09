# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib

from app import orm
from app.tools import oauth2
from app.tools.base import *
from app.util import *


class DomainCreateWrite(orm.BaseModel):
  
  def run(self, context):
    config_input = context.input.copy()
    Configuration = context.models['57']
    config = Configuration(parent=context.user.key, configuration_input=config_input, setup='setup_domain', state='active')
    config.put()
    context._config = config
