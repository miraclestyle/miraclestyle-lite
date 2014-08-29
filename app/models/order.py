# -*- coding: utf-8 -*-
'''
Created on Aug 30, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, util, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.marketing import *


class LineTax(orm.BaseModel):
  
  _kind = xx
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  code = orm.SuperStringProperty('2', required=True, indexed=False)
  formula = orm.SuperStringProperty('3', required=True, indexed=False)
