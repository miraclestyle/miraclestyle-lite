# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import datetime
import cloudstorage

from app import ndb, settings
from app.srv import blob, io, rule, log

from google.appengine.ext import blobstore
from google.appengine.api import images
 

# done!
class CatalogImage(blob.Image):
    
    _kind = 36
    
    # this model is working on multiple images at once because they are always like grid....
    
    # ancestor DomainCatalog (namespace Domain)
    # composite index: ancestor:yes - sequence
    
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('36', io.Action.build_key('36-0').urlsafe(), False, "not context.rule.entity.parent_entity.state == 'unpublished'"),
                                            rule.ActionPermission('36', io.Action.build_key('36-1').urlsafe(), False, "not context.rule.entity.parent_entity.state == 'unpublished'"),
                                             ])
 
    _actions = {
       'multiple_manage' : io.Action(id='36-0',
                              arguments={
                                         
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'images' : ndb.SuperImageKeyProperty(repeated=True),
                                 'catalog' : ndb.SuperKeyProperty(kind='35'),
                               
                                 # update
                                 'keys'  : ndb.SuperKeyProperty(kind='36', repeated=True),
                                 'sequences' : ndb.SuperIntegerProperty(repeated=True),
                                 
                                 # upload url
                                 
                                 'upload_url' : ndb.SuperStringProperty(),
                                 
                                 
                              }
                             ),
 
                
       'delete' : io.Action(id='36-1',
                              arguments={
                                  'keys' : ndb.SuperKeyProperty(kind='36', required=True, repeated=True)
                              }
                             ),
                
       'list' : io.Action(id='36-2',
                              arguments={
                                  'catalog' : ndb.SuperKeyProperty(kind='35', required=True)
                              }
                             ),
                
    }
     
      
    @classmethod
    def multiple_manage(cls, args):

        action = cls._actions.get('multiple_manage')
        context = action.process(args)
        
        if not context.has_error():
           
           upload_url = context.args.get('upload_url')
           
           if upload_url:
              context.response['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.CATALOG_IMAGE_BUCKET)
              return context
            
           image_keys = context.args.get('images')
           keys = context.args.get('keys')
           catalog_key = context.args.get('catalog')
           
           i = cls.query(ancestor=catalog_key).count() # get last sequence
           
           get_images = blobstore.BlobInfo.get(image_keys)
           prepared_images = []
           
           for image in get_images:
               i += 1
              
               f = cloudstorage.open(image.gs_object_name[3:])
               
               blob = f.read()
      
               image_loaded = images.Image(image_data=blob)
           
               f.close()
                
               prepared_images.append({
                                 'parent' : catalog_key,
                                 'image' : image.key(),
                                 'content_type' : image.content_type,
                                 'size' : image.size,
                                 'width' : image_loaded.width,
                                 'height' : image_loaded.height,
                                 'sequence' : i, 
                                })
           
           @ndb.transactional(xg=True)
           def transaction():
                
               if prepared_images:
                   new_catalog_images = []
                   for image in prepared_images:
                       i += 1
                       new_catalog_images.append(cls(**image))
                   saveds = ndb.put_multi(new_catalog_images)
                   for saved in saveds:
                       if saved:
                          blob.Manager.used_blobs(saved.image)
                          context.log.entities.append((saved,))
               elif keys:
                    # can only do sequences
                    sequences = context.args.get('sequences')
                    catalog_images = ndb.get_multi(keys)
                    for i,catalog_image in enumerate(catalog_images):
                        
                        context.rule.entity = catalog_image
                        rule.Engine.run(context)
                        
                        if not rule.executable(context):
                          return context.not_authorized()
                        
                        catalog_image.sequence = sequences[i]
                        context.log.entities.append((catalog_image,))
                    
                    ndb.put_multi(catalog_images)
                    
               log.Engine.run(context)
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
                     
        return context
      
    @classmethod
    def list(cls, args):
      
        action = cls._actions.get('list')
        context = action.process(args)
        
        if not context.has_error():
           catalog_key = context.args.get('catalog')
           catalog = catalog_key.get()
           if not catalog.state == 'unpublished':
              return context.error('catalog', 'not_unpublished')
           context.response['catalog_images'] = cls.query(ancestor=catalog_key).fetch()
              
        return context
  
    @classmethod
    def delete(cls, args):
        
        action = cls._actions.get('delete')
        context = action.process(args)

        if not context.has_error():
          
          @ndb.transactional(xg=True)
          def transaction():
                          
               entity_keys = context.args.get('keys')
               
               entities = ndb.get_multi(entity_keys)
               context.response['deleted'] = []
               
               for entity in entities:
                   context.rule.entity = entity
                   rule.Engine.run(context)
                   if not rule.executable(context):
                      return context.not_authorized()
                    
                   entity.key.delete()
                   context.log.entities.append((entity,)) # cannot log on so many entity groups
                    
                   context.response['deleted'].append(entity)
                   
               log.Engine.run(context) # cannot log on multiple entity groups
               
          try:
             transaction()
          except Exception as e:
             context.transaction_error(e)
             
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
                                        rule.ActionPermission('35', io.Action.build_key('35-0').urlsafe(), False, "not context.rule.entity.state == 'unpublished'"),
                                        rule.ActionPermission('35', io.Action.build_key('35-1').urlsafe(), False, "not context.rule.entity.state == 'unpublished'"),
                                        rule.ActionPermission('35', io.Action.build_key('35-2').urlsafe(), False, "context.rule.entity.state == 'unpublished'"),
                                        rule.ActionPermission('35', io.Action.build_key('35-3').urlsafe(), False, "not context.rule.entity.state == 'unpublished'"),
                                        rule.ActionPermission('35', io.Action.build_key('35-4').urlsafe(), False, "not context.rule.entity.state == 'unpublished'"),
                                        rule.ActionPermission('35', io.Action.build_key('35-5').urlsafe(), False, "not context.rule.entity.state == 'unpublished'"),
                                        rule.ActionPermission('35', io.Action.build_key('35-6').urlsafe(), False, "not context.rule.entity.state == 'unpublished'"),
                                     ])
    
    _actions = {
       'manage' : io.Action(id='35-0',
                              arguments={
                                         
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'domain' : ndb.SuperKeyProperty(kind='6'),
                               
                                 # update
                                 'key'  : ndb.SuperKeyProperty(kind='35'),
                                 
                              }
                             ),
                
       'lock' : io.Action(id='35-1',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                          ),
                
       'discontinue' : io.Action(id='35-2',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'publish' : io.Action(id='35-3',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'log_message' : io.Action(id='35-4',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True),
                              }
                             ),
                
       'duplicate' : io.Action(id='35-5',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                              }
                             ),  
                
       'list' : io.Action(id='35-6',
                              arguments={
                                  'domain' : ndb.SuperKeyProperty(kind='6', required=True)
                              }
                          ),    
    }  
 
  
    @classmethod
    def manage(cls, args):
      
        action = cls._actions.get('manage')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
               create = context.args.get('create')
               
               upload_url = context.args.get('upload_url')
               if upload_url:
                  context.response['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.COMPANY_LOGO_BUCKET)
                  return context
               
               set_args = {}
               
               if create:
                  domain_key = context.args.get('domain')
                  domain = domain_key.get()
                  if  not domain_key:
                      return context.required('domain')
                  
                  entity = cls(state='unpublished', namespace=domain.key_namespace)
               else:
                  entity_key = context.args.get('key')
                  entity = entity_key.get()
            
               # only populate items that are available from expando and other
    
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
               
                          
               entity.name = context.args.get('name')   
               entity.put()
               
               context.status(entity)
               
               context.log.entities.append((entity, ))
               log.Engine.run(context)
          
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
       
    @classmethod
    def lock(cls, args):
      
        action = cls._actions.get('lock')
        context = action.process(args)
        
        if not context.has_error():
          
                       
           entity_key = context.args.get('key')
           entity = entity_key.get()
          
           cover = CatalogImage.query(ancestor=entity.key_parent).order(-CatalogImage.sequence).get(keys_only=True)
  
           @ndb.transactional(xg=True)
           def transaction():
 
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
               
               if cover:
                  entity.cover = cover
                  
               entity.state = 'locked'
               entity.put()
               
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
 
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
      
    @classmethod
    def discontinue(cls, args):
      
        action = cls._actions.get('discontinue')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('key')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
               
               entity.state = 'discontinued'
               entity.put()
               
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
 
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
      
    @classmethod
    def publish(cls, args):
      
        action = cls._actions.get('published')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('key')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
               
               entity.state = 'published'
               entity.put()
               
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
 
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
      
    @classmethod
    def log_message(cls, args):
      
        action = cls._actions.get('log_message')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('key')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
                
               entity.put() # ref project-documentation.py #L-244
  
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
               
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
      
    @classmethod
    def duplicate(cls, args):
        pass
    
    @classmethod
    def list(cls, args):
      
        action = cls._actions.get('list')
        context = action.process(args)
        
        if not context.has_error():
          
           domain_key = context.args.get('domain')
           domain = domain_key.get()
           
           context.response['catalogs'] = cls.query(namespace=domain.key_namespace).fetch()
  
        return context

# done!
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

    _actions = {
       'manage' : io.Action(id='36-0',
                              arguments={
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 
                                 'product_template' : ndb.SuperKeyProperty(kind='38', required=True, indexed=False),
                                 'container_image' : ndb.SuperKeyProperty(kind=CatalogImage, required=True, indexed=False),# blob ce se implementirati na GCS
                                 'source_width' : ndb.SuperFloatProperty(required=True, indexed=False),
                                 'source_width' : ndb.SuperFloatProperty(required=True, indexed=False),
                                 'source_position_top' : ndb.SuperFloatProperty(required=True, indexed=False),
                                 'source_position_left' : ndb.SuperFloatProperty(required=True, indexed=False),
 
                                 'company' : ndb.SuperKeyProperty(kind='44'),
                                 'key' : ndb.SuperKeyProperty(kind='36')
                              }
                             ),
                
       'delete' : io.Action(id='36-1',
                              arguments={
                                   'key' : ndb.SuperKeyProperty(kind='36', required=True)
                              }
                             ),
                
       'list' : io.Action(id='36-2',
                              arguments={
                                  'company' : ndb.SuperKeyProperty(kind='44'),
                              }
                             ),
    } 
    
    @classmethod
    def manage(cls, args):
        
        action = cls._actions.get('manage')
        context = action.process(args)
  
        if not context.has_error():
          
            @ndb.transactional(xg=True)
            def transaction():
              
                create = context.args.get('create')
   
                if create:
                   entity = cls(parent=context.args.get('company'))
                else:
                   entity_key = context.args.get('key')
                   entity = entity_key.get()
       
                context.rule.entity = entity
                rule.Engine.run(context)
                
                if not rule.executable(context):
                   return context.not_authorized()
                 
                set_args = {}
                for field_name in cls.get_fields():
                   if field_name in context.args:
                      set_args[field_name] = context.args.get(field_name)
                
                entity.populate(**set_args)      
                entity.put()
                 
                context.log.entities.append((entity, ))
                log.Engine.run(context)
                   
                context.status(entity)
               
            try:
                transaction()
            except Exception as e:
                context.transaction_error(e)
            
        return context
      
    @classmethod
    def delete(cls, args):
        
        action = cls._actions.get('delete')
        context = action.process(args)

        if not context.has_error():
          
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

    