# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import itertools
import hashlib
 
from app import ndb, settings
from app.srv import io, uom, blob, rule, log

from google.appengine.ext import blobstore

# done!
class Content(ndb.BaseModel):
    
    _kind = 43
    
    # ancestor DomainCatalog (future - root) (namespace Domain)
    # composite index: ancestor:yes - title
    title = ndb.SuperStringProperty('1', required=True)
    body = ndb.SuperTextProperty('2', required=True)
    
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('43', io.Action.build_key('43-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('43', io.Action.build_key('43-3').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('43', io.Action.build_key('43-1').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('43', io.Action.build_key('43-2').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                             ])

    _actions = {
       'create' : io.Action(id='43-0',
                              arguments={
                      
                                 'title' : ndb.SuperStringProperty(required=True),
                                 'body' : ndb.SuperTextProperty(required=True),
                                 'catalog' : ndb.SuperKeyProperty(kind='35', required=True),
                              }
                             ),
                
       'update' : io.Action(id='43-3',
                              arguments={
                                 'title' : ndb.SuperStringProperty(required=True),
                                 'body' : ndb.SuperTextProperty(required=True),
                                 'key' : ndb.SuperKeyProperty(kind='43', required=True)
                              }
                             ),
                
       'delete' : io.Action(id='43-1',
                              arguments={
                                   'key' : ndb.SuperKeyProperty(kind='43', required=True)
                              }
                             ),
                
       'list' : io.Action(id='43-2',
                              arguments={
                                  'catalog' : ndb.SuperKeyProperty(kind='35'),
                              }
                             ),
    } 
    
    @classmethod
    def complete_save(cls, entity, context):
      
         context.rule.entity = entity
         rule.Engine.run(context)
         
         if not rule.executable(context):
            return context.not_authorized()
          
         entity.title = context.args.get('title')
         entity.body = context.args.get('body')
         entity.put()
          
         context.log.entities.append((entity, ))
         log.Engine.run(context)
            
         context.status(entity)        
    
    @classmethod
    def create(cls, context):
 
         @ndb.transactional(xg=True)
         def transaction():
 
             catalog_key = context.args.get('catalog')
             entity = cls(parent=catalog_key)
 
             cls.complete_save(entity, context)
            
         try:
             transaction()
         except Exception as e:
             context.transaction_error(e)
         
         return context

    
    @classmethod
    def update(cls, context):
 
         @ndb.transactional(xg=True)
         def transaction():
             
             entity_key = context.args.get('key')
             entity = entity_key.get()
             
             cls.complete_save(entity, context)
             
         try:
             transaction()
         except Exception as e:
             context.transaction_error(e)
         
         return context
 
    @classmethod
    def delete(cls, context):
 
       @ndb.transactional(xg=True)
       def transaction():
                       
            entity_key = context.args.get('key')
            entity = entity_key.get()
            context.rule.entity = entity
            rule.Engine.run(context)
            if not rule.executable(context):
               return context.not_authorized()
             
            entity.key.delete()
            context.log.entities.append((entity,))
            log.Engine.run(context)

            context.status(entity)
            
       try:
          transaction()
       except Exception as e:
          context.transaction_error(e)
          
       return context
      
    @classmethod
    def list(cls, context):
       
        catalog_key = context.args.get('catalog')
        catalog = catalog_key.get()
        
        context.rule.entity = catalog
        rule.Engine.run(context)
        
        if not rule.executable(context):
           return context.not_authorized()

        context.response['contents'] = cls.query(ancestor=catalog_key).fetch()
           
        return context
     
  

# done!
class Variant(ndb.BaseModel):
    
    _kind = 42
    
    # ancestor DomainCatalog (future - root) (namespace Domain)
    # http://v6apps.openerp.com/addon/1809
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    description = ndb.SuperTextProperty('2')# soft limit 64kb
    options = ndb.SuperStringProperty('3', repeated=True, indexed=False)# soft limit 1000x
    allow_custom_value = ndb.SuperBooleanProperty('4', default=False, indexed=False)# ovu vrednost buyer upisuje u definisano polje a ona se dalje prepisuje u order line description prilikom Add to Cart
 
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('42', io.Action.build_key('42-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('42', io.Action.build_key('42-3').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('42', io.Action.build_key('42-1').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('42', io.Action.build_key('42-2').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                             ]) 

    _actions = {
       'create' : io.Action(id='42-0',
                              arguments={
  
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'description' : ndb.SuperTextProperty(required=True),
                                 'options' : ndb.SuperStringProperty(repeated=True),
                                 'allow_custom_value' : ndb.SuperBooleanProperty(default=False),
                                 'catalog' : ndb.SuperKeyProperty(kind='35', required=True),
              
                              }
                             ),

       'update' : io.Action(id='42-3',
                              arguments={
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'description' : ndb.SuperTextProperty(required=True),
                                 'options' : ndb.SuperStringProperty(repeated=True),
                                 'allow_custom_value' : ndb.SuperBooleanProperty(default=False),
                                 'key' : ndb.SuperKeyProperty(kind='42', required=True)
                              }
                             ),
                
       'delete' : io.Action(id='42-1',
                              arguments={
                                   'key' : ndb.SuperKeyProperty(kind='42', required=True)
                              }
                             ),
                
       'list' : io.Action(id='42-2',
                              arguments={
                                  'catalog' : ndb.SuperKeyProperty(kind='35', required=True),
                              }
                             ),
    } 
    
    @classmethod
    def complete_save(cls, entity, context):
      
         context.rule.entity = entity
         rule.Engine.run(context)
         
         if not rule.executable(context):
            return context.not_authorized()
          
         entity.name = context.args.get('name')
         entity.description = context.args.get('description')
         entity.options = context.args.get('options')
         entity.allow_custom_value = context.args.get('allow_custom_value')
         entity.put()
          
         context.log.entities.append((entity, ))
         log.Engine.run(context)
            
         context.status(entity)
    
    @classmethod
    def create(cls, context):
 
       @ndb.transactional(xg=True)
       def transaction():
         
           catalog_key = context.args.get('catalog')
           entity = cls(parent=catalog_key)
              
           cls.complete_save(entity, context)
          
       try:
           transaction()
       except Exception as e:
           context.transaction_error(e)
       
       return context
    
    @classmethod
    def update(cls, context):
 
       @ndb.transactional(xg=True)
       def transaction():
           
           entity_key = context.args.get('key')
           entity = entity_key.get()
           
           cls.complete_save(entity, context)
   
          
       try:
           transaction()
       except Exception as e:
           context.transaction_error(e)
       
       return context
 
    @classmethod
    def delete(cls, context):
 
         @ndb.transactional(xg=True)
         def transaction():
                         
              entity_key = context.args.get('key')
              entity = entity_key.get()
              context.rule.entity = entity
              rule.Engine.run(context)
              if not rule.executable(context):
                 return context.not_authorized()
               
              entity.key.delete()
              context.log.entities.append((entity,))
              log.Engine.run(context)
  
              context.status(entity)
              
         try:
            transaction()
         except Exception as e:
            context.transaction_error(e)
            
         return context
      
    @classmethod
    def list(cls, context):
 
        catalog_key = context.args.get('catalog')
        catalog = catalog_key.get()
        
        context.rule.entity = catalog
        rule.Engine.run(context)
        
        if not rule.executable(context):
           return context.not_authorized()

        context.response['variants'] = cls.query(ancestor=catalog_key).fetch()
           
        return context

class Template(ndb.BaseExpando):
    
    _kind = 38
    
    # ancestor DomainCatalog (future - root / namespace Domain)
    # composite index: ancestor:yes - name
    product_category = ndb.SuperKeyProperty('1', kind='17', required=True, indexed=False)
    name = ndb.SuperStringProperty('2', required=True)
    description = ndb.SuperTextProperty('3', required=True)# soft limit 64kb
    product_uom = ndb.SuperKeyProperty('4', kind=uom.Unit, required=True, indexed=False)
    unit_price = ndb.SuperDecimalProperty('5', required=True)
    availability = ndb.SuperIntegerProperty('6', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    
    # availability: - ovo cemo pojasniti
    # 'in stock'
    # 'available for order'
    # 'out of stock'
    # 'preorder'
    # 'auto manage inventory - available for order' (poduct is 'available for order' when inventory balance is <= 0)
    # 'auto manage inventory - out of stock' (poduct is 'out of stock' when inventory balance is <= 0)
    # https://support.google.com/merchants/answer/188494?hl=en&ref_topic=2473824
    
    _default_indexed = False
    
    _expando_fields = {
      'variants' : ndb.SuperKeyProperty('7', kind='42', repeated=True),# soft limit 100x
      'contents' : ndb.SuperKeyProperty('8', kind=Content, repeated=True),# soft limit 100x
      'images' : ndb.SuperLocalStructuredProperty(blob.Image, '9', repeated=True),# soft limit 100x
      'weight' : ndb.SuperPickleProperty('10'),# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
      'volume' : ndb.SuperPickleProperty('11'),# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
      'low_stock_quantity' : ndb.SuperDecimalProperty('12', default='0.00'),# notify store manager when qty drops below X quantity
      'product_instance_count' : ndb.SuperIntegerProperty('13') # cuvanje ovog podatka moze biti od koristi zbog prakticnog limita broja instanci na sistemu
 
    }
  
    
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('38', io.Action.build_key('38-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('38', io.Action.build_key('38-4').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('38', io.Action.build_key('38-1').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('38', io.Action.build_key('38-2').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('38', io.Action.build_key('38-3').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                             ]) 

    _actions = {
       'create' : io.Action(id='38-0',
                              arguments={
                             
                                 'product_category' : ndb.SuperKeyProperty(kind='17', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'description' : ndb.SuperTextProperty(required=True),# soft limit 64kb
                                 'product_uom' : ndb.SuperKeyProperty(kind=uom.Unit, required=True),
                                 'unit_price' : ndb.SuperDecimalProperty(required=True),
                                 'availability' : ndb.SuperIntegerProperty(required=True),#
                                 
                                 'variants' : ndb.SuperKeyProperty(kind='42', repeated=True),# soft limit 100x
                                 'contents' : ndb.SuperKeyProperty(kind=Content, repeated=True),# soft limit 100x
                                 'images' : ndb.SuperLocalStructuredProperty(blob.Image, repeated=True),# soft limit 100x
                                 'weight' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
                                 'volume' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
                                 'low_stock_quantity' : ndb.SuperDecimalProperty(default='0.00'),# notify store manager when qty drops below X quantity
                  
                                 'catalog' : ndb.SuperKeyProperty(kind='35', required=True),
                                 
                                 'upload_url' : ndb.SuperStringProperty(),
              
                              }
                             ),
                
       'update' : io.Action(id='38-4',
                              arguments={
              
                                 'product_category' : ndb.SuperKeyProperty(kind='17', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'description' : ndb.SuperTextProperty(required=True),# soft limit 64kb
                                 'product_uom' : ndb.SuperKeyProperty(kind=uom.Unit, required=True),
                                 'unit_price' : ndb.SuperDecimalProperty(required=True),
                                 'availability' : ndb.SuperIntegerProperty(required=True),#
                                 
                                 'variants' : ndb.SuperKeyProperty(kind='42', repeated=True),# soft limit 100x
                                 'contents' : ndb.SuperKeyProperty(kind=Content, repeated=True),# soft limit 100x
                                 'images' : ndb.SuperLocalStructuredProperty(blob.Image, repeated=True),# soft limit 100x
                                 'weight' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
                                 'volume' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
                                 'low_stock_quantity' : ndb.SuperDecimalProperty(default='0.00'),# notify store manager when qty drops below X quantity
                   
                                 'upload_url' : ndb.SuperStringProperty(),
                                  
                                 'key' : ndb.SuperKeyProperty(kind='38', required=True)
                              }
                             ),
                
       'delete' : io.Action(id='38-1',
                              arguments={
                                   'key' : ndb.SuperKeyProperty(kind='38', required=True)
                              }
                             ),
                
       'list' : io.Action(id='38-2',
                              arguments={
                                  'catalog' : ndb.SuperKeyProperty(kind='35'),
                              }
                             ),
                
       'generate_product_instances' : io.Action(id='38-3',
                              arguments={
                                  'template' : ndb.SuperKeyProperty(kind='38'),
                              }
                             ),
    } 
    
    @classmethod
    def complete_save(cls, entity, context):
      
         upload_url = context.args.get('upload_url')
    
         if upload_url:
           context.response['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.PRODUCT_TEMPLATE_BUCKET)
           return context
  
         context.rule.entity = entity
         rule.Engine.run(context)
         
         if not rule.executable(context):
            return context.not_authorized()
          
         set_args = {}
         
         for field_name, field in cls.get_fields():
             if field_name in context.args:
                set_args[field_name] = context.args.get(field_name)
                
         variants = []
         contents = []
         
         for variant in context.args.get('variants', []):
             if variant.key_namespace == entity.key_namespace:
                variants.append(variant)
          
         for content in context.args.get('contents', []):
             if content.key_namespace == entity.key_namespace:
                contents.append(content)
                
         if len(variants):       
            set_args['variants'] = variants
            
         if len(contents):
            set_args['contents'] = contents
 
         entity.populate(**set_args)    
       
         entity.put()
  
         context.log.entities.append((entity, ))
         log.Engine.run(context)
         
         # after log runs, mark all blobs as used, because log can also throw error
                         
         for saved in entity.images:
             if saved:
                blob.Manager.used_blobs(saved.image)
                 
         context.status(entity)

    
    @classmethod
    def create(cls, context):
      
       # @todo images delete
       # weight, volume formatting
       # stock? availability 
        
       # writable fields with rule engine
  
       @ndb.transactional(xg=True)
       def transaction():
         
           catalog_key = context.args.get('catalog')
           entity = cls(parent=catalog_key)
         
           cls.complete_save(entity, context)
          
       try:
           transaction()
       except Exception as e:
           context.transaction_error(e)
        
       return context
    
    @classmethod
    def update(cls, context):
      
       # @todo images delete
       # weight, volume formatting
       # stock? availability 
        
       # writable fields with rule engine
  
       @ndb.transactional(xg=True)
       def transaction():
         
           entity_key = context.args.get('key')
           entity = entity_key.get()
         
           cls.complete_save(entity, context)
          
       try:
           transaction()
       except Exception as e:
           context.transaction_error(e)
        
       return context
 
    @classmethod
    def delete(cls, context):
       
       delete_images = []
       
       @ndb.transactional(xg=True)
       def transaction():
                       
            entity_key = context.args.get('key')
            entity = entity_key.get()
            context.rule.entity = entity
            rule.Engine.run(context)
            if not rule.executable(context):
               return context.not_authorized()
             
            entity.key.delete()
            context.log.entities.append((entity,))
            log.Engine.run(context)
            
            delete_images = entity.images

            context.status(entity)
            
       try:
          transaction()
          if delete_images:
             blobstore.delete(delete_images)
       except Exception as e:
          context.transaction_error(e)
           
       return context
      
    @classmethod
    def list(cls, context):
 
        catalog_key = context.args.get('catalog')
        catalog = catalog_key.get()
        
        context.rule.entity = catalog
        rule.Engine.run(context)
        
        if not rule.executable(context):
           return context.not_authorized()

        context.response['templates'] = cls.query(ancestor=catalog_key).fetch()
           
        return context
    
    @classmethod
    def generate_product_instances(cls, context):
 
       @ndb.transactional(xg=True)
       def transaction():
                       
            product_template_key = context.args.get('template')
            product_template = product_template_key.get()
            
            context.rule.entity = product_template
            rule.Engine.run(context)
            
            if not rule.executable(context):
               return context.not_authorized()

            # cant go delete multi cuz we also need to delete images
            # ndb.delete_multi(Instance.query(ancestor=product_template_key).fetch(keys_only=True))
            for p in Instance.query(ancestor=product_template_key).fetch():
                 p.delete_product_instance()
             
            ndb.delete_multi(InventoryLog.query(ancestor=product_template_key).fetch(keys_only=True))
             
            ndb.delete_multi(InventoryAdjustment.query(ancestor=product_template_key).fetch(keys_only=True))
              
            variants = ndb.get_multi(product_template.variants)
            packer = list()
             
            for v in variants:
                 packer.append(v.options)
                 
            if not packer:
                return context.error('generator', 'empty_generator')
                 
            create_variations = itertools.product(*packer)
             
            context.response['instances'] = list()
            
            if len(create_variations) >= 1000:
               product_template.product_instance_count = 1000
               product_template.put()
               code = '%s_%s' % (product_template_key.urlsafe(), 1)
               inst = Instance(parent=product_template_key, id=code, code=code)
               inst.put()
            
            else:   
              i = 1
              for c in create_variations:
                   code = '%s_%s' % (product_template_key.urlsafe(), i)
                   compiled = Instance.md5_variation_combination(c)
                   inst = Instance(parent=product_template_key, id=compiled, code=code)
                   inst.put()
                   context.log.entities.append((inst, ))
                   i += 1
                   
                   context.response['instances'].append(inst)
                   
              product_template.product_instance_count = i
              product_template.put()
                 
            log.Engine.run(context)
              
       try:
           transaction()
       except Exception as e:
           context.transaction_error(e)
     
       return context
     

# done!
class Instance(ndb.BaseExpando):
    
    _kind = 39
    
    # ancestor DomainProductTemplate
    #variant_signature se gradi na osnovu ProductVariant entiteta vezanih za ProductTemplate-a (od aktuelne ProductInstance) preko ProductTemplateVariant 
    #key name ce se graditi tako sto se uradi MD5 na variant_signature
    #query ce se graditi tako sto se prvo izgradi variant_signature vrednost na osnovu odabira od strane krajnjeg korisnika a potom se ta vrednost hesira u MD5 i koristi kao key identifier
    #mana ove metode je ta sto se uvek mora izgraditi kompletan variant_signature, tj moraju se sve varijacije odabrati (svaka varianta mora biti mandatory_variant_type)
    #default vrednost code ce se graditi na osnovu sledecih informacija: ancestorkey-n, gde je n incremental integer koji se dodeljuje instanci prilikom njenog kreiranja
    #ukoliko user ne odabere multivariant opciju onda se za ProductTemplate generise samo jedna ProductInstance i njen key se gradi automatski.
    # composite index: ancestor:yes - code
    code = ndb.SuperStringProperty('1', required=True)
    
    _default_indexed = False
 
    _expando_fields = {
      'availability' : ndb.SuperIntegerProperty('2', required=True), # overide availability vrednosti sa product_template-a, inventory se uvek prati na nivou instanci, state je stavljen na template kako bi se olaksala kontrola state-ova. 
      'description'  : ndb.SuperTextProperty('3', required=True), # soft limit 64kb
      'unit_price' : ndb.SuperDecimalProperty('4', required=True),
      'contents' : ndb.SuperKeyProperty('5', kind=Content, repeated=True), # soft limit 100x
      'images' : ndb.SuperLocalStructuredProperty(blob.Image, '6', repeated=True), # soft limit 100x
      'low_stock_quantity' : ndb.SuperDecimalProperty('7', default='0.00'), # notify store manager when qty drops below X quantity
      'weight' : ndb.SuperStringProperty('8'), # prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
      'volume' : ndb.SuperStringProperty('9'), # prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
      'variant_signature' : ndb.SuperTextProperty('10', required=True),# soft limit 64kb - ova vrednost kao i vrednosti koje kupac manuelno upise kao opcije variante se prepisuju u order line description prilikom Add to Cart
    }
    
    
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('39', io.Action.build_key('39-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('39', io.Action.build_key('39-1').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            ]) 

    _actions = {
       'update' : io.Action(id='39-0',
                              arguments={
                     
                                 'code' : ndb.SuperStringProperty(required=True),
                                 'availability' : ndb.SuperIntegerProperty(),#
                                 'description' : ndb.SuperTextProperty(),# soft limit 64kb
                                 'unit_price' : ndb.SuperDecimalProperty(),
                                 
                                 'contents' : ndb.SuperKeyProperty(kind=Content, repeated=True),# soft limit 100x
                                 'variants' : ndb.SuperKeyProperty(kind='42', repeated=True),# soft limit 100x
                                 'images' : ndb.SuperLocalStructuredProperty(blob.Image, repeated=True),# soft limit 100x
                                 'weight' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
                                 'volume' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
                                 # not sure if this should be writable ? 'variant_signature' : ndb.SuperStringProperty(),# notify store manager when qty drops below X quantity
                   
                                 'upload_url' : ndb.SuperStringProperty(),
                                  
                                 'key' : ndb.SuperKeyProperty(kind='39', required=True)
                              }
                             ),
       'list' : io.Action(id='39-1',
                              arguments={
                                  'catalog' : ndb.SuperKeyProperty(kind='35', required=True),
                              }
                             ),
                
  
    } 
  
    def delete_product_instance(self):
        
        self.key.delete()
        blobstore.delete([img.image for img in self.images])
            
 
    @classmethod
    def md5_variation_combination(cls, codes):
        codes = list(codes)
        return hashlib.md5(u'-'.join(codes)).hexdigest()
    
    @classmethod
    def update(cls, context):
      
       # @todo images delete per selected image, possible custom argument
       # weight, volume formatting
       # stock, availability
       # writable fields
  
       @ndb.transactional(xg=True)
       def transaction():
           
           entity_key = context.args.get('key')
           entity = entity_key.get()
         
           upload_url = context.args.get('upload_url')
      
           if upload_url:
             context.response['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.PRODUCT_TEMPLATE_BUCKET)
             return context

           context.rule.entity = entity
           rule.Engine.run(context)
           
           if not rule.executable(context):
              return context.not_authorized()
            
           set_args = {}
           
           for field_name, field in cls.get_fields():
               if field_name in context.args:
                  set_args[field_name] = context.args.get(field_name)
                  
           variants = []
           contents = []
           
           for variant in context.args.get('variants', []):
               if variant.key_namespace == entity.key_namespace:
                  variants.append(variant)
            
           for content in context.args.get('contents', []):
               if content.key_namespace == entity.key_namespace:
                  contents.append(content)
                  
           if len(variants):       
              set_args['variants'] = variants
              
           if len(contents):
              set_args['contents'] = contents
 
           entity.populate(**set_args)    
 
           entity.put()

           context.log.entities.append((entity, ))
           log.Engine.run(context)
           
           # after log runs, mark all blobs as used, because log can also throw error
                           
           for saved in entity.images:
               if saved:
                  blob.Manager.used_blobs(saved.image)
                   
           context.status(entity)
          
       try:
           transaction()
       except Exception as e:
           context.transaction_error(e)
       
       return context
   
      
    @classmethod
    def list(cls, context):
 
        catalog_key = context.args.get('catalog')
        catalog = catalog_key.get()
        
        context.rule.entity = catalog
        rule.Engine.run(context)
        
        if not rule.executable(context):
           return context.not_authorized()
  
        context.response['instances'] = cls.query(ancestor=catalog_key).fetch()
        
        return context

# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class InventoryLog(ndb.BaseModel):
    
    _kind = 40
    
    # ancestor DomainProductInstance (namespace Domain)
    # key za DomainProductInventoryLog ce se graditi na sledeci nacin:
    # key: parent=domain_product_instance.key, id=str(reference_key) ili mozda neki drugi destiled id iz key-a
    # idempotency je moguc ako se pre inserta proverava da li postoji record sa id-jem reference_key
    # not logged
    # composite index: ancestor:yes - logged:desc
    logged = ndb.SuperDateTimeProperty('1', auto_now_add=True)
    quantity = ndb.SuperDecimalProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    balance = ndb.SuperDecimalProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query

# done!
class InventoryAdjustment(ndb.BaseModel):
    
    _kind = 41
    
    # ancestor DomainProductInstance (namespace Domain)
    # not logged ?
    adjusted = ndb.SuperDateTimeProperty('1', auto_now_add=True, indexed=False)
    agent = ndb.SuperKeyProperty('2', kind='0', required=True, indexed=False)
    quantity = ndb.SuperDecimalProperty('3', required=True, indexed=False)
    comment = ndb.SuperStringProperty('4', indexed=False)

    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('41', io.Action.build_key('41-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                       ])

    _actions = {
       'create' : io.Action(id='41-0',
                              arguments={
                         
                                 'comment' : ndb.SuperStringProperty(required=True),
                                 'quantity' : ndb.SuperDecimalProperty(required=True),
                    
                                 'product_instance' : ndb.SuperKeyProperty(kind='39')
                              }
                             ),
 
    } 
    
    @classmethod
    def create(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
           
            product_instance_key = context.args.get('product_instance')
            entity = cls(parent=product_instance_key)
   
            context.rule.entity = entity
            rule.Engine.run(context)
            
            if not rule.executable(context):
               return context.not_authorized()
             
            entity.comment = context.args.get('comment')
            entity.quantity = context.args.get('quantity')
            entity.put()
            
            product_inventory_log = InventoryLog.query(parent=product_instance_key).order(-InventoryLog.logged).get()
            new_product_inventory_log = InventoryLog(parent=product_instance_key, id=entity.key.urlsafe(), quantity=entity.quantity, balance=product_inventory_log.balance + entity.quantity)
            new_product_inventory_log.put()
             
            context.log.entities.append((entity, ))
            log.Engine.run(context)
               
            context.status(entity)
            context.response['product_inventory_log'] = product_inventory_log
           
        try:
            transaction()
        except Exception as e:
            context.transaction_error(e)
        
        return context

