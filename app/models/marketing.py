# -*- coding: utf-8 -*-
'''
Created on May 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime

from app import orm, util, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.marketing import *


class ProductCategory(orm.BaseModel):
  
  _kind = 17
  
  _use_record_engine = False
  
  parent_record = orm.SuperKeyProperty('1', kind='17', indexed=False)
  name = orm.SuperStringProperty('2', required=True)
  complete_name = orm.SuperTextProperty('3', required=True)
  state = orm.SuperStringProperty('4', required=True, default='indexable')
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('17', [orm.Action.build_key('17', 'update')], True, 'user._root_admin or user._is_taskqueue'),
      orm.ActionPermission('17', [orm.Action.build_key('17', 'search')], True, 'not user._is_guest'),
      orm.FieldPermission('17', ['parent_record', 'name', 'complete_name', 'state'], False, True, 'True'),
      orm.FieldPermission('17', ['parent_record', 'name', 'complete_name', 'state'], True, True,
                          'user._root_admin or user._is_taskqueue')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('17', 'update'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            ProductCategoryUpdateWrite(cfg={'file': settings.PRODUCT_CATEGORY_DATA_FILE,
                                            'prod_env': settings.DEVELOPMENT_SERVER})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('17', 'search'),  # @todo Search is very inaccurate when using 'contains' filter. so we will have to use here document search i think.
      arguments={  # @todo Add default filter to list active ones.
        'search': orm.SuperSearchProperty(
          default={'filters': [{'field': 'state', 'value': 'indexable', 'operator': '=='}], 'orders': [{'field': 'name', 'operator': 'asc'}]},
          cfg={
            'search_by_keys': True,
            'search_arguments': {'kind': '17', 'options': {'limit': settings.SEARCH_PAGE}},
            'filters': {'name': orm.SuperStringProperty(),
                        'state': orm.SuperStringProperty(choices=['indexable'])},
            'indexes': [{'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('name', ['==', 'contains', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!=']), ('name', ['==', 'contains', '!='])],
                         'orders': [('name', ['asc', 'desc'])]}]
            }
          )
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Search(),
            RulePrepare(cfg={'path': '_entities', 'skip_user_roles': True}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      )
    ]


class ProductContent(orm.BaseModel):
  
  _kind = 43
  
  title = orm.SuperStringProperty('1', required=True, indexed=False)
  body = orm.SuperTextProperty('2', required=True)


class ProductVariant(orm.BaseModel):
  
  _kind = 42
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  description = orm.SuperTextProperty('2')
  options = orm.SuperStringProperty('3', repeated=True, indexed=False)
  allow_custom_value = orm.SuperBooleanProperty('4', required=True, indexed=False, default=False)


class ProductInstance(orm.BaseExpando):
  
  _kind = 39
  
  _use_rule_engine = False
  
  variant_signature = orm.SuperJsonProperty('1', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'description': orm.SuperTextProperty('2'),
    'unit_price': orm.SuperDecimalProperty('3'),
    'availability': orm.SuperStringProperty('4', default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
    'code': orm.SuperStringProperty('5'),
    'weight': orm.SuperDecimalProperty('6'),
    'weight_uom': orm.SuperKeyProperty('7', kind='19'),
    'volume': orm.SuperDecimalProperty('8'),
    'volume_uom': orm.SuperKeyProperty('9', kind='19'),
    'images': SuperImageLocalStructuredProperty(Image, '10', repeated=True),
    'contents': orm.SuperLocalStructuredProperty(ProductContent, '11', repeated=True),
    'low_stock_quantity': orm.SuperDecimalProperty('12', default='0.00')
    }
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    variant_signature = input.get('variant_signature')
    key_id = hashlib.md5(json.dumps(variant_signature)).hexdigest()
    product_instance_key = cls.build_key(key_id, parent=kwargs.get('parent'))
    return product_instance_key
  
  def prepare(self, **kwargs):
    self.key = self.prepare_key({'variant_signature': self.variant_signature}, **kwargs)


class Product(orm.BaseExpando):
  
  _kind = 38
  
  product_category = orm.SuperKeyProperty('1', kind='17', required=True, searchable=True)
  name = orm.SuperStringProperty('2', required=True, searchable=True)
  description = orm.SuperTextProperty('3', required=True, searchable=True)  # Soft limit 64kb.
  product_uom = orm.SuperKeyProperty('4', kind='19', required=True, indexed=False)
  unit_price = orm.SuperDecimalProperty('5', required=True, indexed=False)
  availability = orm.SuperStringProperty('6', required=True, indexed=False, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock'])
  code = orm.SuperStringProperty('7', required=True, indexed=False, searchable=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'weight': orm.SuperDecimalProperty('8'),
    'weight_uom': orm.SuperKeyProperty('9', kind='19'),
    'volume': orm.SuperDecimalProperty('10'),
    'volume_uom': orm.SuperKeyProperty('11', kind='19'),
    'images': SuperImageLocalStructuredProperty(Image, '12', repeated=True),
    'contents': orm.SuperLocalStructuredProperty(ProductContent, '13', repeated=True),
    'variants': orm.SuperLocalStructuredProperty(ProductVariant, '14', repeated=True),
    'low_stock_quantity': orm.SuperDecimalProperty('15', default='0.00')  # Notify store manager when quantity drops below X quantity.
    }
  
  _virtual_fields = {
    '_instances': orm.SuperStorageStructuredProperty(ProductInstance, storage='remote_multi')
    }


class CatalogPricetag(orm.BaseModel):
  
  _kind = 34
  
  product = orm.SuperKeyProperty('1', kind='38', required=True, indexed=False)
  image_width = orm.SuperIntegerProperty('2', required=True, indexed=False)  # @todo We will test pricetag positioning without these values!
  image_height = orm.SuperIntegerProperty('3', required=True, indexed=False)  # @todo We will test pricetag positioning without these values!
  position_top = orm.SuperFloatProperty('4', required=True, indexed=False)
  position_left = orm.SuperFloatProperty('5', required=True, indexed=False)
  value = orm.SuperStringProperty('6', required=True, indexed=False)


class CatalogImage(Image):
  
  _kind = 36
  
  sequence = orm.SuperIntegerProperty('7', required=True, indexed=True)
  pricetags = orm.SuperLocalStructuredProperty(CatalogPricetag, '8', repeated=True)
  
  def prepare(self, **kwds):
    key_id = self.key_id
    if key_id is None:
      self.set_key(key_id, parent=kwds.get('parent'))
      key = 'prepare_%s' % self.key.urlsafe()
      sequence = mem.temp_get(key, util.Nonexistent)
      if sequence is util.Nonexistent:
        entity = self.query(ancestor=self.key.parent()).order(-self.__class__.sequence).get()
        if not entity:
          sequence = 0
        else:
          sequence = entity.sequence
        mem.temp_set(key, sequence)
      self.sequence = self._sequence + sequence


class Catalog(orm.BaseExpando):
  
  _kind = 35
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True, searchable=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True, searchable=True)
  name = orm.SuperStringProperty('3', required=True, searchable=True)
  publish_date = orm.SuperDateTimeProperty('4', required=True, searchable=True)
  discontinue_date = orm.SuperDateTimeProperty('5', required=True, searchable=True)
  state = orm.SuperStringProperty('6', required=True, default='unpublished',
                                  choices=['unpublished', 'locked', 'published', 'discontinued'], searchable=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'cover': SuperImageLocalStructuredProperty(CatalogImage, '7', process_config={'copy': True, 'copy_name': 'cover',
                                                                                  'transform': True, 'width': 240,
                                                                                  'height': 100, 'crop_to_fit': True}),
    'cost': orm.SuperDecimalProperty('8')
    }
  
  _virtual_fields = {
    '_images': SuperImageStorageStructuredProperty(CatalogImage, storage='remote_multi',
                                                   read_arguments={'config': {'order': {'field': 'sequence',
                                                                                        'direction': 'asc'}}}),
    '_products': orm.SuperStorageStructuredProperty(Product, storage='remote_multi'),
    '_records': orm.SuperRecordProperty('35')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('35', [orm.Action.build_key('35', 'prepare'),
                                  orm.Action.build_key('35', 'create'),
                                  orm.Action.build_key('35', 'read'),
                                  orm.Action.build_key('35', 'update'),
                                  orm.Action.build_key('35', 'catalog_upload_images'),
                                  orm.Action.build_key('35', 'product_upload_images'),
                                  orm.Action.build_key('35', 'product_instance_upload_images'),
                                  orm.Action.build_key('35', 'search'),
                                  orm.Action.build_key('35', 'lock'),
                                  orm.Action.build_key('35', 'discontinue'),
                                  orm.Action.build_key('35', 'log_message'),
                                  orm.Action.build_key('35', 'catalog_duplicate'),
                                  orm.Action.build_key('35', 'product_duplicate')], False, 'entity._original.namespace_entity._original.state != "active"'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'update'),
                                  orm.Action.build_key('35', 'product_duplicate'),
                                  orm.Action.build_key('35', 'lock'),
                                  orm.Action.build_key('35', 'catalog_upload_images'),
                                  orm.Action.build_key('35', 'product_upload_images'),
                                  orm.Action.build_key('35', 'product_instance_upload_images')], False, 'entity._original.state != "unpublished"'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'catalog_process_duplicate'),
                                  orm.Action.build_key('35', 'product_process_duplicate'),
                                  orm.Action.build_key('35', 'delete'),
                                  orm.Action.build_key('35', 'publish'),
                                  orm.Action.build_key('35', 'sudo'),
                                  orm.Action.build_key('35', 'index'),
                                  orm.Action.build_key('35', 'unindex'),
                                  orm.Action.build_key('35', 'cron')], False, 'True'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'discontinue'),
                                  orm.Action.build_key('35', 'catalog_duplicate')], False, 'entity._original.state != "published"'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'read')], True, 'entity._original.state == "published" or entity._original.state == "discontinued"'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'publish')], True, 'user._is_taskqueue and entity._original.state != "published" and entity._is_eligible'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'discontinue')], True, 'user._is_taskqueue and entity._original.state != "discontinued"'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'sudo')], True, 'user._root_admin'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'catalog_process_duplicate'),
                                  orm.Action.build_key('35', 'product_process_duplicate'),
                                  orm.Action.build_key('35', 'delete'),
                                  orm.Action.build_key('35', 'index'),
                                  orm.Action.build_key('35', 'unindex'),
                                  orm.Action.build_key('35', 'cron')], True, 'user._is_taskqueue'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'public_search')], True, 'True'),
      orm.FieldPermission('35', ['created', 'updated', 'state'], False, None, 'True'),
      orm.FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_products', '_records'], False, False,
                          'entity._original.namespace_entity._original.state != "active"'),
      orm.FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_products', '_records'], False, None,
                          'entity._original.state != "unpublished"'),
      orm.FieldPermission('35', ['state'], True, None,
                          '(action.key_id_str == "create" and entity.state == "unpublished") or (action.key_id_str == "lock" and entity.state == "locked") or (action.key_id_str == "publish" and entity.state == "published") or (action.key_id_str == "discontinue" and entity.state == "discontinued") or (action.key_id_str == "sudo" and (entity.state == "published" or entity.state == "discontinued"))'),
      orm.FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', '_images', '_products'], None, True,
                          'entity._original.state == "published" or entity._original.state == "discontinued"'),
      orm.FieldPermission('35', ['_records.note'], True, True,
                          'user._root_admin'),
      orm.FieldPermission('35', ['_records.note'], False, False,
                          'not user._root_admin'),
      orm.FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_products', '_records'], None, True,
                          'user._is_taskqueue or user._root_admin'),
      orm.FieldPermission('35', ['_images.image', '_images.content_type', '_images.size', '_images.gs_object_name', '_images.serving_url',
                                 '_products.images.image', '_products.images.content_type', '_products.images.size', '_images.proportion',
                                 '_products.images.gs_object_name', '_products.images.serving_url', '_products.images.proportion',
                                 '_products._instances.images.image', '_products._instances.images.content_type', '_products._instances.images.size',
                                 '_products._instances.images.gs_object_name', '_products._instances.images.serving_url', '_products._instances.images.proportion'], False, None,
                          '(action.key_id_str not in ["catalog_upload_images", "product_upload_images", "product_instance_upload_images", "catalog_process_duplicate", "product_process_duplicate"])'),
      orm.FieldPermission('35', ['_images', '_products.images', '_products._instances.images'], True, None,
                          '(action.key_id_str in ["catalog_upload_images", "product_upload_images", "product_instance_upload_images"])'),
      orm.FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost',
                                 '_products', '_images'], True, True,
                          '(action.key_id_str in ["catalog_process_duplicate", "product_process_duplicate"])')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('35', 'prepare'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'upload_url': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            BlobURL(cfg={'bucket': settings.BUCKET_PATH}),
            Set(cfg={'d': {'output.entity': '_catalog',
                           'output.upload_url': '_blob_url'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'create'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'name': orm.SuperStringProperty(required=True),
        'publish_date': orm.SuperDateTimeProperty(required=True),
        'discontinue_date': orm.SuperDateTimeProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_catalog.state': 'unpublished'},
                     'd': {'_catalog.name': 'input.name',
                           '_catalog.publish_date': 'input.publish_date',
                           '_catalog.discontinue_date': 'input.discontinue_date'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'name': orm.SuperStringProperty(required=True),
        'publish_date': orm.SuperDateTimeProperty(required=True),
        'discontinue_date': orm.SuperDateTimeProperty(required=True),
        '_images': orm.SuperLocalStructuredProperty(CatalogImage, repeated=True),
        '_products': orm.SuperLocalStructuredProperty(Product, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_catalog.name': 'input.name',
                           '_catalog.publish_date': 'input.publish_date',
                           '_catalog.discontinue_date': 'input.discontinue_date',
                           '_catalog._images': 'input._images',
                           '_catalog._products': 'input._products'}}),
            CatalogProcessCoverSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'catalog_upload_images'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        '_images': SuperImageLocalStructuredProperty(CatalogImage, argument_format_upload=True, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            UploadImages(cfg={'add_config': {'_images': 'input._images'}}),
            CatalogProcessCoverSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'product_upload_images'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'product': orm.SuperKeyProperty(kind='38', required=True),
        'images': SuperImageLocalStructuredProperty(Image, argument_format_upload=True, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            UploadImages(cfg={'target_field_path': '_products',
                              'key_path': 'input.product',
                              'add_config': {'images': 'input.images'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'product_instance_upload_images'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'product_instance': orm.SuperKeyProperty(kind='39', required=True),
        'images': SuperImageLocalStructuredProperty(Image, argument_format_upload=True, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            UploadImages(cfg={'target_field_path': '_products._instances',
                              'key_path': 'input.product_instance',
                              'add_config': {'images': 'input.images'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify()
            ]
          )
        ]
      ),
    orm.Action(
      # marketing.Delete() plugin deems this action to allways execute in taskqueue!
      key=orm.Action.build_key('35', 'delete'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Delete(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'search'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'orders': [{'field': 'created', 'operator': 'asc'}]},
          cfg={
            'search_by_keys': True,
            'search_arguments': {'kind': '35', 'options': {'limit': settings.SEARCH_PAGE}},
            'filters': {'name': orm.SuperStringProperty(),
                        'state': orm.SuperStringProperty(choices=['invited', 'accepted'])},
            'indexes': [{'orders': [('name', ['asc', 'desc'])]},
                        {'orders': [('created', ['asc', 'desc'])]},
                        {'orders': [('updated', ['asc', 'desc'])]},
                        {'filters': [('name', ['==', 'contains', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!=']), ('name', ['==', 'contains', '!='])],
                         'orders': [('name', ['asc', 'desc'])]}]
            }
          )
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Search(),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'lock'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'message': orm.SuperTextProperty(required=True)
        #'note': orm.SuperTextProperty()  # @todo Decide on this!
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_catalog.state': 'locked'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'publish'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'message': orm.SuperTextProperty(required=True)
        #'note': orm.SuperTextProperty()  # @todo Decide on this!
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_catalog.state': 'published'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'index', 'action_model': '35'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'discontinue'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'message': orm.SuperTextProperty(required=True)
        #'note': orm.SuperTextProperty()  # @todo Decide on this!
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_catalog.state': 'discontinued'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'unindex', 'action_model': '35'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'sudo'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'state': orm.SuperStringProperty(required=True, choices=['published', 'discontinued']),
        'index_state': orm.SuperStringProperty(choices=['index', 'unindex']),
        'message': orm.SuperTextProperty(required=True),
        'note': orm.SuperTextProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_catalog.state': 'input.state'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),  # 'index_state': 'input.index_state',  # @todo We embed this field on the fly, to indicate what administrator has chosen!
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_model': '35'},
                               {'action_id': 'input.index_state', 'key': '_catalog.key_urlsafe'})])  # @todo What happens if input.index_state is not supplied (e.g. None)?
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'log_message'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'message': orm.SuperTextProperty(required=True),
        'note': orm.SuperTextProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      # marketing.SearchWrite() plugin deems this action to allways execute in taskqueue!
      key=orm.Action.build_key('35', 'index'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogSearchDocumentWrite(cfg={'index': settings.CATALOG_INDEX})
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'sra': {'log_entity': False}}),  # @todo Perhaps entity should be logged in order to refresh updated field? - 'd': {'message': 'tmp.message'}
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      # marketing.SearchDelete() plugin deems this action to allways execute in taskqueue!
      key=orm.Action.build_key('35', 'unindex'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogSearchDocumentDelete(cfg={'index': settings.CATALOG_INDEX})
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'sra': {'log_entity': False}}),  # @todo Perhaps entity should be logged in order to refresh updated field? - 'd': {'message': 'tmp.message'}
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'cron'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogCronPublish(cfg={'page': 10}),
            CatalogCronDiscontinue(cfg={'page': 10}),
            CatalogCronDelete(cfg={'page': 10,
                                   'unpublished_life': settings.CATALOG_UNPUBLISHED_LIFE,
                                   'discontinued_life': settings.CATALOG_DISCONTINUED_LIFE}),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'catalog_duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'catalog_process_duplicate', 'action_model': '35'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'catalog_process_duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Duplicate(),
            Set(cfg={'s': {'_catalog.created': None,
                           '_catalog.state': 'unpublished'}}),
            Write(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'product_duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'product': orm.SuperKeyProperty(kind='38', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'product_process_duplicate', 'action_model': '35'},
                               {'key': '_catalog.key_urlsafe', 'product': 'input.product._urlsafe', 'read_arguments': 'input.read_arguments'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'product_process_duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'product': orm.SuperKeyProperty(kind='38', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Duplicate(cfg={'target_field_path': '_products',
                           'key_path': 'input.product'}),
            Write(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    # @todo 'indexes' will need optimization!
    orm.Action(
      key=orm.Action.build_key('35', 'public_search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'kind': '35', 'orders': [{'field': 'created', 'operator': 'desc'}]},
          cfg={
            'use_search_engine': True,
            'search_arguments': {'options': {'limit': settings.SEARCH_PAGE}},
            'filters': {'name': orm.SuperStringProperty(),
                        'state': orm.SuperStringProperty(choices=['invited', 'accepted'])},
            'orders': {'created': {'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}},
                       'updated': {'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}}},
            'indexes': [{'orders': [('name', ['asc', 'desc'])]},
                        {'orders': [('created', ['asc', 'desc'])]},
                        {'orders': [('updated', ['asc', 'desc'])]},
                        {'filters': [('name', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!=']), ('name', ['==', '!='])],
                         'orders': [('name', ['asc', 'desc'])]}]
            }
          )
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogSearch(cfg={'index': settings.CATALOG_INDEX}),
            #RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.total_matches': '_total_matches',
                           'output.entities_count': '_entities_count',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      )
    ]
  
  @property
  def _is_eligible(self):
    # @todo Here we implement the logic to validate if catalog publisher has funds to support catalog publishing!
    return True
