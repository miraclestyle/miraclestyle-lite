# -*- coding: utf-8 -*-
'''
Created on May 29, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.datastore.datastore_query import Cursor

from app import orm, util


class ProcessCatalogs(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    page_size = self.cfg.get('page', 10)
    CronConfig = context.models['83']
    Domain = context.models['6']
    config_key = CronConfig.build_key('process_catalogs_config')
    config = config_key.get()
    if not config:
      config = CronConfig(key=config_key)
    cursor = None
    if config.data.get('current_cursor') and config.data.get('current_more'):
      cursor = Cursor(urlsafe=config.data.get('current_cursor'))
    entities, cursor, more = Domain.query().order(Domain.created).fetch_page(page_size, start_cursor=cursor, keys_only=True)
    if cursor:
      cursor = cursor.urlsafe()
    for key in entities:
      data = {'action_id': 'cron',
              'action_model': '35',
              'domain': key.urlsafe()}
      context._callbacks.append(('callback', data))
    config.data['current_cursor'] = cursor
    config.data['current_more'] = more
    config.put()
