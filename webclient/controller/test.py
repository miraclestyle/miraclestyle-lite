# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import inspect

from webclient import handler 

from app import ndb, memcache, util
from app.srv import io

class Reset(handler.Angular):
  
  def respond(self):
      
      from app.opt import buyer
      from app.srv import auth, log, setup, rule, nav, event, notify, marketing, product, location, uom
 
      models = [auth.Domain, log.Record, setup.Configuration, auth.User, rule.DomainRole, rule.DomainUser,
                setup.Configuration, nav.Widget, event.Action, notify.Template,
                marketing.Catalog, marketing.CatalogImage, marketing.CatalogPricetag,
                product.Template, product.Images, product.Instance, product.Variants, product.Contents,
                buyer.Addresses, buyer.Collection
                ]
      keys_to_delete = []
      if self.request.get('delete'):
        for mod in models:
          keys_to_delete.extend(mod.query().fetch(keys_only=True))
            
      if self.request.get('system'):
        for mod in [location.Country, location.CountrySubdivision, uom.Unit, uom.Measurement]:
          keys_to_delete.extend(mod.query().fetch(keys_only=True))
            
      if keys_to_delete:
         ndb.delete_multi(keys_to_delete)
             
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