# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient import handler
 
from app import ndb
from app.srv import io

class Reset(handler.Angular):
  
  def respond(self):
    
      from app import srv
      from app import domain
      from app import opt
    
      models = [srv.auth.Domain, srv.log.Record, srv.setup.Configuration, srv.auth.User, srv.rule.DomainRole, srv.rule.DomainUser,
                domain.business.Company, domain.business.CompanyContent, domain.marketing.Catalog,
                domain.marketing.CatalogImage, domain.marketing.CatalogPricetag, domain.product.Content,
                domain.product.Instance, domain.product.InventoryAdjustment, domain.product.InventoryLog,
                domain.product.Variant, domain.product.Template, opt.buyer.Address, opt.buyer.Collection, 
                opt.misc.Content, opt.misc.ProductCategory, opt.misc.SupportRequest]
 
      for mod in models:
          ndb.delete_multi(mod.query().fetch(keys_only=True))
      
      return {'models' : [f.__name__ for f in models]}

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