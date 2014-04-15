# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import itertools
import hashlib
import copy
 
from app import ndb, settings
from app.srv import event, uom, blob, rule, log, callback, cruds

from google.appengine.ext import blobstore
 

# this model will either serve as LocalStructuredProperty of Template/Instance, or will fan-out as single child entity
# of Template, packed with multiple contents
# this entity will reference only one Template/Instance, not multiple.. that will require Duplicate Product feature!
class Content(ndb.BaseModel):
    
    _kind = 43
    
    # ancestor DomainCatalog (future - root) (namespace Domain)
    # composite index: ancestor:yes - title
    title = ndb.SuperStringProperty('1', required=True)
    body = ndb.SuperTextProperty('2', required=True)
    

# this model will either serve as LocalStructuredProperty of Template, or will fan-out as single child entity
# of Template, packed with multiple variants
# this entity will reference only one Template/Instance, not multiple.. that will require Duplicate Product feature!
class Variant(ndb.BaseModel):
    
    _kind = 42
    
    # ancestor DomainCatalog (future - root) (namespace Domain)
    # http://v6apps.openerp.com/addon/1809
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    description = ndb.SuperTextProperty('2')# soft limit 64kb
    options = ndb.SuperStringProperty('3', repeated=True, indexed=False)# soft limit 1000x
    allow_custom_value = ndb.SuperBooleanProperty('4', default=False, indexed=False)# ovu vrednost buyer upisuje u definisano polje a ona se dalje prepisuje u order line description prilikom Add to Cart


class Image(blob.Image):
  
  _kind = 76


class Images(ndb.BaseModel):
  
  _kind = 73
  
  images = ndb.SuperLocalStructuredProperty(Image, '1')


class Variants(ndb.BaseModel):
  
  _kind = 74
  
  variants = ndb.SuperLocalStructuredProperty(Variant, '1')


class Contents(ndb.BaseModel):
  
  _kind = 75
  
  contents = ndb.SuperLocalStructuredProperty(Content, '1')

# done!
class Category(ndb.BaseModel):
    
    _kind = 17
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/category.py#l8
    # https://support.google.com/merchants/answer/1705911
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L227
    # composite index: ancestor:no - status,name
 
    parent_record = ndb.SuperKeyProperty('1', kind='17', indexed=False)
    name = ndb.SuperStringProperty('2', required=True)
    complete_name = ndb.SuperTextProperty('3')# da je ovo indexable bilo bi idealno za projection query
    state = ndb.SuperStringProperty('4', default='active', required=True) # @todo status => state ? better ? for convention ? or just active = boolean 
    
    _global_role = rule.GlobalRole(permissions=[
        rule.ActionPermission('17', [event.Action.build_key('17-0').urlsafe(),
                                     event.Action.build_key('17-1').urlsafe(),
                                     event.Action.build_key('17-2').urlsafe(),
                                     event.Action.build_key('17-3').urlsafe(),
                                     event.Action.build_key('17-4').urlsafe(),
                                     event.Action.build_key('17-5').urlsafe(),
                                     event.Action.build_key('17-6').urlsafe(),
                                     event.Action.build_key('17-7').urlsafe(),
                                     event.Action.build_key('17-8').urlsafe(),], True, 'True'),
        rule.FieldPermission('17', ['parent_record', 'name', 'complete_name', 'state'], True, True, 'True')
    ]) 

    _actions = {
       'create' : event.Action(id='17-0',
                              arguments={
                                 'parent_record' : ndb.SuperKeyProperty(kind='17', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'state' : ndb.SuperStringProperty(),
                              }
                             ),
                
       'update' : event.Action(id='17-1',
                              arguments={
                                 'parent_record' : ndb.SuperKeyProperty(kind='17', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'state' : ndb.SuperStringProperty(),
                                 'key' : ndb.SuperKeyProperty(kind='17', required=True)
                              }
                             ),
                
       'delete' : event.Action(id='17-2',
                              arguments={
                                   'key' : ndb.SuperKeyProperty(kind='17', required=True)
                              }
                             ),
                
       'search' : event.Action(
        id='17-3',
        arguments={
          'search': ndb.SuperSearchProperty(
            default={"filters": [], "order_by": {"field": "name", "operator": "desc"}},
            filters={
              'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
              'state': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
              },
            indexes=[
              {'filter': [],
               'order_by': [['name', ['asc', 'desc']],]},
              {'filter': ['name'],
               'order_by': [['name', ['asc', 'desc']],]},
              {'filter': ['state'],
               'order_by': [['name', ['asc', 'desc']],]},
              {'filter': ['name', 'state'],
               'order_by': [['name', ['asc', 'desc']],]},
              ],
            order_by={
              'name': {'operators': ['asc', 'desc']},
              }
            ),
        'next_cursor': ndb.SuperStringProperty()
        }
       ),
       'read' : event.Action(id='17-6',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='17', required=True),
                              }
        ),  
       'read_records' : event.Action(id='17-7',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='17', required=True),
                                  'next_cursor': ndb.SuperStringProperty()
                              }
        ),
       'prepare' : event.Action(id='17-8',
                              arguments={}
        ),  
    }
        
    
    @classmethod
    def complete_save(cls, context):
      parent = context.input.get('parent_record')
      complete_name = None
      if parent:
        parent_record = parent.get()
        complete_name = ndb.make_complete_name(parent_record, 'name', 'parent_record')
      return {'parent_record' : context.input.get('parent_record'),
              'name' : context.input.get('name'),
              'complete_name' : complete_name,
              'state' : context.input.get('state')}
    
    @classmethod
    def create(cls, context):
      values = cls.complete_save(context)
      context.rule.skip_user_roles = True
      context.cruds.entity = cls()
      context.cruds.values = values
      cruds.Engine.create(context)
    
    @classmethod
    def update(cls, context):
      values = cls.complete_save(context)
      context.rule.skip_user_roles = True
      context.cruds.entity = context.input.get('key').get()
      context.cruds.values = values
      cruds.Engine.update(context)
    
    @classmethod
    def delete(cls, context):
      context.rule.skip_user_roles = True
      context.cruds.entity = context.input.get('key').get()
      cruds.Engine.delete(context)
    
    @classmethod
    def search(cls, context):
      context.rule.skip_user_roles = True
      context.cruds.entity = cls()
      cruds.Engine.search(context)
    
    @classmethod
    def read(cls, context):
      context.rule.skip_user_roles = True
      context.cruds.entity = context.input.get('key').get()
      cruds.Engine.read(context)
      
    @classmethod
    def read_records(cls, context):
      context.rule.skip_user_roles = True
      context.cruds.entity = context.input.get('key').get()
      cruds.Engine.read_records(context)
    
    @classmethod
    def prepare(cls, context):
      context.rule.skip_user_roles = True
      context.cruds.entity = cls()
      cruds.Engine.prepare(context)
      

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
    code = ndb.SuperStringProperty('7', required=True)
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
      'weight' : ndb.SuperPickleProperty('8'),# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
      'volume' : ndb.SuperPickleProperty('9'),# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
      'low_stock_quantity' : ndb.SuperDecimalProperty('10', default='0.00'),# notify store manager when qty drops below X quantity
     }
    
    _virtual_fields = {
       '_images' : ndb.SuperLocalStructuredProperty(Image, repeated=True),
       '_contents' : ndb.SuperLocalStructuredProperty(Content, repeated=True),
       '_variants' : ndb.SuperLocalStructuredProperty(Variant, repeated=True),
       '_records': log.SuperLocalStructuredRecordProperty('38', repeated=True),
     }
   
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('38', event.Action.build_key('38-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('38', event.Action.build_key('38-4').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('38', event.Action.build_key('38-1').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('38', event.Action.build_key('38-2').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('38', event.Action.build_key('38-3').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                             ]) 

    _actions = {
       'create' : event.Action(id='38-0',
                              arguments={
                             
                                 'product_category' : ndb.SuperKeyProperty(kind='17', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'description' : ndb.SuperTextProperty(required=True),# soft limit 64kb
                                 'product_uom' : ndb.SuperKeyProperty(kind=uom.Unit, required=True),
                                 'unit_price' : ndb.SuperDecimalProperty(required=True),
                                 'availability' : ndb.SuperIntegerProperty(required=True),#
                                  
                                 'weight' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
                                 'volume' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
                                 'low_stock_quantity' : ndb.SuperDecimalProperty(default='0.00'),# notify store manager when qty drops below X quantity
                  
                                 'catalog' : ndb.SuperKeyProperty(kind='35', required=True),
             
                              }
                             ),
                
       'update' : event.Action(id='38-1',
                              arguments={
                                         
                                 '_variants' : ndb.SuperLocalStructuredProperty(Variant, repeated=True),# soft limit 100x
                                 '_contents' : ndb.SuperLocalStructuredProperty(Content, repeated=True),# soft limit 100x
                                 '_images' : ndb.SuperLocalStructuredProperty(Image, repeated=True),# soft limit 100x
                                       
                                 'product_category' : ndb.SuperKeyProperty(kind='17', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'description' : ndb.SuperTextProperty(required=True),# soft limit 64kb
                                 'product_uom' : ndb.SuperKeyProperty(kind=uom.Unit, required=True),
                                 'unit_price' : ndb.SuperDecimalProperty(required=True),
                                 'availability' : ndb.SuperIntegerProperty(required=True),#
                             
                                 'weight' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
                                 'volume' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
                                 'low_stock_quantity' : ndb.SuperDecimalProperty(default='0.00'),# notify store manager when qty drops below X quantity
                    
                                 'key' : ndb.SuperKeyProperty(kind='38', required=True)
                              }
                             ),
 
       'search' : event.Action(
        id='38-3',
        arguments={
          'catalog': ndb.SuperKeyProperty(kind='38', required=True),
          'search': ndb.SuperSearchProperty(
            default={"filters": [], "order_by": {"field": "name", "operator": "desc"}},
            filters={
              'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
              'product_category': {'operators': ['==', '!='], 'type': ndb.SuperKeyProperty(kind='17')},
              },
            indexes=[
              {'filter': [],
               'order_by': [['name', ['asc', 'desc']],]},
              {'filter': ['name'],
               'order_by': [['name', ['asc', 'desc']],]},
              {'filter': ['product_category'],
               'order_by': [['name', ['asc', 'desc']],]},
              {'filter': ['name', 'product_category'],
               'order_by': [['name', ['asc', 'desc']],]},
              ],
            order_by={
              'name': {'operators': ['asc', 'desc']},
              }
            ),
        'next_cursor': ndb.SuperStringProperty()
        }
       ),
                 
       'generate_product_instances' : event.Action(id='38-4',
                              arguments={
                                  'key' : ndb.SuperKeyProperty(kind='38'),
                              }
                             ),
                
       'upload_images' : event.Action(id='38-5',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='38', required=True),
                                 'images' : ndb.SuperLocalStructuredImageProperty(Image, repeated=True),
                                 'upload_url' : ndb.SuperStringProperty(),
                              }
        ),
       'read' : event.Action(id='38-6',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='38', required=True),
                              }
        ),  
       'read_records' : event.Action(id='38-7',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='38', required=True),
                                  'next_cursor': ndb.SuperStringProperty()
                              }
        ),
       'prepare' : event.Action(id='38-8',
                              arguments={
                                  'catalog' : ndb.SuperKeyProperty(kind='38', required=True)
                              }
        ),  
       'duplicate' : event.Action(id='38-9',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='38', required=True),
                              }
        ),       
       
    }
    
    def _single_entity_key(self, model):
      """Builds singular key from the key_id_str with parent"""
      return model.build_key(self.key_id_str, parent=self.key)
    
    def get_single_entities(self):
      """Gets all storage entities for the product template. Returns list in order [Contents, Images, Variants]"""
      return ndb.get_multi([self._single_entity_key(model) for model in [Contents, Images, Variants]])
    
    def populate_single_entities(self):
      """Single-handedly retrieves all storage entities and populates the virtual fields along with it""" 
      
      contents, images, variants = self.get_single_entities()
      
      if contents:
        self._contents = contents.contents
        
      if images:
        self._images = images.images
        
      if variants:
        self._variants = variants.variants
        
        
    @classmethod
    def create(cls, context):
      
      catalog_key = context.input.get('catalog')
      catalog = catalog_key.get()
      
      context.cruds.entity = cls(namespace=catalog.key_namespace)
      context.cruds.values = context.input
      cruds.Engine.create(context)
 

    @classmethod
    def update(cls, context):
      
       entity_key = context.input.get('key')
       _images = context.input.get('_images')
       _contents = context.input.get('_contents')
       _variants = context.input.get('_variants')
       
       entity = entity_key.get()
  
       context.rule.entity = entity
       rule.Engine.run(context)
        
       if not rule.executable(context):
         raise rule.ActionDenied(context)   
       
       entity.populate_single_entities() # retrieve from storage
       
       contents, images, variants = entity.get_single_entities()
 
       @ndb.transactional(xg=True)
       def transaction():
           
          copy_current_images = copy.copy(entity._images) # ahold the current images
 
          values = context.input
      
          rule.write(entity, values)
           
          contents.contents = entity._contents
          images.images = entity._images
          variants.variants = entity._variants
          
          ndb.put_multi([entity, contents, images, variants])
 
          delete_catalog_image_keys = []
          possible_keys = [image.image for image in entity._images]
          
          for copy_current_image in copy_current_images:
             if copy_current_image.image not in possible_keys:
                delete_catalog_image_keys.append(copy_current_image.image)
          
          blob.Manager.unused_blobs(delete_catalog_image_keys) # delete all images that were removed from the list
                 
          context.log.entities.append((entity, ))
          log.Engine.run(context)
          rule.read(entity)
          context.output['entity'] = entity
          context.callback.payloads.append(('notify',
                                              {'action_key': 'initiate',
                                               'action_model': '61',
                                               'caller_entity': entity.key.urlsafe()}))
          callback.Engine.run(context)
         
       transaction()
       
       
    @classmethod
    def search(cls, context):
      catalog_key = context.input.get('catalog')
      context.cruds.entity = cls(parent=catalog_key)
      cruds.Engine.search(context)
    
    
    @classmethod
    def read(cls, context):
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
   
      entity.populate_single_entities()
      
      rule.read(entity)
      context.output['entity'] = entity
      context.output['categories'] = Category.query().fetch()
      
      
    @classmethod
    def read_records(cls, context):
      context.cruds.entity = context.input.get('key').get()
      cruds.Engine.read_records(context)
    
    
    @classmethod
    def prepare(cls, context):
      catalog_key = context.input.get('catalog')
      context.cruds.entity = cls(parent=catalog_key)
      cruds.Engine.prepare(context)
      
      context.output['categories'] = Category.query().fetch()
 
 
    @classmethod
    def upload_images(cls, context):
      
      upload_images = context.input.get('images')
      upload_url = context.input.get('upload_url')
 
      if upload_url:
         context.output['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.PRODUCT_TEMPLATE_BUCKET)
         return # exit here no need to continue
      else:
         if not upload_images: # if no images were saved, do nothing...
           return
          
      entity_key = context.input.get('key')
      entity = entity_key.get()
   
      context.rule.entity = entity
      rule.Engine.run(context)
        
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      
      entity.populate_single_entities()
      
      contents, images, variants = entity.get_single_entities()

      i = len(entity._images) # get last sequence

      for image in upload_images:
          i += 1
          image.sequence = i
      
      @ndb.transactional(xg=True)
      def transaction():
          
          images.images.extend(upload_images)
          images.put()
          
          context.log.entities.append((entity,))
           
          log.Engine.run(context)
          
          # after log runs, mark all blobs as used, because log can also throw error
          for saved in upload_images:
              if saved:
                 blob.Manager.used_blobs(saved.image)
          
          entity._images.extend(upload_images)
          rule.read(entity)
           
          context.output['entity'] = entity

      transaction()
      
      
    @classmethod
    def generate_product_instances(cls, context):
      
       ### to be depracated
       
       entity_key = context.input.get('key')
       entity = entity_key.get()
      
       entity.populate_single_entities()
      
       context.rule.entity = entity
       rule.Engine.run(context)
      
       if not rule.executable(context):
         raise rule.ActionDenied(context)
 
       @ndb.transactional(xg=True)
       def transaction():
                 
            # cant go delete multi cuz we also need to delete images
            # ndb.delete_multi(Instance.query(ancestor=entity_key).fetch(keys_only=True))
            for p in Instance.query(ancestor=entity_key).fetch():
                 p.delete()
              
            variants = entity._variants
            packer = list()
             
            for v in variants:
                 packer.append(v.options)
                 
            if not packer:
              #return context.error('generator', 'empty_generator')
              return
                 
            create_variations = itertools.product(*packer)
             
            context.output['instances'] = list()
            
            if len(create_variations) > 1000:
               code = '%s_%s' % (entity_key.urlsafe(), 1)
               inst = Instance(parent=entity_key, id=code, code=code)
               inst.put()
            
            else:   
              i = 1
              for c in create_variations:
                   code = '%s_%s' % (entity_key.urlsafe(), i)
                   compiled = Instance.md5_variation_combination(c)
                   inst = Instance(parent=entity_key, id=compiled, code=code)
                   inst.put()
                   context.log.entities.append((inst, ))
                   i += 1
                   context.output['instances'].append(inst)
 
            log.Engine.run(context)
              
       transaction()
       
    @classmethod
    def duplicate(cls, context):
        # how we are going to duplicate the catalog? copy-paste the blobs?
        pass
       
 
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
     
    _default_indexed = False
 
    _expando_fields = {
      'code' : ndb.SuperStringProperty('1', required=True),              
      'availability' : ndb.SuperIntegerProperty('2', required=True), # overide availability vrednosti sa product_template-a, inventory se uvek prati na nivou instanci, state je stavljen na template kako bi se olaksala kontrola state-ova. 
      'description'  : ndb.SuperTextProperty('3', required=True), # soft limit 64kb
      'unit_price' : ndb.SuperDecimalProperty('4', required=True),
      'low_stock_quantity' : ndb.SuperDecimalProperty('5', default='0.00'), # notify store manager when qty drops below X quantity
      'weight' : ndb.SuperStringProperty('6'), # prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
      'volume' : ndb.SuperStringProperty('7'), # prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
     }
     
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('39', event.Action.build_key('39-0').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            rule.ActionPermission('39', event.Action.build_key('39-1').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.parent_entity.state == 'unpublished')"),
                                            ]) 

    _actions = {
       'update' : event.Action(id='39-0',
                              arguments={
                     
                                 'code' : ndb.SuperStringProperty(required=True),
                                 'availability' : ndb.SuperIntegerProperty(),#
                                 'description' : ndb.SuperTextProperty(),# soft limit 64kb
                                 'unit_price' : ndb.SuperDecimalProperty(),
                                 
                                 '_contents' : ndb.SuperLocalStructuredProperty(Content, repeated=True),# soft limit 100x
                                 '_variants' : ndb.SuperLocalStructuredProperty(Variant, repeated=True),# soft limit 100x
                                 '_images' : ndb.SuperLocalStructuredProperty(Image, repeated=True),# soft limit 100x
                                 
                                 'weight' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
                                 'volume' : ndb.SuperStringProperty(),# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
                            
                                 'key' : ndb.SuperKeyProperty(kind='39', required=True)
                              }
      ),
      'upload_images' : event.Action(id='39-1',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='39', required=True),
                                 'images' : ndb.SuperLocalStructuredImageProperty(Image, repeated=True),
                                 'upload_url' : ndb.SuperStringProperty(),
                              }
      ),
                
      'search' : event.Action(
        id='39-2',
        arguments={
          'search': ndb.SuperSearchProperty(
            default={"filters": [], "order_by": {"field": "code", "operator": "desc"}},
            filters={
              'code': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
              },
            indexes=[
              {'filter': [],
               'order_by': [['code', ['asc', 'desc']],]},
              {'filter': ['code'],
               'order_by': [['code', ['asc', 'desc']],]},
              ],
            order_by={
              'code': {'operators': ['asc', 'desc']},
              }
            ),
        'next_cursor': ndb.SuperStringProperty()
        }
       ),
       'read' : event.Action(id='39-3',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='39', required=True),
                              }
        ),  
       'read_records' : event.Action(id='39-4',
                              arguments={
                                  'key'  : ndb.SuperKeyProperty(kind='39', required=True),
                                  'next_cursor': ndb.SuperStringProperty()
                              }
        ),
  
    }
    
    def delete(self):
      self.populate_single_entities()
      blob.Manager.unused_blobs([img.image for img in self._images])
      self.key.delete()
      
    
    @classmethod
    def md5_variation_combination(cls, codes):
        codes = list(codes)
        return hashlib.md5(u'-'.join(codes)).hexdigest()
     
    def _single_entity_key(self, model):
      """Builds singular key from the key_id_str with parent"""
      return model.build_key(self.key_id_str, parent=self.key)
    
    def get_single_entities(self):
      """Gets all storage entities for the product template. Returns list in order [Contents, Images, Variants]"""
      return ndb.get_multi([self._single_entity_key(model) for model in [Contents, Images, Variants]])
    
    def populate_single_entities(self):
      """Single-handedly retrieves all storage entities and populates the virtual fields along with it""" 
      
      contents, images, variants = self.get_single_entities()
      
      if contents:
        self._contents = contents.contents
        
      if images:
        self._images = images.images
        
      if variants:
        self._variants = variants.variants
        
    @classmethod
    def upload_images(cls, context):
      
      upload_images = context.input.get('images')
      upload_url = context.input.get('upload_url')
 
      if upload_url:
         context.output['upload_url'] = blobstore.create_upload_url(upload_url, gs_bucket_name=settings.PRODUCT_TEMPLATE_BUCKET)
         return # exit here no need to continue
      else:
         if not upload_images: # if no images were saved, do nothing...
           return
          
      entity_key = context.input.get('key')
      entity = entity_key.get()
   
      context.rule.entity = entity
      rule.Engine.run(context)
        
      if not rule.executable(context):
        raise rule.ActionDenied(context)
      
      entity.populate_single_entities()
      
      contents, images, variants = entity.get_single_entities()

      i = len(entity._images) # get last sequence

      for image in upload_images:
          i += 1
          image.sequence = i
      
      @ndb.transactional(xg=True)
      def transaction():
          
          images.images.extend(upload_images)
          images.put()
          
          context.log.entities.append((entity,))
           
          log.Engine.run(context)
          
          # after log runs, mark all blobs as used, because log can also throw error
          for saved in upload_images:
              if saved:
                 blob.Manager.used_blobs(saved.image)
          
          entity._images.extend(upload_images)
          rule.read(entity)
           
          context.output['entity'] = entity

      transaction()
      
    @classmethod
    def update(cls, context):
      
       entity_key = context.input.get('key')
       _images = context.input.get('_images')
       _contents = context.input.get('_contents')
       _variants = context.input.get('_variants')
       
       entity = entity_key.get()
  
       context.rule.entity = entity
       rule.Engine.run(context)
        
       if not rule.executable(context):
         raise rule.ActionDenied(context)   
       
       entity.populate_single_entities() # retrieve from storage
       
       contents, images, variants = entity.get_single_entities()
 
       @ndb.transactional(xg=True)
       def transaction():
           
          copy_current_images = copy.copy(entity._images) # ahold the current images
 
          values = context.input
      
          rule.write(entity, values)
           
          contents.contents = entity._contents
          images.images = entity._images
          variants.variants = entity._variants
          
          ndb.put_multi([entity, contents, images, variants])
 
          delete_catalog_image_keys = []
          possible_keys = [image.image for image in entity._images]
          
          for copy_current_image in copy_current_images:
             if copy_current_image.image not in possible_keys:
                delete_catalog_image_keys.append(copy_current_image.image)
          
          blob.Manager.unused_blobs(delete_catalog_image_keys) # delete all images that were removed from the list
                 
          context.log.entities.append((entity, ))
          log.Engine.run(context)
          rule.read(entity)
          context.output['entity'] = entity
          context.callback.payloads.append(('notify',
                                              {'action_key': 'initiate',
                                               'action_model': '61',
                                               'caller_entity': entity.key.urlsafe()}))
          callback.Engine.run(context)
         
       transaction()
       
       
    @classmethod
    def search(cls, context):
      catalog_key = context.input.get('catalog')
      context.cruds.entity = cls(parent=catalog_key)
      cruds.Engine.search(context)
    
    
    @classmethod
    def read(cls, context):
      entity_key = context.input.get('key')
      entity = entity_key.get()
      context.rule.entity = entity
      
      rule.Engine.run(context)
      if not rule.executable(context):
        raise rule.ActionDenied(context)
   
      entity.populate_single_entities()
      
      rule.read(entity)
      context.output['entity'] = entity
      context.output['categories'] = Category.query().fetch()
      
      
    @classmethod
    def read_records(cls, context):
      context.cruds.entity = context.input.get('key').get()
      cruds.Engine.read_records(context)
