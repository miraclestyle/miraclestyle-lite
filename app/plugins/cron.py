# -*- coding: utf-8 -*-
'''
Created on May 29, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.datastore.datastore_query import Cursor

from app import orm
from app.util import *


class CronConfigProcessCatalogs(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    limit = self.cfg.get('page', 10)
    Account = context.models['11']  # @todo Not sure if this is ok!? Perhaps we shoud target Seller?
    cursor = None
    if context._cronconfig.data.get('more'):
      cursor = Cursor(urlsafe=context._cronconfig.data.get('cursor'))
    entities, cursor, more = Account.query().order(Account.created).fetch_page(limit, start_cursor=cursor, keys_only=True)
    if cursor:
      cursor = cursor.urlsafe()
    context._cronconfig.data['cursor'] = cursor
    context._cronconfig.data['more'] = more
    for key in entities:
      data = {'action_id': 'cron',
              'action_model': '35',
              'account': key.urlsafe()}
      context._callbacks.append(('callback', data))
