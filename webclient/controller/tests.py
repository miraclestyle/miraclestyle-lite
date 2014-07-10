# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import inspect
import copy

from app import ndb

from webclient import handler
  
class BaseTestHandler(handler.Base):
   
  LOAD_CURRENT_USER = False
  
  def before(self):
    self.response.headers['Content-Type'] = 'text/plain;charset=utf8;'
  
  def out_json(self, s):
    self.out(json.dumps(s, indent=2, cls=handler.JSONEncoderHTML))
  
  def out(self, s, a=0):
    sp = "\n"
    self.response.write(sp*a)
    self.response.write(s)
    self.response.write(sp*a)

class Test1(BaseTestHandler):
 
  def respond(self):
    self.out('Hello World')
    
class TestDeepCopyStruct(ndb.BaseModel):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
  
  
  name = ndb.SuperStringProperty()
    
class TestDeepCopyModel(ndb.BaseModel):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
  
  test1 = ndb.SuperLocalStructuredProperty(TestDeepCopyStruct, repeated=True)
  test2 = ndb.SuperStructuredProperty(TestDeepCopyStruct, repeated=True)
  test3 = ndb.SuperLocalStructuredProperty(TestDeepCopyStruct)
  test4 = ndb.SuperStructuredProperty(TestDeepCopyStruct)
  
  _virtual_fields = dict(test5=ndb.SuperStorageStructuredProperty(TestDeepCopyStruct, storage='remote_multi'),
                         test6=ndb.SuperStorageStructuredProperty(TestDeepCopyStruct, storage='remote_multi_sequenced'),
                         )
    
class TestDeepCopy(BaseTestHandler):
 
  def respond(self):
    the_id = self.request.get('the_id')
    put = self.request.get('put')
    fields = ['test1', 'test2', 'test3', 'test4', 'test5', 'test6']
    if the_id and put:
      entity = TestDeepCopyModel(id=the_id)
      for f in fields:
        if f not in ['test3', 'test4']:
          s = [TestDeepCopyStruct(name='%s' % f)]
        else:
          s = TestDeepCopyStruct(name='%s' % f)
        setattr(entity, f, s)
      entity.put()
    else:
      entity = TestDeepCopyModel.build_key(the_id).get()
      entity.read()
      duplicated = entity.duplicate()
    self.out_json(entity)
      
    if self.request.get('copy'):
      if entity:
        entity_copy = copy.deepcopy(entity)
        self.out_json(entity_copy)
        for f in fields:
          a = getattr(entity_copy, f, None)
          b = getattr(entity, f, None)
          if a == b:
            self.out('EntityCopy.%s == Entity.%s' % (f, f), 1)
    
    
    
    
    
for k,o in globals().items():
  if inspect.isclass(o) and issubclass(o, BaseTestHandler):
    handler.register(('/Tests/%s' % o.__name__, o))