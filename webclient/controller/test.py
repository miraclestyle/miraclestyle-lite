# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import inspect
import time
import random
import json

from google.appengine.ext.ndb import metadata, eventloop
from google.appengine.api import search

from webclient import handler

from app import ndb, memcache, util, io

from app.models.base import GlobalRole

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


class Account(ndb.Model):
  name = ndb.StringProperty()

class Inventory(ndb.Model):
  name = ndb.StringProperty()

class CartItem(ndb.Model):
  account = ndb.KeyProperty()
  inventory = ndb.KeyProperty()
  
class SpecialOffer(ndb.Model):
  inventory = ndb.KeyProperty()
 
 
class TestEntitySingleStorage(ndb.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_field_rules = False
  
  names = ndb.SuperStringProperty(repeated=True)
  
class TestEntityChildrenStorage(ndb.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_field_rules = False
  
  name = ndb.SuperStringProperty()
  
class TestEntityRangeStorage(ndb.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_field_rules = False
  
  name = ndb.SuperStringProperty()
  
class TestEntityLocalStructuredStorage(ndb.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_field_rules = False
  
  name = ndb.SuperStringProperty()
  
class TestEntityStructuredStorage(ndb.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_field_rules = False
  
  name = ndb.SuperStringProperty()
  
class TestEntity(ndb.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_field_rules = False
  
  _virtual_fields = dict(_magic_single_entity = ndb.SuperEntityStorageStructuredProperty(TestEntitySingleStorage, storage='single'),
                         _magic_children_entity = ndb.SuperEntityStorageStructuredProperty(TestEntityChildrenStorage, storage='children_multi'),
                         _magic_range_children_entity = ndb.SuperEntityStorageStructuredProperty(TestEntityRangeStorage, storage='range_children_multi')
                        )
  
  local_structured_repeated = ndb.SuperLocalStructuredProperty(TestEntityLocalStructuredStorage, repeated=True)
  structured_repeated = ndb.SuperStructuredProperty(TestEntityStructuredStorage, repeated=True)
  
  local_structured = ndb.SuperLocalStructuredProperty(TestEntityLocalStructuredStorage)
  structured = ndb.SuperStructuredProperty(TestEntityStructuredStorage)
 
  
class TestEntityManager(handler.Base):
  
  def respond(self):
    new_id = self.request.get('new_id')
    if self.request.get('make'):
      entity = TestEntity(id=new_id)
      entity.put()
    else:
      entity = TestEntity.build_key(new_id).get()
      entity._magic_single_entity.read()
      entity._magic_children_entity.read()
      entity._magic_range_children_entity.read(start_cursor=0, limit=10)
      
      entity.local_structured.read()
      entity.structured.read()
      
      entity.local_structured_repeated.read()
      entity.structured_repeated.read()
     
    if self.request.get('do_put1'):
      storage = entity._magic_single_entity.read()
      storage.names.append('magic_single')
      entity.put()
    
    if self.request.get('do_put2'):
      storages = entity._magic_children_entity.read()
      storages.append(TestEntityChildrenStorage(name='magic_single2')) # is it not imperative that you specify parent= ? @todo
      entity.put()
      
    if self.request.get('do_put3'):
      storages = entity._magic_range_children_entity.read()
      storages.append(TestEntityRangeStorage(name='magic_single3')) # is it not imperative that you specify parent= ? @todo
      entity.put()
      
    if self.request.get('do_put4'):
      entity.local_structured_repeated = [TestEntityLocalStructuredStorage(name='magic_local4')]
      entity.structured_repeated = [TestEntityStructuredStorage(name='magic_local4')]
      entity.put()
      
    if self.request.get('do_put5'):
      entity.local_structured = TestEntityLocalStructuredStorage(name='magic_local5')
      entity.structured = TestEntityStructuredStorage(name='magic_local5')
      entity.put()
      
    if self.request.get('search1'):
      self.response.write(TestEntity.query(TestEntity.structured.name == 'magic_local5').fetch())
    
    o = self.response.write
    self.response.headers['content-type'] = 'text/plain'
    space = "\n"*2
    
    o('entity' + space)
    o(entity)
    o(space)
    
    o('single' + space)
    o(entity._magic_single_entity)
    o(space)
    
    o('children' + space)
    o(entity._magic_children_entity)
    o(space)
    
    o('range' + space)
    o(entity._magic_range_children_entity)
    o(space)
    
    o('local' + space)
    o(entity.local_structured)
    o(space)
    
    o('struct' + space)
    o(entity.structured)
    o(space)
    
    o('localr' + space)
    o(entity.local_structured_repeated)
    o(space)
    
    o('structr' + space)
    o(entity.structured_repeated)
    o(space)


class TestGetsRef(ndb.BaseModel):
  
  _use_field_rules = False
  _use_memcache = False
  _use_cache = False
  
  name = ndb.StringProperty()
  
  
class TestGetsRefEmail(ndb.BaseModel):
  
  _use_field_rules = False
  _use_memcache = False
  _use_cache = False
  
  name = ndb.StringProperty()
  

class TestGets(ndb.BaseModel):
  
  _use_field_rules = False
  _use_memcache = False
  _use_cache = False
  
  referenced = ndb.SuperKeyProperty(kind=TestGetsRef)
  referenced2 = ndb.SuperKeyProperty(kind=TestGetsRefEmail)
    
  _virtual_fields = {
   '_referenced_name' : ndb.SuperReadProperty(kind=TestGetsRef, 
                                          callback=lambda self: self.referenced.get_async(),
                                          format_callback=lambda self, entity: self._get_reference_name(entity)),
                 
   '_referenced2_email' : ndb.SuperReadProperty(kind=TestGetsRefEmail, 
                                          callback=lambda self: self.referenced2.get_async(),
                                          format_callback=lambda self, entity: self._get_reference_email(entity)),
   '_referenced' : ndb.SuperReadProperty(kind=TestGetsRef, 
                                          target_field='referenced'),
   '_referenced2' : ndb.SuperReadProperty(kind=TestGetsRefEmail, 
                                          target_field='referenced2'),           
  }
  
  def _get_reference_email(self, entity):
    if entity:
      return entity.name
    else:
      return None
  
  def _get_reference_name(self, entity):
    if entity:
      return entity.name
    else:
      return None

    
class TestGetAsync(handler.Base):
  
  def respond(self):
    ranger = xrange(0, 10)
    sig = self.request.get('new_id')
    
    self.response.headers['content-type'] = 'text/plain'
    
    def respond(*args):
      for a in args:
        self.response.write(json.dumps(a, cls=handler.JSONEncoderHTML, indent=4))
    
    if self.request.get('delete'):
      ndb.delete_multi(TestGetsRef.query().fetch(keys_only=True) 
                       + TestGetsRefEmail.query().fetch(keys_only=True)
                       + TestGets.query().fetch(keys_only=True))
    
    if self.request.get('make'):
      for i in ranger:
        TestGetsRef(id='A_%s' % i, name='Test_%s' % i).put()
        TestGetsRefEmail(id='B_%s' % i, name='TestB_%s' % i).put()
        
      for i in ranger:
        TestGets(id='%s_%s' % (sig, i), 
                 referenced=ndb.Key(TestGetsRef.get_kind(), 'A_%s' % i),
                 referenced2=ndb.Key(TestGetsRefEmail.get_kind(), 'B_%s' % i)).put()
  
    if self.request.get('query2'):
       results = TestGets.query().fetch()
       for result in results:
         respond(result)
         
    if self.request.get('get'):
      result = TestGets.build_key('%s_%s' % (sig, self.request.get('get'))).get()
      respond(result)
 
 
class TestRuleWriteModelRef(ndb.BaseModel):
  
  _use_field_rules = False
  _use_memcache = False
  _use_cache = False
 
  name = ndb.SuperStringProperty(required=True)
  foobar = ndb.SuperIntegerProperty(default=0)
  

class TestRuleWriteModelRef2(ndb.BaseModel):
  
  _use_field_rules = False
  _use_memcache = False
  _use_cache = False
 
  name = ndb.SuperStringProperty(required=True)
  foobar = ndb.SuperIntegerProperty(default=0)
      
      
class TestRuleWriteModel(ndb.BaseModel):
  
  _kind = 1500
  
  _use_field_rules = True
  _use_memcache = False
  _use_cache = False
  
  _record = False
  
  name = ndb.SuperStringProperty()
  another = ndb.SuperStructuredProperty(TestRuleWriteModelRef, repeated=False)
  other = ndb.SuperStructuredProperty(TestRuleWriteModelRef2, repeated=True)
  
  _global_role = GlobalRole(
    permissions=[
       ndb.FieldPermission('1500', ['name'], True, True, 'True'),
       ndb.FieldPermission('1500', ['another', 'other'], False, True, 'True'),
       ndb.FieldPermission('1500', ['another.name', 'other.foobar'], True, True, 'True'),
      ]
    )

    
class TestRuleWrite(handler.Base):
  
  LOAD_CURRENT_USER = False
  
  def respond(self):
    def out(a):
      self.response.write(json.dumps(a, cls=handler.JSONEncoderHTML))
    ider = self.request.get('id')
    make = self.request.get('make')
    if make:
      a = TestRuleWriteModel(id='tester_%s' % ider, name='Tester one %s' % ider,
                             another=TestRuleWriteModelRef(name='Yes'),
                             other=[TestRuleWriteModelRef2(name='#1'),
                                    TestRuleWriteModelRef2(name='#2'),
                                    TestRuleWriteModelRef2(name='#3')])
      
      a._use_field_rules = False
      a.put()
      out(a)
    else:
      
      a = ndb.Key(TestRuleWriteModel, 'tester_%s' % ider).get()
      a.rule_prepare(TestRuleWriteModel._global_role.permissions)
      a.rule_read()
      if a and self.request.get('do_put'):
        a.name = 'Tester one changed'
        stuff = a.other.read()
        stuff[0].foobar = 77
        stuff[0].name = 'Else 3'
        a.put()
      out(a)
    

class UploadTest(handler.Base):
  
  def respond(self):
    item = self.request.params.get('yes')
    name = self.request.get('name')
 
    if 'yes' in self.request.params:
      blob = item.file.read()
      import cgi
      import cloudstorage as gcs
      from app import settings
      from google.appengine.api import images
      from google.appengine.ext import blobstore
      from google.appengine.api import blobstore as ggg
      from app.models.base import Image
 
      filename = '/%s/%s' % (settings.DOMAIN_LOGO_BUCKET, 'test_%s' % name)
      filename2 = '/gs%s' % filename
 
      with gcs.open(filename, 'w') as f:
        f.write(blob)
        m = images.Image(image_data=blob)
        w = m.width
        h = m.height
      blob_key = blobstore.create_gs_key(filename2)
      blob_key = blobstore.BlobKey(blob_key)
 
      f = Image(id='test_%s' % name, width=w, height=h, image=blob_key, size=len(blob),
                gs_object_name=filename, content_type=item.type, serving_url=images.get_serving_url(blob_key))
      f.put()
      self.response.write(f)
        
      
      
    self.response.write(self.request.params)
    self.response.write('''<form method="post" enctype="multipart/form-data">
    <p><input type="file" name="yes" /></p>
    <input type="hidden" name="name" value="%s" />
    <p><input type="submit" value="Send" />
    </p></form>''' % name)
  
  
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
        raise ndb.Return('foo %s' % i)
 
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
                 ('/test_tasklet', TestTasklet),
                 ('/upload_test', UploadTest),
                 ('/TestEntityManager', TestEntityManager),
                 ('/TestGetAsync', TestGetAsync),
                 ('/TestRuleWrite', TestRuleWrite))