# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import inspect
import time

from google.appengine.ext.ndb import metadata, eventloop
from google.appengine.api import search

from webclient import handler 

from app import ndb, memcache, util, io

@ndb.tasklet
def results_search_callback(entities):
  @ndb.tasklet
  def process_fields(entity):
    entity._primary_contact = yield entity.primary_contact.get_async()
    raise ndb.Return()
  futures = []
  for entity in entities:
    futures.append(process_fields(entity))
  ndb.Future.wait_all(futures)
  raise ndb.Return()

@ndb.tasklet
def process_search():
  entities = yield ndb.Model.query().fetc_page_async() # arguments
  yield results_search_callback(entities) # possible other arguments
  raise ndb.Return(entities)

#entities = process_search().get_result()

class Account(ndb.Model):
  name = ndb.StringProperty()

class Inventory(ndb.Model):
  name = ndb.StringProperty()

class CartItem(ndb.Model):
  account = ndb.KeyProperty()
  inventory = ndb.KeyProperty()
  
class SpecialOffer(ndb.Model):
  inventory = ndb.KeyProperty()

class TestTasklet(handler.Angular):
  
  def respond(self):
    """
    import Queue
    import threading
    import urllib2
    
    # called by each thread
    def get_url(q, url):
        time.sleep(0.5)
        print 'doing %s' % url
        q.put({'done' : url})
    
    theurls = range(1, 10)
    
    q = Queue.Queue()
    
    for u in theurls:
        t = threading.Thread(target=get_url, args = (q,u))
        t.daemon = True
        t.start()
    
    s = q.get()
    print s
    
    return
    """
    
    @ndb.tasklet
    def resulter():
      results = []
      @ndb.tasklet
      def generator(i):
        time.sleep(0.5)
        print 'doing %s' % i
 
      for i in range(1, 10):
        result = yield generator(i)
        results.append(result)
      raise ndb.Return(results)
    
    @ndb.tasklet
    def mapper():
      f = resulter()
      results = yield f
      print results
    
    f = mapper()
    eventloop.run()
    f.done()
    
    print f
 
   
    return
    
    acc = ndb.Key('Account', 'edis')
    if self.request.get('write'):
      Account(id='edis', name='Edis').put()
      
      for x in range(0, 15):
        inv = Inventory(id=str(x), name='Inventory #%s' % x)
        inv.put()
        CartItem(id=str(x), inventory=inv.key, account=acc).put()
      
      for x in range(16, 31):
        inv = Inventory(id=str(x), name='Inventory #%s' % x)
        inv.put()
        SpecialOffer(id=str(x), inventory=inv.key).put()
         
    
    @ndb.tasklet
    def get_cart_async(acct):
      cart = yield CartItem.query(CartItem.account == acct).fetch_async()
      print 'get_cart_async', cart
      invs = yield ndb.get_multi_async([item.inventory for item in cart])
      print 'get_cart_async', invs
      raise ndb.Return(cart)
    
    @ndb.tasklet
    def get_offers_async(acct):
      offers = yield SpecialOffer.query().fetch_async(10)
      print 'get_offers_async', offers
      invs = yield ndb.get_multi_async([offer.inventory for offer in offers])
      print 'get_offers_async', invs
      raise ndb.Return(offers)
    
    @ndb.tasklet
    def get_cart_plus_offers(acct):
      cart, offers = yield get_cart_async(acct), get_offers_async(acct)
      raise ndb.Return((cart, offers))
    
    print get_cart_plus_offers(acc).get_result()

class Reset(handler.Angular):
  
  def respond(self):
    
      models = io.Engine.get_schema()
      
      kinds = ['0', '6', '83', '5', '35', '36', '62', '61', '39', '38', '60', '8', '57', '77', '10']
      namespaces = metadata.get_namespaces()
      keys_to_delete = []
      
      ignore = ['15', '16', '17', '18', '19']
      @ndb.tasklet
      def wipe(kind):
          util.logger(kind)
          @ndb.tasklet
          def generator():
            model = models.get(kind)
            if model and not kind.startswith('__'):
              keys = yield model.query().fetch_async(keys_only=True)
              keys_to_delete.extend(keys)
              for namespace in namespaces:
                  keys = yield model.query(namespace=namespace).fetch_async(keys_only=True)
                  keys_to_delete.extend(keys)
                  
          yield generator()
              
      if self.request.get('delete'):
        futures = []
        for kind in kinds:
          if kind not in ignore:
            futures.append(wipe(kind))
        ndb.Future.wait_all(futures)
 
      if self.request.get('and_system'):
        futures = []
        for kind in kinds:
          if kind in ignore:
            futures.append(wipe(kind))
        ndb.Future.wait_all(futures)
     
      if keys_to_delete:
         ndb.delete_multi(keys_to_delete)
      # empty catalog index!
      index = search.Index(name='catalogs')
      while True:
        document_ids = [document.doc_id for document in index.get_range(ids_only=True)]
        if not document_ids:
          break
        index.delete(document_ids)
      memcache.flush_all()
 
      
class Endpoint(handler.Angular):
    
    def respond(self):
        output = io.Engine.run(self.get_input())
        return output
      
    def after(self):
      if not self.data:
         self.data = {}
         
      self.send_json(self.data)
 
 
handler.register(('/endpoint', Endpoint), 
                 ('/reset', Reset),
                 ('/test_tasklet', TestTasklet))