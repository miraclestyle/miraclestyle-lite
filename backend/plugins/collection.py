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
    age = self.cfg.get('age', 7)
    Collection = context.models['18']
    Catalog = context.models['31']
    result = Collection.query(Collection.notify == True).fetch_page(1, start_cursor=context.input.get('cursor'))
    collection = None
    if len(result) and len(result[0]):
      collection = result[0][0]
    else:
      return  # nothing found
    context.entity = collection
    context._collection = collection
    context._recipient = collection.key.parent().get()  # user account
    if context._recipient.state == 'active':  # only active users get mail
      age = datetime.datetime.now() - datetime.timedelta(days=age)
      published_catalogs = collections.OrderedDict()
      discontinued_catalogs = collections.OrderedDict()
      futures = []
      collection._sellers.read()
      for seller in collection._sellers.value:
        published_catalogs[seller.key] = {'seller': seller}
        published_catalogs[seller.key]['catalogs'] = Catalog.query(Catalog.published_date > age,
                                                                   Catalog.state == 'published', ancestor=seller.key).fetch_async(use_memcache=False, use_cache=False)
        discontinued_catalogs[seller.key] = {'seller': seller}
        discontinued_catalogs[seller.key]['catalogs'] = Catalog.query(Catalog.updated > age,
                                                                      Catalog.state == 'discontinued', ancestor=seller.key).fetch_async(use_memcache=False, use_cache=False)
        futures.append(discontinued_catalogs[seller.key]['catalogs'])
        futures.append(published_catalogs[seller.key]['catalogs'])
      orm.Future.wait_all(futures)  # process future queue

      def get_results(catalogs):
        for key, value in catalogs.iteritems():
          value['catalogs'] = value['catalogs'].get_result()

      get_results(published_catalogs)
      get_results(discontinued_catalogs)

      context._published_catalogs = published_catalogs
      context._discontinued_catalogs = discontinued_catalogs

    if result[2] and result[1]:  # if result.more and result.cursor
      data = {'action_id': 'cron_notify',
              'action_model': '18',
              'cursor': result[1]}
      context._callbacks.append(('callback', data))
