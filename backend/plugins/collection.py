# -*- coding: utf-8 -*-
'''
Created on Sep 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import datetime
import orm

__all__ = ['CollectionCronNotify']


class CollectionCronNotify(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    Collection = context.models['18']
    Catalog = context.models['35']
    collections = Collection.query(Collection.notify == True).fetch_page(1, cursor=context.input.get('cursor'))
    collection = None
    if len(collections) and len(collections[0]):
      collection = collections[0][0]
    else:
      return # nothing found
    context.entity = collection
    context._collection = collection
    today_minus_7_days = datetime.datetime.now() - datetime.timedelta(days=7)

    all_published_catalogs = []
    all_discontinued_catalogs = []

    for seller_key in collection.sellers:
      published_catalogs = Catalog.query(ancestor=seller_key,
                                         Catalog.published_date > today_minus_7_days,
                                         Catalog.state == 'published').fetch_async(use_memcache=False, use_cache=False)
      discontinued_catalogs = Catalog.query(ancestor=seller_key,
                                            Catalog.updated > today_minus_7_days,
                                            Catalog.state == 'discontinued').fetch_async(use_memcache=False, use_cache=False)
      all_discontinued_catalogs.extend(discontinued_catalogs)
      all_published_catalogs.extend(published_catalogs)

    orm.get_async_results(all_published_catalogs, all_discontinued_catalogs) # waits for all rpcs above to complete

    context._all_published_catalogs = all_published_catalogs
    context._all_discontinued_catalogs = all_discontinued_catalogs
    context._recipient = collection.parent().get() # user account

    if collections[2] and collections[1]: # if result.more and result.cursor
      data = {'action_id': 'cron_notify',
              'action_model': '18',
              'cursor': collections[1]}
      context._callbacks.append(('callback', data))
