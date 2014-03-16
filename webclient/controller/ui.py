# -*- coding: utf-8 -*-
'''
Created on Feb 5, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json

from webclient import handler
from webclient.util import JSONEncoderHTML

class Index(handler.Angular):
  
  def respond(self):
    return {}
  
class ModelInfo(handler.Base):
  
  def respond(self):
    
    # beside the content type include the cache headers in the future
    self.response.headers['Content-Type'] = 'text/javascript'
    
    script = u''
    
    
    from app import srv
    from app import domain
    from app import opt
    
    # here we would combine all classes that are models with their _actions and get_fields() methods
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
        actions[model.get_kind()] = model._actions
        
      if hasattr(model, 'get_fields'):
        fields[model.get_kind()] = model.get_fields()
        
    script += "ModelInfo.actions = %s; \n" % json.dumps(actions, indent=2, cls=JSONEncoderHTML)
    script += "ModelInfo.fields = %s; \n" % json.dumps(fields, indent=2, cls=JSONEncoderHTML)
    
    self.response.write(script)
      
      
handler.register(('/', Index),
                 ('/model_info.js', ModelInfo))
