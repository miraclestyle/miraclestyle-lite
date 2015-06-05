# -*- coding: utf-8 -*-
'''
Created on Sep 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import datetime
import orm
from collections import OrderedDict

__all__ = ['CollectionCronNotify']


class CollectionCronNotify(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    Collection = context.models['18']
    Catalog = context.models['31']
    collections = Collection.query(Collection.notify == True).fetch_page(1, cursor=context.input.get('cursor'))
    collection = None
    if len(collections) and len(collections[0]):
      collection = collections[0][0]
    else:
      return # nothing found
    context.entity = collection
    context._collection = collection
    context._recipient = collection.key.parent().get() # user account
    if context._recipient.state == 'active': # only active users get mail
      today_minus_7_days = datetime.datetime.now() - datetime.timedelta(days=7)
      all_published_catalogs = OrderedDict()
      all_discontinued_catalogs = OrderedDict()
      sellers = orm.get_multi(collection.sellers)
      futures = []
      for seller in sellers:
        published_catalogs = Catalog.query(Catalog.published_date > today_minus_7_days,
                                           Catalog.state == 'published', ancestor=seller.key).fetch_async(use_memcache=False, use_cache=False) # minimaze impact on memcache
        discontinued_catalogs = Catalog.query(Catalog.updated > today_minus_7_days,
                                              Catalog.state == 'discontinued', ancestor=seller.key).fetch_async(use_memcache=False, use_cache=False)
        all_discontinued_catalogs[seller.key] = {'seller': seller, 'catalogs': discontinued_catalogs}
        all_published_catalogs[seller.key] = {'seller': seller, 'catalogs': published_catalogs}
        futures.append(discontinued_catalogs)
        futures.append(published_catalogs)
      orm.Future.wait_all(futures) # process future queue

      def unload_future_results(structure):
        for key, item in structure.iteritems():
          item['catalogs'] = item['catalogs'].get_result()

      unload_future_results(all_published_catalogs)
      unload_future_results(all_discontinued_catalogs)

      context._all_published_catalogs = all_published_catalogs
      context._all_discontinued_catalogs = all_discontinued_catalogs

    if collections[2] and collections[1]: # if result.more and result.cursor
      data = {'action_id': 'cron_notify',
              'action_model': '18',
              'cursor': collections[1]}
      context._callbacks.append(('callback', data))
