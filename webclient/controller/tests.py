# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import inspect
import copy

from google.appengine.ext import blobstore
from google.appengine.api import images

from app import ndb, settings

from app.models import base

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
    
class TestDeepCopyStructFar(ndb.BaseModel):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
  
  what = ndb.SuperStringProperty()
    
class TestDeepCopyStruct(ndb.BaseModel):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
   
  name = ndb.SuperStringProperty()
  
  _virtual_fields = dict(_far=ndb.SuperStorageStructuredProperty(TestDeepCopyStructFar, storage='remote_multi_sequenced'))
 
class TestDeepCopyStructImage(base.Image):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
  
  _virtual_fields = dict(_other=ndb.SuperStorageStructuredProperty(TestDeepCopyStructFar, storage='remote_multi_sequenced'))
 
    
class TestDeepCopyModel(ndb.BaseModel):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
  
  test1 = ndb.SuperLocalStructuredProperty(TestDeepCopyStruct, repeated=True)
  test2 = ndb.SuperStructuredProperty(TestDeepCopyStruct, repeated=True)
  test3 = ndb.SuperLocalStructuredProperty(TestDeepCopyStruct)
  test4 = ndb.SuperStructuredProperty(TestDeepCopyStruct)
  
  _virtual_fields = dict(_test5=ndb.SuperStorageStructuredProperty(TestDeepCopyStruct, storage='remote_multi'),
                         _test6=base.SuperImageStorageStructuredProperty(TestDeepCopyStructImage, storage='remote_multi'),)
    
class TestDeepCopy(BaseTestHandler):
 
  def respond(self):
    the_id = self.request.get('the_id')
    put = self.request.get('put')
    fields = ['test1', 'test2', 'test3', 'test4', '_test5', '_test6']
    if the_id and put:
      entity = TestDeepCopyModel(id=the_id)
      for f in fields:
        if f in ['test1', 'test2']:
          s = [TestDeepCopyStruct(name='%s' % f)]
        elif f in ['test3', 'test4']:
          s = TestDeepCopyStruct(name='%s' % f)
        elif f == '_test5':
          s = [TestDeepCopyStruct(name='%s' % f, _far=[
                                                      TestDeepCopyStructFar(what='Yes'), 
                                                      TestDeepCopyStructFar(what='No')
                                                     ])]
          
        elif f == '_test6':
          
          the_file = self.request.params.get('file')
          a = blobstore.parse_blob_info(the_file)
          b = blobstore.parse_file_info(the_file)
          serving_url = images.get_serving_url(a.key())
          
          s = [TestDeepCopyStructImage(image=a.key(),
          content_type=a.content_type,
          size=a.size,
          gs_object_name=b.gs_object_name,
          serving_url=serving_url,
          _other=[
              TestDeepCopyStructFar(what='AYes'), 
              TestDeepCopyStructFar(what='ANo')
           ])]
        setattr(entity, f, s)
      entity._test6.process()  
      entity.put()
    else:
      entity = TestDeepCopyModel.build_key(the_id).get()
      entity.read()
      
    
    self.out_json(entity)
    
    if self.request.get('duplicate'):
      duplicate = entity.duplicate()
      duplicate.put()
      self.out_json(duplicate)
      
    if self.request.get('copy'):
      if entity:
        entity_copy = copy.deepcopy(entity)
        self.out_json(entity_copy)
        for f in fields:
          a = getattr(entity_copy, f, None)
          b = getattr(entity, f, None)
          if a == b:
            self.out('EntityCopy.%s == Entity.%s' % (f, f), 1)
            
            
class TestCreateURL(BaseTestHandler):
  
  def respond(self):
    self.out(blobstore.create_upload_url(self.request.get('path'), gs_bucket_name=settings.DOMAIN_LOGO_BUCKET))
     
    
for k,o in globals().items():
  if inspect.isclass(o) and issubclass(o, BaseTestHandler):
    handler.register(('/Tests/%s' % o.__name__, o))