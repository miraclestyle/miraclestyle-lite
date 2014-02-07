# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb, settings
from app.srv import blob, event, rule, log

from google.appengine.ext import blobstore
 

# implements pricetags repeated local structured property
class CatalogImage(blob.Image):
    
    _kind = 36
    # id = sequence, so we can construct keys and use get_multy for fetching image sets, instead of ancestor query
    sequence = ndb.SuperIntegerProperty('7', required=True)
    
    # this model is working on multiple images at once because they are always like grid....
    
    # ancestor DomainCatalog (namespace Domain)
    # composite index: ancestor:yes - sequence
    
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('36', event.Action.build_key('36-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('36', event.Action.build_key('36-3').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('36', event.Action.build_key('36-1').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('36', event.Action.build_key('36-2').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                             ])
 
    _actions = {
       'multiple_upload' : event.Action(id='36-0',
                              arguments={
          
                                 'images' : ndb.SuperLocalStructuredImageProperty(blob.Image, repeated=True),
                                 'catalog' : ndb.SuperKeyProperty(kind='35', required=True),
                                 'upload_url' : ndb.SuperStringProperty(),
                                 
                                 
                              }
                             ),
                
       'multiple_update' : event.Action(id='36-3',
                              arguments={
                                 'keys'  : ndb.SuperKeyProperty(kind='36', repeated=True),
                                 'sequences' : ndb.SuperIntegerProperty(repeated=True),
                              }
                             ),
  
       'delete' : event.Action(id='36-1',
                              arguments={
                                  'keys' : ndb.SuperKeyProperty(kind='36', required=True)
                              }
                             ),
                
       'list' : event.Action(id='36-2',
                              arguments={
                                  'catalog' : ndb.SuperKeyProperty(kind='35', required=True)
                              }
                             ),
                
    }
     
     
    @classmethod
    def multiple_update(cls, context):
      
          @ndb.transactional(xg=True)
          def transaction():
              
              keys = context.input.get('keys')
              sequences = context.input.get('sequences')
              catalog_images = ndb.get_multi(keys)
              
              for i,catalog_image in enumerate(catalog_images):
                  
                  context.rule.entity = catalog_image
                  rule.Engine.run(context)
                  
                  if not rule.executable(context):
                     raise rule.ActionDenied(context)
                  
                  catalog_image.sequence = sequences[i]
                  context.log.entities.append((catalog_image,))
              
              ndb.put_multi(catalog_images)
              
              log.Engine.run(context)
              
              context.output['images'] = catalog_images

          transaction()
 
          return context

      
    @classmethod
    def multiple_upload(cls, context):
 
           upload_url = context.input.get('upload_url')
           images = context.input.get('images')
           catalog_key = context.input.get('catalog')
           
           if upload_url:
              context.output['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.CATALOG_IMAGE_BUCKET)
              return context
           else:
              if not images:
                 return context.required('images')
            
           i = cls.query(ancestor=catalog_key).count() # get last sequence
           prepared_images = []
           
           for image in images:
               i += 1
               data = image.to_dict()
               data['sequence'] = i
               prepared_images.append(cls(**data))
           
           @ndb.transactional(xg=True)
           def transaction():
                
               if prepared_images:
                   ndb.put_multi(prepared_images)
             
                   for saved in prepared_images:
                       if saved:
                          context.log.entities.append((saved,))
                          
                   log.Engine.run(context)
                   
                   # after log runs, mark all blobs as used, because log can also throw error
                   for saved in prepared_images:
                       if saved:
                          blob.Manager.used_blobs(saved.image)
                          
                   context.output['images'] = prepared_images
 
           transaction()
                     
           return context
       
    @classmethod
    def list(cls, context):
 
        catalog_key = context.input.get('catalog')
        catalog = catalog_key.get()
        
        context.rule.entity = catalog
        rule.Engine.run(context)
        
        if not rule.executable(context):
           raise rule.ActionDenied(context)

        context.output['images'] = cls.query(ancestor=catalog_key).fetch()
           
        return context
  
    @classmethod
    def delete(cls, context):
  
        @ndb.transactional(xg=True)
        def transaction():
                        
             entity_keys = context.input.get('keys')
             
             entities = ndb.get_multi(entity_keys)
             context.output['deleted'] = []
             
             for entity in entities:
                 context.rule.entity = entity
                 rule.Engine.run(context)
                 if not rule.executable(context):
                    raise rule.ActionDenied(context)
                  
                 entity.key.delete()
                 context.log.entities.append((entity,)) # cannot log on so many entity groups
                  
                 context.output['deleted'].append(entity)
                 
             log.Engine.run(context) # cannot log on multiple entity groups
             
        transaction()
           
        return context
      

class Catalog(ndb.BaseExpando):
    
    _kind = 35
    
    # root (namespace Domain)
    # https://support.google.com/merchants/answer/188494?hl=en&hlrm=en#other
    # composite index: ???
    company = ndb.SuperKeyProperty('1', kind='44', required=True)
    name = ndb.SuperStringProperty('2', required=True)
    publish_date = ndb.SuperDateTimeProperty('3')# today
    discontinue_date = ndb.SuperDateTimeProperty('4')# +30 days
    updated = ndb.SuperDateTimeProperty('5', auto_now=True)
    created = ndb.SuperDateTimeProperty('6', auto_now_add=True)
    state = ndb.SuperStringProperty('7', required=True)
 
    # Expando
    # cover = blobstore.BlobKeyProperty('8', required=True)# blob ce se implementirati na GCS
    # cost = DecimalProperty('9', required=True)
    # Search improvements
    # product count per product category
    # rank coefficient based on store feedback
     
    _expando_fields = {
       'cover' :  ndb.SuperKeyProperty('8', kind=CatalogImage, required=True),# blob ce se implementirati na GCS
       'cost' : ndb.SuperDecimalProperty('9', required=True)
             
    }
    
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                        rule.ActionPermission('35', event.Action.build_key('35-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
                                        rule.ActionPermission('35', event.Action.build_key('35-1').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
                                        rule.ActionPermission('35', event.Action.build_key('35-7').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
                                        rule.ActionPermission('35', event.Action.build_key('35-2').urlsafe(), False, "context.rule.entity.namespace_entity.state != 'active' and context.rule.entity.state == 'unpublished'"),
                                        rule.ActionPermission('35', event.Action.build_key('35-3').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
                                        rule.ActionPermission('35', event.Action.build_key('35-4').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
                                        rule.ActionPermission('35', event.Action.build_key('35-5').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"), # maybe different rules for duplicate?
                                        rule.ActionPermission('35', event.Action.build_key('35-6').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
                                     ])
    
    _actions = {
       'create' : event.Action(id='35-0',
                              arguments={
                         
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'company' : ndb.SuperKeyProperty(kind='44', required=True),
                        
                              }
                             ),
                
       'update' : event.Action(id='35-7',
                              arguments={
 
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'company' : ndb.SuperKeyProperty(kind='44', required=True),
                                 'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                 
                              }
                             ),
                
                
       'lock' : event.Action(id='35-1',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                          ),
                
       'discontinue' : event.Action(id='35-2',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'publish' : event.Action(id='35-3',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'log_message' : event.Action(id='35-4',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True),
                              }
                             ),
                
       'duplicate' : event.Action(id='35-5',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                              }
                             ),  
                
       'list' : event.Action(id='35-6',
                              arguments={
                                  'domain' : ndb.SuperKeyProperty(kind='6', required=True)
                              }
                          ),    
    }  
    
    @classmethod
    def complete_save(cls, entity, company, context):
      
        if company.state != 'open':
           return context.error('company', 'not_open')
         
        if company.key_namespace != entity.key_namespace:
           raise rule.ActionDenied(context)
           

        context.rule.entity = entity
        rule.Engine.run(context)
        
        if not rule.executable(context):
           raise rule.ActionDenied(context)
        
                   
        entity.name = context.input.get('name')   
        entity.company = context.input.get('company')
        entity.put()
        
        context.status(entity)
        
        context.log.entities.append((entity, ))
        log.Engine.run(context)
 

    @classmethod
    def create(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
  
            company_key = context.input.get('company')
            company = company_key.get() 
 
            entity = cls(state='unpublished', namespace=company.key_namespace)
            
            cls.complete_save(entity, company, context)
       
        transaction()
        
        return context
       
  
    @classmethod
    def update(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
          
            company_key = context.input.get('company')
            company = company_key.get() 
 
            entity_key = context.input.get('key')
            entity = entity_key.get()
             
            cls.complete_save(entity, company, context)
       
        transaction()
        
        return context
       
    @classmethod
    def lock(cls, context):
       
        # @todo
        # discontinue consequences
 
        @ndb.transactional(xg=True)
        def transaction():
          
        
            entity_key = context.input.get('key')
            entity = entity_key.get()
           
            cover = CatalogImage.query(ancestor=entity.key_parent).order(-CatalogImage.sequence).get(keys_only=True)
    
            context.rule.entity = entity
            rule.Engine.run(context)
            
            if not rule.executable(context):
               raise rule.ActionDenied(context)
            
            if cover:
               entity.cover = cover
               
            entity.state = 'locked'
            entity.put()
            
            context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
            log.Engine.run(context)
             
            context.status(entity)

        transaction()
        
        return context
      
    @classmethod
    def discontinue(cls, context):
      
        # @todo
        # discontinue consequences
 
        @ndb.transactional(xg=True)
        def transaction():
          
            entity_key = context.input.get('key')
            entity = entity_key.get()
       
            context.rule.entity = entity
            rule.Engine.run(context)
            
            if not rule.executable(context):
               raise rule.ActionDenied(context)
            
            entity.state = 'discontinued'
            entity.put()
            
            context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
            log.Engine.run(context)
             
            context.status(entity)

        transaction()
        
        return context
      
    @classmethod
    def publish(cls, context):
        
        # @todo
        # publish date 
        # checking if user has enough credts
        # and some reactions to other things when the catalog gets published
 
        @ndb.transactional(xg=True)
        def transaction():
          
            entity_key = context.input.get('key')
            entity = entity_key.get()
       
            context.rule.entity = entity
            rule.Engine.run(context)
            
            if not rule.executable(context):
               raise rule.ActionDenied(context)
            
            entity.state = 'published'
            entity.put()
            
            context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
            log.Engine.run(context)
             
            context.status(entity)

        transaction()
           
        return context
      
    @classmethod
    def log_message(cls, context):
  
         @ndb.transactional(xg=True)
         def transaction():
           
             entity_key = context.input.get('key')
             entity = entity_key.get()
        
             context.rule.entity = entity
             rule.Engine.run(context)
             
             if not rule.executable(context):
                raise rule.ActionDenied(context)
              
             entity.put() # ref project-documentation.py #L-244
  
             context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
             log.Engine.run(context)
              
             context.status(entity)
             
         transaction()
         
         return context
      
    @classmethod
    def duplicate(cls, context):
        # how we are going to duplicate the catalog? copy-paste the blobs?
        pass
    
    @classmethod
    def list(cls, context):
 
        domain_key = context.input.get('domain')
        domain = domain_key.get()
      
        context.rule.entity = domain
        rule.Engine.run(context)
        
        if not rule.executable(context):
           raise rule.ActionDenied(context)

        context.output['catalogs'] = cls.query(namespace=domain.key_namespace).fetch()
           
        return context
# this is LocalStructuredProperty and is repeated per catalog image.
class CatalogPricetag(ndb.BaseModel):
    
    _kind = 34
    
    # ancestor DomainCatalog (namespace Domain)
    product_template = ndb.SuperKeyProperty('1', kind='38', required=True, indexed=False)
    container_image = ndb.SuperKeyProperty('2', kind=CatalogImage, required=True, indexed=False)# blob ce se implementirati na GCS
    source_width = ndb.SuperFloatProperty('3', required=True, indexed=False)
    source_height = ndb.SuperFloatProperty('4', required=True, indexed=False)
    source_position_top = ndb.SuperFloatProperty('5', required=True, indexed=False)
    source_position_left = ndb.SuperFloatProperty('6', required=True, indexed=False)
    value = ndb.SuperStringProperty('7', required=True, indexed=False)# $ 19.99 - ovo se handla unutar transakcije kada se radi update na unit_price od ProductTemplate ili ProductInstance

    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('34', event.Action.build_key('34-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('34', event.Action.build_key('34-3').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('34', event.Action.build_key('34-1').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('34', event.Action.build_key('34-2').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
 
                                             ])

    _actions = {
       'create' : event.Action(id='34-0',
                              arguments={
                        
                                 'product_template' : ndb.SuperKeyProperty(kind='38', required=True),
                                 'container_image' : ndb.SuperKeyProperty(kind=CatalogImage, required=True),# blob ce se implementirati na GCS
                                 'source_width' : ndb.SuperFloatProperty(required=True),
                                 'source_width' : ndb.SuperFloatProperty(required=True),
                                 'source_position_top' : ndb.SuperFloatProperty(required=True),
                                 'source_position_left' : ndb.SuperFloatProperty(required=True),
 
                                 'catalog' : ndb.SuperKeyProperty(kind='35', required=True),
               
                              }
                             ),
                
       'update' : event.Action(id='34-3',
                              arguments={
                                 'product_template' : ndb.SuperKeyProperty(kind='38', required=True),
                                 'container_image' : ndb.SuperKeyProperty(kind=CatalogImage, required=True),# blob ce se implementirati na GCS
                                 'source_width' : ndb.SuperFloatProperty(required=True),
                                 'source_width' : ndb.SuperFloatProperty(required=True),
                                 'source_position_top' : ndb.SuperFloatProperty(required=True),
                                 'source_position_left' : ndb.SuperFloatProperty(required=True),
                                 'key' : ndb.SuperKeyProperty(kind='34', required=True)
                              }
                             ),
                
       'delete' : event.Action(id='34-1',
                              arguments={
                                   'key' : ndb.SuperKeyProperty(kind='34', required=True)
                              }
                             ),
                
       'list' : event.Action(id='34-2',
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
              raise rule.ActionDenied(context)
            
           set_args = {}
           for field_name in cls.get_fields():
              if field_name in context.input:
                 set_args[field_name] = context.input.get(field_name)
           
           entity.populate(**set_args)      
           entity.put()
            
           context.log.entities.append((entity, ))
           log.Engine.run(context)
              
           context.status(entity)      

    
    @classmethod
    def create(cls, context):
       # @todo value prop formatting
 
       @ndb.transactional(xg=True)
       def transaction():
 
           catalog_key = context.input.get('catalog_key')
           entity = cls(parent=catalog_key)
 
           cls.complete_save(entity, context)
          
       transaction()
       
       return context
    
    @classmethod
    def update(cls, context):
       # @todo value prop formatting
 
       @ndb.transactional(xg=True)
       def transaction():
  
           entity_key = context.input.get('key')
           entity = entity_key.get()
  
           cls.complete_save(entity, context)
           
       transaction()
       
       return context
      
    @classmethod
    def delete(cls, context):
 
          @ndb.transactional(xg=True)
          def transaction():
                          
               entity_key = context.input.get('key')
               entity = entity_key.get()
               context.rule.entity = entity
               rule.Engine.run(context)
               if not rule.executable(context):
                  raise rule.ActionDenied(context)
                
               entity.key.delete()
               context.log.entities.append((entity,))
               log.Engine.run(context)
 
               context.status(entity)
               
          transaction()
             
          return context
    
    @classmethod
    def list(cls, context):
 
        catalog_key = context.input.get('catalog')
        catalog = catalog_key.get()
        
        context.rule.entity = catalog
        rule.Engine.run(context)
        
        if not rule.executable(context):
           raise rule.ActionDenied(context)

        context.output['price_tags'] = cls.query(ancestor=catalog_key).fetch()
             
        return context

    