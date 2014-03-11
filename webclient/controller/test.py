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
    
      from app import srv
      from app import domain
      from app import opt
    
      models = [srv.auth.Domain, srv.log.Record, srv.setup.Configuration, srv.auth.User, srv.rule.DomainRole, srv.rule.DomainUser,
                srv.setup.Configuration, srv.nav.Widget, srv.event.Action, srv.notify.Template,
                domain.business.Company, domain.business.CompanyContent, domain.marketing.Catalog,
                domain.marketing.CatalogImage, domain.marketing.CatalogPricetag, domain.product.Content,
                domain.product.Instance, domain.product.InventoryAdjustment, domain.product.InventoryLog,
                domain.product.Variant, domain.product.Template, opt.buyer.Address, opt.buyer.Collection, 
                opt.misc.Content, opt.misc.ProductCategory, opt.misc.SupportRequest]
      
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
        
      return {'models' : [f.__name__ for f in models], 'paths' : paths}

class Submitter(handler.Angular):
  
    def respond(self):
        return self.render('tests/submitter.html')
      
      
class Endpoint(handler.Angular):
    
    def respond(self):
        output = io.Engine.run(self.get_input())
        return output
      
    def after(self):
      if not self.data:
         self.data = {}
         
      self.send_json(self.data)
      
class Engine(handler.Angular):

    def respond(self):      
        output = io.Engine.taskqueue_run(self.get_input())
        return output
   
 
handler.register(('/endpoint', Endpoint), 
         ('/reset', Reset),
         ('/engine_run', Engine), 
         ('/submitter', Submitter))