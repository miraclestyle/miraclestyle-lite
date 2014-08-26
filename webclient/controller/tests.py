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

from app import orm, settings

from app.models import base

from webclient import handler
  
class BaseTestHandler(handler.Base):
   
  LOAD_CURRENT_USER = False
  
  def before(self):
    self.response.headers['Content-Type'] = 'text/plain;charset=utf8;'
  
  def out_json(self, s):
    self.out(json.dumps(s, indent=2, cls=handler.JSONEncoderHTML))
  
  def out(self, s, a=0, before=True):
    sp = "\n"
    if before:
      self.response.write(sp*a)
    self.response.write(s)
    self.response.write(sp*a)

class Test1(BaseTestHandler):
 
  def respond(self):
    self.out('Hello World')
    
class TestDeepCopyStructFar(orm.BaseModel):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
  _use_cache = False
  
  what = orm.SuperStringProperty()
    
class TestDeepCopyStruct(orm.BaseModel):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
  _use_cache = False
   
  name = orm.SuperStringProperty()
  
  _virtual_fields = dict(_far=orm.SuperStorageStructuredProperty(TestDeepCopyStructFar, storage='remote_multi_sequenced'))
 
class TestDeepCopyStructImage(base.Image):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
  _use_cache = False
  
  _virtual_fields = dict(_other=orm.SuperStorageStructuredProperty(TestDeepCopyStructFar, storage='remote_multi_sequenced'))
 
    
class TestDeepCopyModel(orm.BaseModel):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
  _use_cache = False
  
  test1 = orm.SuperLocalStructuredProperty(TestDeepCopyStruct, repeated=True)
  test2 = orm.SuperStructuredProperty(TestDeepCopyStruct, repeated=True)
  test3 = orm.SuperLocalStructuredProperty(TestDeepCopyStruct)
  test4 = orm.SuperStructuredProperty(TestDeepCopyStruct)
  
  _virtual_fields = dict(_test5=orm.SuperStorageStructuredProperty(TestDeepCopyStruct, storage='remote_multi'),
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
          
          continue
          
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
      #entity._test6.process()  
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
  
class TestKeyParentModel(orm.BaseModel):
  
  _use_record_engine = False
  _use_rule_engine = False
  _use_memcache = False
  _use_cache = False
  
  name = orm.SuperStringProperty()  
    
class TestKeyParent(BaseTestHandler):
  
  def respond(self):
    root = TestKeyParentModel(name='Root', id='root')
    child1 = TestKeyParentModel(name='Child #1', id='child1', parent=root.key)
    child2 = TestKeyParentModel(name='Child #2', id='child2', parent=child1.key)
    entity = TestKeyParentModel(name='Child #3', parent=child2.key, id='child3')
    
    if self.request.get('put'):
      orm.put_multi([root, child1, child2, entity])
    else:
      entity = entity.key.get()
    
    self.out_json(entity)
     
     
class TestPossibleFieldNames(BaseTestHandler):
  
  def respond(self):
    for f in dir(TestKeyParentModel()):
      self.out(f, 1, before=False)
      
      
class TestImageUrl(BaseTestHandler):
  
  def respond(self):
    params = self.request.params
    upload = params.get('upload')
    if 'upload' in params:
      blobinfo = blobstore.parse_blob_info(upload)
      images.Image()
      self.response.write(images.get_serving_url(blobinfo.key()))
    else:
      upload_url = blobstore.create_upload_url(self.request.path, gs_bucket_name=settings.CATALOG_IMAGE_BUCKET)
      self.response.headers['Content-Type'] = 'text/html;charset=utf8;'
      self.response.write("""
      <form method="post" action="%s" enctype="multipart/form-data">
        <input type="file" name="upload" />
        <input type="submit" name="Upload" />
      </form>
      """ % upload_url)
      
tao = (1,2,3,4,5)
      
class TestIterTuple(BaseTestHandler):
  
  def respond(self):
    for i in tao:
      self.response.write(i)
 
for k,o in globals().items():
  if inspect.isclass(o) and issubclass(o, BaseTestHandler):
    handler.register(('/Tests/%s' % o.__name__, o))