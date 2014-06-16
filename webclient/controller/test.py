# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import inspect

from google.appengine.ext.ndb import metadata
from google.appengine.api import search

from webclient import handler 

from app import ndb, memcache, util, io
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
                 ('/reset', Reset))