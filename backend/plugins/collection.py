# -*- coding: utf-8 -*-
'''
Created on Sep 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import datetime
import collections

import orm

__all__ = ['CollectionCronNotify']


class CollectionCronNotify(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    Collection = context.models['18']
    Catalog = context.models['31']
    result = Collection.query(Collection.notify == True).fetch_page(1, cursor=context.input.get('cursor'))
    collection = None
    if len(result) and len(result[0]):
      collection = result[0][0]
    else:
      return # nothing found
    context.entity = collection
    context._collection = collection
    context._recipient = collection.key.parent().get() # user account
    if context._recipient.state == 'active': # only active users get mail
      today_minus_7_days = datetime.datetime.now() - datetime.timedelta(days=7)
      all_published_catalogs = collections.OrderedDict()
      all_discontinued_catalogs = collections.OrderedDict()
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

    if result[2] and result[1]: # if result.more and result.cursor
      data = {'action_id': 'cron_notify',
              'action_model': '18',
              'cursor': result[1]}
      context._callbacks.append(('callback', data))
