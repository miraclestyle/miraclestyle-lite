# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from google.appengine.ext.ndb import metadata
from google.appengine.api import search, datastore

from app import io, orm, util, mem

from webclient import handler

class Reset(handler.Angular):
  
  def respond(self):
    models = io.Engine.get_schema()
    kinds = ['0', '6', '83', '5', '35', '36', '62', '61', '39', '38', '60', '8', '57', '77', '10', '15', '16', '17', '18', '19', '49', '47']
    namespaces = metadata.get_namespaces()
    indexes = []
    keys_to_delete = []
    if self.request.get('kinds'):
      kinds = self.request.get('kinds').split(',')
    
    util.log('DELETE KINDS %s' % kinds)
    
    ignore = ['15', '16', '17', '18', '19']
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
    mem.flush_all()

class Install(handler.Angular):
  
  def respond(self):
    out = []
    for model, action in [('15', 'update'), ('17', 'update'), ('19', 'update_unit'), ('19', 'update_currency')]:
      out.append(io.Engine.run({'action_model' : model, 'action_id' : action}))
    return out
    
  def after(self):
    if not self.data:
       self.data = {}
       
    self.send_json(self.data)
      
class Endpoint(handler.Angular):
 
  def respond(self):
    output = io.Engine.run(self.get_input())
    return output
    
  def after(self):
    if not self.data:
       self.data = {}
       
    self.send_json(self.data)
 
 
handler.register(('/endpoint', Endpoint),
                 ('/install', Install),
                 ('/reset', Reset),)