# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import inspect

from google.appengine.ext.ndb import metadata
from google.appengine.api import search, datastore
from google.appengine.ext import blobstore

from backend import orm, http, io, util, mem
from frontend import frontend_settings
from frontend.handler import base
  
class BaseTestHandler(base.Handler):
   
  autoload_current_account = False
  
  def before(self):
    self.response.headers['Content-Type'] = 'text/plain;charset=utf8;'
  
  def out_json(self, s):
    self.out(http.json_output(s))
  
  def out(self, s, a=0, before=True):
    sp = "\n"
    if before:
      self.response.write(sp*a)
    self.response.write(s)
    self.response.write(sp*a)
    
    
class TestA(orm.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_record_engine = False
  _use_rule_engine = False
  _use_search_engine = False
  
  
  name = orm.SuperStringProperty()
  gaa = orm.SuperIntegerProperty()
  
class TestB(orm.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_record_engine = False
  _use_rule_engine = False
  _use_search_engine = False
  
  
  name = orm.SuperStringProperty()
  gaa = orm.SuperIntegerProperty()
  
    
class TestP(orm.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_record_engine = False
  _use_rule_engine = False
  _use_search_engine = False
  
  tests1 = orm.SuperStructuredProperty(TestA, repeated=True)
  tests2 = orm.SuperStructuredProperty(TestB)
    
    
class Test1(BaseTestHandler):
  
  def respond(self):
    if self.request.get('rr'):
      orm.delete_multi(TestP.query().fetch(keys_only=True))
    pp = self.request.get('pp')
    cc = self.request.get('cc')
    if pp and cc:
      outer = TestP(id=pp, tests1=[TestA(name='foobar1', gaa=1)], tests2=TestB(name='foobar2', gaa=2))
      outer.put()
    else:
      outer = TestP.build_key(pp).get()
      outer.read()
      if self.request.get('edit'):
        outer.tests1 = [TestA(name='zoobar1', gaa=2, _sequence=10)]
        outer.put()
    self.out_json([outer.tests2.value._properties, outer])
    
    
class Reset(BaseTestHandler):
  
  def respond(self):
    # @todo THIS DELETES EVERYTHING FROM DATASTORE AND BLOBSTORE, AND CURRENTLY EXISTS ONLY FOR TESTING PURPOSES!
    models = io.Engine.get_schema()
    kinds = ['0', '6', '83', '5', '35', '36', '62', '61', '39', '38', '60', '8', '57', '77', '10', '15', '16', '17', '18', '19', '49', '47']
    namespaces = metadata.get_namespaces()
    indexes = []
    keys_to_delete = []
    if self.request.get('kinds'):
      kinds = self.request.get('kinds').split(',')
    if self.request.get('all_kinds'):
      kinds = []
      for kind_id in models:
        if len(kind_id) < 4 and not kind_id.startswith('__'):
          try:
            kinds.append(str(int(kind_id)))
          except ValueError:
            pass
    util.log('DELETE KINDS %s' % kinds)
    ignore = ['15', '16', '17', '18', '19']
    if self.request.get('ignore'):
      ignore = self.request.get('ignore')
    @orm.tasklet
    def wipe(kind):
      util.log(kind)
      @orm.tasklet
      def generator():
        model = models.get(kind)
        if model and not kind.startswith('__'):
          keys = yield model.query().fetch_async(keys_only=True)
          keys_to_delete.extend(keys)
          indexes.append(search.Index(name=kind))
          for namespace in namespaces:
            util.log(namespace)
            keys = yield model.query(namespace=namespace).fetch_async(keys_only=True)
            keys_to_delete.extend(keys)
            indexes.append(search.Index(name=kind, namespace=namespace))
      yield generator()
    if self.request.get('delete'):
      futures = []
      for kind in kinds:
        if kind not in ignore:
          futures.append(wipe(kind))
      orm.Future.wait_all(futures)
    if self.request.get('and_system'):
      futures = []
      for kind in kinds:
        if kind in ignore:
          futures.append(wipe(kind))
      orm.Future.wait_all(futures)
    if keys_to_delete:
      datastore.Delete([key.to_old_key() for key in keys_to_delete])
    indexes.append(search.Index(name='catalogs'))
    # empty catalog index!
    for index in indexes:
      while True:
        document_ids = [document.doc_id for document in index.get_range(ids_only=True)]
        if not document_ids:
          break
        try:
          index.delete(document_ids)
        except:
          pass
    # delete all blobs
    blobstore.delete(blobstore.BlobInfo.all().fetch(keys_only=True))
    mem.flush_all()
 
 
for k,o in globals().items():
  if inspect.isclass(o) and issubclass(o, BaseTestHandler):
    frontend_settings.ROUTES.append(('/Tests/%s' % o.__name__, o))