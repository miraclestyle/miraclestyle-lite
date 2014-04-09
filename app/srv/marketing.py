# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import copy

from app import ndb, settings
from app.srv import blob, event, rule, log, callback, cruds

from google.appengine.ext import blobstore

# this is LocalStructuredProperty and is repeated per catalog image.
# properties to remain in this class are: 
# product_template, position_top (former source_position_top), position_left (former source_position_left), value
class CatalogPricetag(ndb.BaseModel):
    
    _kind = 34
    
    product_template = ndb.SuperKeyProperty('1', kind='38', required=True, indexed=False)
    position_top = ndb.SuperFloatProperty('5', required=True, indexed=False)
    position_left = ndb.SuperFloatProperty('6', required=True, indexed=False)
    value = ndb.SuperStringProperty('7', required=True, indexed=False)# $ 19.99 - ovo se handla unutar transakcije kada se radi update na unit_price od ProductTemplate ili ProductInstance
    
    
# implements pricetags repeated local structured property
class CatalogImage(blob.Image):
    
    _kind = 36
    # id = sequence, so we can construct keys and use get_multy for fetching image sets, instead of ancestor query
    # this will require delete/put on every update to image sequence, so it has to be evaluated further
    sequence = ndb.SuperIntegerProperty('7', required=True)
    pricetags = ndb.SuperLocalStructuredProperty(CatalogPricetag, '8', repeated=True)
    
    # this model is working on multiple images at once because they are always like grid....
  
  
class Catalog(ndb.BaseExpando):
    
    _kind = 35
    
    # root (namespace Domain)
    # https://support.google.com/merchants/answer/188494?hl=en&hlrm=en#other
    # composite index: ???
    name = ndb.SuperStringProperty('1', required=True)
    publish_date = ndb.SuperDateTimeProperty('2')# today
    discontinue_date = ndb.SuperDateTimeProperty('3')# +30 days
    updated = ndb.SuperDateTimeProperty('4', auto_now=True)
    created = ndb.SuperDateTimeProperty('5', auto_now_add=True)
    state = ndb.SuperStringProperty('6', required=True)
 
    # Expando
    # cover = blobstore.BlobKeyProperty('8', required=True)# blob ce se implementirati na GCS
    # cost = DecimalProperty('9', required=True)
    # Search improvements
    # product count per product category
    # rank coefficient based on store feedback
     
    _expando_fields = {
       'cover' :  ndb.SuperKeyProperty('7', kind='36', required=True),# blob ce se implementirati na GCS
       'cost' : ndb.SuperDecimalProperty('8', required=True)
    }
    
    _virtual_fields = {
       '_images' : ndb.SuperLocalStructuredProperty(CatalogImage, repeated=True),
       '_records': log.SuperLocalStructuredRecordProperty('35', repeated=True),
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
                                 'domain' : ndb.SuperKeyProperty(kind='6', required=True),        
                                 'name' : ndb.SuperStringProperty(required=True),
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
                
       'search' : event.Action(id='35-6',
                              arguments={
                                  'domain' : ndb.SuperKeyProperty(kind='6', required=True)
                              }
                          ),  
       'update' : event.Action(id='35-7',
                              arguments={
                                 'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 '_images' : ndb.SuperLocalStructuredProperty(CatalogImage, repeated=True),
                              }
                             ),
       'upload_images' : event.Action(id='35-8',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='35', required=True),
                                 'images' : ndb.SuperLocalStructuredImageProperty(CatalogImage, repeated=True),
                                 'upload_url' : ndb.SuperStringProperty(),
                              }
                             ),
                
       'read' : event.Action(id='35-9',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                                  'next' : ndb.SuperIntegerProperty(default=0)
                              }
        ),  
       'read_records' : event.Action(id='35-10',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='35', required=True),
                              }
        ),
       'prepare' : event.Action(id='35-11',
                              arguments={
                                  'domain' : ndb.SuperKeyProperty(kind='6', required=True)
                              }
        ),  
    }  
  
    @classmethod
    def create(cls, context):
      
      domain_key = context.input.get('domain')
      entity = cls(namespace=domain_key.urlsafe())
      
      context.rule.entity = entity
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      
      @ndb.transactional(xg=True)
      def transaction():
        # population values here...
        rule.write(entity, {'name' : context.input.get('name')})
        entity.put()
        context.log.entities.append((entity, ))
        log.Engine.run(context)
        rule.read(entity)
        context.output['entity'] = entity
        context.callback.payloads.append(('notify',
                                            {'action_key': 'initiate',
                                             'action_model': '61',
                                             'entity_key': entity.key.urlsafe()}))
        callback.Engine.run(context)
      
      transaction()
 
  
    @classmethod
    def update(cls, context):
      
       entity_key = context.input.get('key')
       name = context.input.get('name')
       _images = context.input.get('_images')
       entity = entity_key.get()
       
       context.rule.entity = entity
       rule.Engine.run(context)
         
       if not rule.executable(context):
         raise rule.ActionDenied(context)      
 
       @ndb.transactional(xg=True)
       def transaction():
          
          current_images = CatalogImage.query(ancestor=entity.key).fetch()
          
          copy_current_images = copy.copy(current_images)
          
          entity._images = current_images
          
          values = {
           'name' : name,
           '_images' : _images
          }
          rule.write(entity, values)
          entity.put()
          
          delete_catalog_keys = []
          delete_catalog_image_keys = []
          possible_keys = [catalog_image.key for catalog_image in entity._images]
          
          for copy_current_image in copy_current_images:
             if copy_current_image.key not in possible_keys:
                delete_catalog_keys.append(copy_current_image.key)
                delete_catalog_image_keys.append(copy_current_image.image)
          
          if entity._images:
             ndb.put_multi(entity._images)
          else:
             delete_catalog_images = entity._images
             
             for delete_catalog_image in delete_catalog_images:
               delete_catalog_keys.append(delete_catalog_image.key)
               delete_catalog_image_keys.append(delete_catalog_image.image)
          
          if len(delete_catalog_keys):
            ndb.delete_multi(delete_catalog_keys)
               # blob manager will delete the images
            blob.Manager.unused_blobs(delete_catalog_image_keys)
                 
          context.log.entities.append((entity, ))
          log.Engine.run(context)
          rule.read(entity)
          context.output['entity'] = entity
          context.callback.payloads.append(('notify',
                                              {'action_key': 'initiate',
                                               'action_model': '61',
                                               'entity_key': entity.key.urlsafe()}))
          callback.Engine.run(context)
         
       transaction()
 
       
    @classmethod
    def lock(cls, context):
       
        # @todo
        # discontinue consequences
        entity_key = context.input.get('key')
        entity = entity_key.get()
        context.rule.entity = entity
        rule.Engine.run(context)
        if not rule.executable(context):
          raise rule.ActionDenied(context)
        
        @ndb.transactional(xg=True)
        def transaction():
          rule.write(entity, {'state': 'locked'})
          entity.put()
          rule.Engine.run(context)
          context.log.entities.append((entity, {'message': context.input.get('message')}))
          log.Engine.run(context)
          context.callback.payloads.append(('notify',
                                            {'action_key': 'initiate',
                                             'action_model': '61',
                                             'entity_key': entity.key.urlsafe()}))
          callback.Engine.run(context)
          rule.read(entity)
          context.output['entity'] = entity
        
        transaction()
      
    @classmethod
    def discontinue(cls, context):
      
        # @todo
        # discontinue consequences
 
        entity_key = context.input.get('key')
        entity = entity_key.get()
        context.rule.entity = entity
        rule.Engine.run(context)
        if not rule.executable(context):
          raise rule.ActionDenied(context)
        
        @ndb.transactional(xg=True)
        def transaction():
          rule.write(entity, {'state': 'discontinued'})
          entity.put()
          rule.Engine.run(context)
          context.log.entities.append((entity, {'message': context.input.get('message')}))
          log.Engine.run(context)
          context.callback.payloads.append(('notify',
                                            {'action_key': 'initiate',
                                             'action_model': '61',
                                             'entity_key': entity.key.urlsafe()}))
          callback.Engine.run(context)
          rule.read(entity)
          context.output['entity'] = entity
        
        transaction()
 
 
    @classmethod
    def publish(cls, context):
        
        # @todo
        # publish date 
        # checking if user has enough credts
        # and some reactions to other things when the catalog gets published
 
        entity_key = context.input.get('key')
        entity = entity_key.get()
        context.rule.entity = entity
        rule.Engine.run(context)
        if not rule.executable(context):
          raise rule.ActionDenied(context)
        
        @ndb.transactional(xg=True)
        def transaction():
          rule.write(entity, {'state': 'published'})
          entity.put()
          rule.Engine.run(context)
          context.log.entities.append((entity, {'message': context.input.get('message')}))
          log.Engine.run(context)
          context.callback.payloads.append(('notify',
                                            {'action_key': 'initiate',
                                             'action_model': '61',
                                             'entity_key': entity.key.urlsafe()}))
          callback.Engine.run(context)
          rule.read(entity)
          context.output['entity'] = entity
        
        transaction()
           
 
    @classmethod
    def log_message(cls, context):
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      
      @ndb.transactional(xg=True)
      def transaction():
        entity.put()  # We update this entity (before logging it) in order to set the value of the 'updated' property to newest date.
        values = {'message': context.input.get('message'), 'note': context.input.get('note')}
        if not rule.writable(context, '_records.note'):
          values.pop('note')
        context.log.entities.append((entity, values))
        log.Engine.run(context)
        context.callback.payloads.append(('notify',
                                          {'action_key': 'initiate',
                                           'action_model': '61',
                                           'entity_key': entity.key.urlsafe()}))
        callback.Engine.run(context)
        rule.read(entity)
        context.output['entity'] = entity
      
      transaction()
 
      
    @classmethod
    def duplicate(cls, context):
        # how we are going to duplicate the catalog? copy-paste the blobs?
        pass
  
    @classmethod
    def upload_images(cls, context):
      
      upload_url = context.input.get('upload_url')
      images = context.input.get('images')
      entity_key = context.input.get('key')
      entity = entity_key.get()
   
      context.rule.entity = entity
      rule.Engine.run(context)
        
      if not rule.executable(context):
        raise rule.ActionDenied(context)
            
      if upload_url:
         context.output['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.CATALOG_IMAGE_BUCKET)
         return # exit here no need to continue
      else:
         if not images: # if no images were saved, do nothing...
           return

      i = cls.query(ancestor=entity_key).count() # get last sequence
   
      for image in images:
          i += 1
          image.set_key(str(i), parent=entity.key)
          image.sequence = i
      
      @ndb.transactional(xg=True)
      def transaction():
        
          ndb.put_multi(images)
    
          for saved in images:
              if saved:
                 context.log.entities.append((saved,))
                 
          log.Engine.run(context)
          
          # after log runs, mark all blobs as used, because log can also throw error
          for saved in images:
              if saved:
                 blob.Manager.used_blobs(saved.image)
          
          entity._images.extend(images)      
          rule.read(entity)
           
          context.output['entity'] = entity

      transaction()
      
    @classmethod
    def prepare(cls, context):
      domain_key = context.input.get('domain')
      context.cruds.domain_key = domain_key
      context.cruds.model = cls
      cruds.Engine.prepare(context)
 
    @classmethod
    def read(cls, context):
      entity_key = context.input.get('key')
      next = context.input.get('next')
      entity = entity_key.get()
      if not context.rule.entity:
        context.rule.entity = entity
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      
      """
      images = []
      # i think this pager is not needed because we can load all images at once, but not show them all at once... that is a lot more efficient...
      get_images = ndb.get_multi([CatalogImage.build_key(str(i), parent=entity_key) for i in range(next, settings.CATALOG_IMAGES_PER_PAGE+next)])
      for get in get_images:
        if get:
          images.append(get)
          
      """
      
      images = CatalogImage.query(parent=entity_key).fetch(CatalogImage.sequence)
          
      entity._images = images
      
      rule.read(entity)
      context.output['entity'] = entity
  
 
    @classmethod
    def read_records(cls, context):
      context.cruds.model = cls
      cruds.Engine.read_records(context)