# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import inspect

from webclient import handler 

from app import ndb, memcache
from app.srv import io

class Reset(handler.Angular):
  
  def respond(self):
    
      from app.srv import auth, log, setup, rule, nav, event, notify, marketing
 
      models = [auth.Domain, log.Record, setup.Configuration, auth.User, rule.DomainRole, rule.DomainUser,
                setup.Configuration, nav.Widget, event.Action, notify.Template,
                marketing.Catalog, marketing.CatalogImage, marketing.CatalogPricetag,
                ]
      
      if self.request.get('delete'):
        for mod in models:
            ndb.delete_multi(mod.query().fetch(keys_only=True))
             
        memcache.flush_all()
        
      paths = {}
      
      for mod in models:
          path = inspect.getfile(mod)
          pathsplit = path.split('/app/')
          if pathsplit and pathsplit[1]:
             modelpath = '%s.%s' % (pathsplit[1].split('.')[0], mod.__name__)
             modelpath = modelpath.replace('/', '.')
             paths[mod.get_kind()] = modelpath
        
      return {'models' : dict([(model.get_kind(), model.__name__) for model in models]), 'paths' : paths}
  
      
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