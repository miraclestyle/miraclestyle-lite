# -*- coding: utf-8 -*-
'''
Created on Sep 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import datetime
import copy

from google.appengine.api import search

from app import orm
from app.tools.base import *
from app.util import *


class SellerCronGenerateFeedbackStats(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    limit = self.cfg.get('interval', 10)
    Catalog = context.models['31']
    catalogs = Catalog.query(Catalog.state == 'published',
                             Catalog.discontinue_date <= datetime.datetime.now()).fetch(limit=limit)
    for catalog in catalogs:
      data = {'action_id': 'discontinue',
              'action_model': '31',
              'message': 'Expired',
              'key': catalog.key.urlsafe()}
      context._callbacks.append(('callback', data))
