# -*- coding: utf-8 -*-
'''
Created on Feb 5, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json

from webclient import handler
from webclient.util import JSONEncoderHTML
  
class ModelInfo(handler.Base):
  
  def respond(self):
    
    self.response.headers['Content-Type'] = 'text/javascript'
    
    script = u''
    
    
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
    
    
    script += "ModelInfo = {}; \n"
    
    actions = {}
    fields = {}
 
    for model in models:
      if hasattr(model, '_actions'):
        actions[model.get_kind()] = model.get_actions()
        
      if hasattr(model, 'get_fields'):
        fields[model.get_kind()] = model.get_fields()
        
    script += "ModelInfo.actions = %s; \n" % json.dumps(actions, cls=JSONEncoderHTML)
    script += "ModelInfo.properties = %s; \n" % json.dumps(fields, cls=JSONEncoderHTML)
    
    self.response.write(script)
      
      
handler.register(('/model_info.js', ModelInfo))



