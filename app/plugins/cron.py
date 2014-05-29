# -*- coding: utf-8 -*-
'''
Created on May 29, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.srv import event

from google.appengine.datastore.datastore_query import Cursor

class DomainCatalogProcessRun(event.Plugin):
  
  page_size = ndb.SuperIntegerProperty(default=10)
  
  def run(self, context):
    DomainCatalogProcess = context.models['83']
    Domain = context.models['6']
    config_key = DomainCatalogProcess.build_key('config')
    config = config_key.get()
    if not config:
      config = DomainCatalogProcess(key=config_key)
    cursor = None
    if config.current_cursor and config.current_more:
      cursor = Cursor(urlsafe=config.current_cursor)
    entities, cursor, more = Domain.query().order(Domain.created).fetch_page(self.page_size, keys_only=True, start_cursor=cursor)
    if cursor:
      cursor = cursor.urlsafe()
    for key in entities:
      data = {'action_id': 'cron',
              'action_model': '35',
              'domain': key.urlsafe()}
      context.callback_payloads.append(('callback', data))
    config.current_cursor = cursor
    config.current_more = more
    config.put()
    