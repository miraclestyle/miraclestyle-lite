# -*- coding: utf-8 -*-
'''
Created on May 12, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv.event import Action, PluginGroup
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.srv import log as ndb_log
from app.srv import blob as ndb_blob
from app.plugins import common, rule, log, callback, blob, product


class Content(ndb.BaseModel):
  
  _kind = 43
  
  title = ndb.SuperStringProperty('1', required=True, indexed=False)
  body = ndb.SuperTextProperty('2', required=True)


class Variant(ndb.BaseModel):
  
  _kind = 42
  
  name = ndb.SuperStringProperty('1', required=True, indexed=False)
  description = ndb.SuperTextProperty('2')
  options = ndb.SuperStringProperty('3', repeated=True, indexed=False)
  allow_custom_value = ndb.SuperBooleanProperty('4', required=True, indexed=False, default=False)


class Category(ndb.BaseModel):
  
  _kind = 17
  
  parent_record = ndb.SuperKeyProperty('1', kind='17', indexed=False)
  name = ndb.SuperStringProperty('2', required=True)
  complete_name = ndb.SuperTextProperty('3', required=True)
  state = ndb.SuperStringProperty('4', required=True, default='indexable')
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('17', [Action.build_key('17', 'update')], True, 'context.user._root_admin or context.user._is_taskqueue'),
      ActionPermission('17', [Action.build_key('17', 'search')], True, 'not context.user._is_guest'),
      FieldPermission('17', ['parent_record', 'name', 'complete_name', 'state'], False, None, 'True'),
      FieldPermission('17', ['parent_record', 'name', 'complete_name', 'state'], True, True,
                      'context.user._root_admin or context.user._is_taskqueue')
      ]
    )
  
  _actions = [  # @todo Do we need read action here?
    Action(
      key=Action.build_key('17', 'update'),
      arguments={},
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            product.CategoryUpdate(file_path=settings.PRODUCT_CATEGORY_DATA_FILE)
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('17', 'search'),
      arguments={  # @todo Add default filter to list active ones.
        'search': ndb.SuperSearchProperty(
          default={'filters': [{'field': 'state', 'value': 'searchable', 'operator': '=='}], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['IN'], 'type': ndb.SuperKeyProperty(kind='17', repeated=True)},
            'name': {'operators': ['==', '!=', 'contains'], 'type': ndb.SuperStringProperty(value_filters=[lambda p, s: s.capitalize()])},
            'state': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()}
            },
          indexes=[
            {'filter': ['key']},
            {'filter': ['state'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name', 'state'],
             'order_by': [['name', ['asc', 'desc']]]},
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
            }
          ),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Exec(),
            common.Search(page_size=settings.SEARCH_PAGE),
            rule.Prepare(skip_user_roles=True, strict=False),
            rule.Read(),
            common.Set(dynamic_values={'output.entities': 'entities',
                                       'output.search_cursor': 'search_cursor',
                                       'output.search_more': 'search_more'})
            ]
          )
        ]
      )
    ]


class Instance(ndb.BaseExpando):
  
  _kind = 39
  
  variant_signature = ndb.SuperJsonProperty('1', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'description': ndb.SuperTextProperty('2'),
    'unit_price': ndb.SuperDecimalProperty('3'),
    'availability': ndb.SuperStringProperty('4', default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
    'code': ndb.SuperStringProperty('5'),
    'weight': ndb.SuperDecimalProperty('6'),
    'weight_uom': ndb.SuperKeyProperty('7', kind='19'),
    'volume': ndb.SuperDecimalProperty('8'),
    'volume_uom': ndb.SuperKeyProperty('9', kind='19'),
    'images': ndb.SuperLocalStructuredProperty(ndb_blob.Image, '10', repeated=True),
    'contents': ndb.SuperLocalStructuredProperty(Content, '11', repeated=True),
    'low_stock_quantity': ndb.SuperDecimalProperty('12', default='0.00')
    }


class Template(ndb.BaseExpando):
  
  _kind = 38
  
  product_category = ndb.SuperKeyProperty('1', kind='17', required=True)
  name = ndb.SuperStringProperty('2', required=True)
  description = ndb.SuperTextProperty('3', required=True)  # Soft limit 64kb.
  product_uom = ndb.SuperKeyProperty('4', kind='19', required=True, indexed=False)
  unit_price = ndb.SuperDecimalProperty('5', required=True, indexed=False)
  availability = ndb.SuperStringProperty('6', required=True, indexed=False, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock'])
  code = ndb.SuperStringProperty('7', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'weight': ndb.SuperDecimalProperty('8'),
    'weight_uom': ndb.SuperKeyProperty('9', kind='19'),
    'volume': ndb.SuperDecimalProperty('10'),
    'volume_uom': ndb.SuperKeyProperty('11', kind='19'),
    'images': ndb.SuperLocalStructuredProperty(ndb_blob.Image, '12', repeated=True),
    'contents': ndb.SuperLocalStructuredProperty(Content, '13', repeated=True),
    'variants': ndb.SuperLocalStructuredProperty(Variant, '14', repeated=True),
    'low_stock_quantity': ndb.SuperDecimalProperty('15', default='0.00')  # Notify store manager when quantity drops below X quantity.
    }
  
  _virtual_fields = {
    '_instances': ndb.SuperLocalStructuredProperty(Instance, repeated=True),
    '_records': ndb_log.SuperLocalStructuredRecordProperty('38', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('38', [Action.build_key('38', 'prepare'),
                              Action.build_key('38', 'create'),
                              Action.build_key('38', 'read'),
                              Action.build_key('38', 'update'),
                              Action.build_key('38', 'upload_images'),
                              Action.build_key('38', 'search'),
                              Action.build_key('38', 'read_records'),
                              Action.build_key('38', 'read_instances'),
                              Action.build_key('38', 'duplicate'),
                              Action.build_key('38', 'instance_prepare'),
                              Action.build_key('38', 'instance_create'),
                              Action.build_key('38', 'instance_read'),
                              Action.build_key('38', 'instance_update'),
                              Action.build_key('38', 'instance_upload_images')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('38', [Action.build_key('38', 'create'),
                              Action.build_key('38', 'update'),
                              Action.build_key('38', 'upload_images'),
                              Action.build_key('38', 'duplicate'),
                              Action.build_key('38', 'instance_create'),
                              Action.build_key('38', 'instance_update'),
                              Action.build_key('38', 'instance_upload_images')], False, 'context.entity.parent_entity.state != "unpublished"'),
      ActionPermission('38', [Action.build_key('38', 'delete'),
                              Action.build_key('38', 'process_images'),
                              Action.build_key('38', 'process_duplicate'),
                              Action.build_key('38', 'instance_delete'),
                              Action.build_key('38', 'instance_process_images')], False, 'True'),
      ActionPermission('38', [Action.build_key('38', 'read'),
                              Action.build_key('38', 'read_instances'),
                              Action.build_key('38', 'instance_read')], True, 'context.entity.parent_entity.state == "published" or context.entity.parent_entity.state == "discontinued"'),
      ActionPermission('38', [Action.build_key('38', 'delete'),
                              Action.build_key('38', 'process_images'),
                              Action.build_key('38', 'process_duplicate'),
                              Action.build_key('38', 'instance_delete'),
                              Action.build_key('38', 'instance_process_images')], True, 'context.user._is_taskqueue'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents', 'variants', '_instances', '_records'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents', 'variants', '_instances', '_records'], False, None,
                      'context.entity.parent_entity.state != "unpublished"'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'images', 'contents', 'variants', '_instances'], None, True,
                      'context.entity.parent_entity.state == "published" or context.entity.parent_entity.state == "discontinued"'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents', 'variants', '_instances', '_records'], None, True,
                      'context.user._is_taskqueue or context.user._root_admin'),
      FieldPermission('38', ['images'], True, None,
                      'context.action.key_id_str == "process_images" and (context.user._is_taskqueue or context.user._root_admin)'),
      FieldPermission('39', ['variant_signature', 'description', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('39', ['variant_signature', 'description', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents'], False, None,
                      'context.entity.parent_entity.parent_entity.state != "unpublished"'),
      FieldPermission('39', ['variant_signature', 'description', 'unit_price', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'images', 'contents'], None, True,
                      'context.entity.parent_entity.parent_entity.state == "published" or context.entity.parent_entity.parent_entity.state == "discontinued"'),
      FieldPermission('39', ['variant_signature', 'description', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents'], None, True,
                      'context.user._is_taskqueue or context.user._root_admin'),
      FieldPermission('39', ['images'], True, None,
                      'context.action.key_id_str == "instance_process_images" and (context.user._is_taskqueue or context.user._root_admin)')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('38', 'prepare'),
      arguments={
        'parent': ndb.SuperKeyProperty(kind='35', required=True),
        'upload_url': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(parent_path='input.parent'),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            blob.URL(gs_bucket_name=settings.PRODUCT_TEMPLATE_BUCKET),
            common.Set(dynamic_values={'output.entity': 'entities.38'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'create'),
      arguments={
        'product_category': ndb.SuperKeyProperty(kind='17', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'description': ndb.SuperTextProperty(required=True),
        'product_uom': ndb.SuperKeyProperty(kind='19', required=True),
        'unit_price': ndb.SuperDecimalProperty(required=True),
        'availability': ndb.SuperStringProperty(required=True, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
        'code': ndb.SuperStringProperty(required=True),
        'weight': ndb.SuperDecimalProperty(required=True),
        'weight_uom': ndb.SuperKeyProperty(kind='19', required=True),
        'volume': ndb.SuperDecimalProperty(required=True),
        'volume_uom': ndb.SuperKeyProperty(kind='19', required=True),
        'variants': ndb.SuperLocalStructuredProperty(Variant, repeated=True),
        'contents': ndb.SuperLocalStructuredProperty(Content, repeated=True),
        'low_stock_quantity': ndb.SuperDecimalProperty(default='0.00'),
        'parent': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(parent_path='input.parent'),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            common.Set(dynamic_values={'values.38.product_category': 'input.product_category',
                                       'values.38.name': 'input.name',
                                       'values.38.description': 'input.description',
                                       'values.38.product_uom': 'input.product_uom',
                                       'values.38.unit_price': 'input.unit_price',
                                       'values.38.availability': 'input.availability',
                                       'values.38.code': 'input.code',
                                       'values.38.weight': 'input.weight',
                                       'values.38.weight_uom': 'input.weight_uom',
                                       'values.38.volume': 'input.volume',
                                       'values.38.volume_uom': 'input.volume_uom',
                                       'values.38.variants': 'input.variants',
                                       'values.38.contents': 'input.contents',
                                       'values.38.low_stock_quantity': 'input.low_stock_quantity'})
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            log.Entity(),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.38'}),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.38'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'update'),
      arguments={
        'variants': ndb.SuperLocalStructuredProperty(Variant, repeated=True),
        'contents': ndb.SuperLocalStructuredProperty(Content, repeated=True),
        'sort_images': ndb.SuperStringProperty(repeated=True),
        'product_category': ndb.SuperKeyProperty(kind='17', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'description': ndb.SuperTextProperty(required=True),
        'product_uom': ndb.SuperKeyProperty(kind='19', required=True),
        'unit_price': ndb.SuperDecimalProperty(required=True),
        'availability': ndb.SuperStringProperty(required=True, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
        'code': ndb.SuperStringProperty(required=True),
        'weight': ndb.SuperDecimalProperty(required=True),
        'weight_uom': ndb.SuperKeyProperty(kind='19', required=True),
        'volume': ndb.SuperDecimalProperty(required=True),
        'volume_uom': ndb.SuperKeyProperty(kind='19', required=True),
        'low_stock_quantity': ndb.SuperDecimalProperty(default='0.00'),
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            common.Set(dynamic_values={'values.38.product_category': 'input.product_category',
                                       'values.38.name': 'input.name',
                                       'values.38.description': 'input.description',
                                       'values.38.product_uom': 'input.product_uom',
                                       'values.38.unit_price': 'input.unit_price',
                                       'values.38.availability': 'input.availability',
                                       'values.38.code': 'input.code',
                                       'values.38.weight': 'input.weight',
                                       'values.38.weight_uom': 'input.weight_uom',
                                       'values.38.volume': 'input.volume',
                                       'values.38.volume_uom': 'input.volume_uom',
                                       'values.38.low_stock_quantity': 'input.low_stock_quantity',
                                       'values.38.variants': 'input.variants',
                                       'values.38.contents': 'input.contents'}),
            product.UpdateSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            product.WriteImages(),
            log.Entity(),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.38'}),
            blob.Update(),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'upload_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        'images': ndb.SuperLocalStructuredImageProperty(ndb_blob.Image, repeated=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            product.UploadImagesSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(),
            common.Write(),
            product.WriteImages(),
            log.Entity(),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.38'}),
            blob.Update(),
            callback.Notify(),
            callback.Payload(queue='callback',
                             static_data={'action_id': 'process_images', 'action_model': '38'},
                             dynamic_data={'key': 'entities.38.key_urlsafe'}),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'process_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            product.ProcessImages(),
            rule.Write(),
            common.Write(),
            product.WriteImages(),
            log.Entity(),
            log.Write(),
            blob.Update(),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            product.TemplateReadInstances(read_all=True)
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            product.TemplateDelete(),
            product.DeleteImages(),
            common.Delete(),
            log.Entity(),
            log.Write(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.38'}),
            blob.Update(),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'search'),
      arguments={
        'parent': ndb.SuperKeyProperty(kind='35', required=True),  # This argument is used for access control.
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'desc'}},
          filters={
            'ancestor': {'operators': ['=='], 'type': ndb.SuperKeyProperty(kind='35')},
            'product_category': {'operators': ['==', '!='], 'type': ndb.SuperKeyProperty(kind='17')}
            },
          indexes=[  # We'll see if we are going to allow searches by name.
            {'filter': ['ancestor'],
             'order_by': [['name', ['asc', 'desc']]]},
            #{'filter': ['name'],
            # 'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['ancestor', 'product_category'],
             'order_by': [['name', ['asc', 'desc']]]},
            #{'filter': ['name', 'product_category'],
            # 'order_by': [['name', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
            }
          ),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(parent_path='input.parent'),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            common.Search(page_size=settings.SEARCH_PAGE),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Read(),
            common.Set(dynamic_values={'output.entities': 'entities',
                                       'output.search_cursor': 'search_cursor',
                                       'output.search_more': 'search_more'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            log.Read(page_size=settings.RECORDS_PAGE),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.38',
                                       'output.log_read_cursor': 'log_read_cursor',
                                       'output.log_read_more': 'log_read_more'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'read_instances'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        'instances_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            product.TemplateReadInstances(page_size=settings.SEARCH_PAGE),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.38',
                                       'output.instances_cursor': 'tmp.instances_cursor',
                                       'output.instances_more': 'tmp.instances_more'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'duplicate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            rule.Read(),
            common.Set(dynamic_values={'output.entity': 'entities.38'}),
            callback.Notify(),
            callback.Payload(queue='callback',
                             static_data={'action_id': 'process_duplicate', 'action_model': '38'},
                             dynamic_data={'key': 'entities.38.key_urlsafe'}),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'process_duplicate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            rule.Prepare(skip_user_roles=False, strict=False),
            rule.Exec(),
            product.TemplateReadInstances(read_all=True)
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            product.DuplicateWrite(),
            log.Write(),
            callback.Notify(),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'instance_prepare'),
      arguments={
        'parent': ndb.SuperKeyProperty(kind='38', required=True),
        'upload_url': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(kind_id='38', parent_path='input.parent.entity.key_parent'),
            common.Prepare(kind_id='39', parent_path='input.parent'),
            rule.Prepare(prepare_entities=['38', '39'], skip_user_roles=False, strict=False),
            rule.Exec(),
            blob.URL(gs_bucket_name=settings.PRODUCT_INSTANCE_BUCKET),
            common.Set(dynamic_values={'output.entity': 'entities.39'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'instance_create'),
      arguments={
        'variant_signature': ndb.SuperJsonProperty(required=True),
        'code': ndb.SuperStringProperty(required=True),
        'description': ndb.SuperTextProperty(required=True),
        'unit_price': ndb.SuperDecimalProperty(required=True),
        'availability': ndb.SuperStringProperty(required=True, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
        'weight': ndb.SuperDecimalProperty(required=True),
        'weight_uom': ndb.SuperKeyProperty(kind='19', required=True),
        'volume': ndb.SuperDecimalProperty(required=True),
        'volume_uom': ndb.SuperKeyProperty(kind='19', required=True),
        'contents': ndb.SuperLocalStructuredProperty(Content, repeated=True),
        'low_stock_quantity': ndb.SuperDecimalProperty(default='0.00'),
        'parent': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(kind_id='38', parent_path='input.parent.entity.key_parent'),
            product.InstancePrepare(),
            rule.Prepare(prepare_entities=['38', '39'], skip_user_roles=False, strict=False),
            rule.Exec(),
            common.Set(dynamic_values={'values.39.variant_signature': 'input.variant_signature',
                                       'values.39.code': 'input.code',
                                       'values.39.description': 'input.description',
                                       'values.39.unit_price': 'input.unit_price',
                                       'values.39.availability': 'input.availability',
                                       'values.39.weight': 'input.weight',
                                       'values.39.weight_uom': 'input.weight_uom',
                                       'values.39.volume': 'input.volume',
                                       'values.39.volume_uom': 'input.volume_uom',
                                       'values.39.contents': 'input.contents',
                                       'values.39.low_stock_quantity': 'input.low_stock_quantity'})
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(write_entities=['39']),
            common.Write(write_entities=['39']),
            log.Entity(log_entities=['39']),
            log.Write(),
            rule.Read(read_entities=['39']),
            common.Set(dynamic_values={'output.entity': 'entities.39'}),
            callback.Notify(dynamic_data={'caller_entity': 'entities.39.key_urlsafe'}),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'instance_read'),
      arguments={
        'variant_signature': ndb.SuperJsonProperty(required=True),
        'parent': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Prepare(kind_id='38', parent_path='input.parent.entity.key_parent'),
            product.InstanceRead(),
            rule.Prepare(prepare_entities=['38', '39'], skip_user_roles=False, strict=False),
            rule.Exec(),
            rule.Read(read_entities=['39']),
            common.Set(dynamic_values={'output.entity': 'entities.39'})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'instance_update'),
      arguments={
        'contents': ndb.SuperLocalStructuredProperty(Content, repeated=True),
        'sort_images': ndb.SuperStringProperty(repeated=True),
        'code': ndb.SuperStringProperty(required=True),
        'description': ndb.SuperTextProperty(required=True),
        'unit_price': ndb.SuperDecimalProperty(required=True),
        'availability': ndb.SuperStringProperty(required=True, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
        'weight': ndb.SuperDecimalProperty(required=True),
        'weight_uom': ndb.SuperKeyProperty(kind='19', required=True),
        'volume': ndb.SuperDecimalProperty(required=True),
        'volume_uom': ndb.SuperKeyProperty(kind='19', required=True),
        'low_stock_quantity': ndb.SuperDecimalProperty(default='0.00'),
        'key': ndb.SuperKeyProperty(kind='39', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(read_entities={'39': 'input.key'}),
            common.Prepare(kind_id='38', parent_path='entities.39.parent_entity.key_parent'),
            rule.Prepare(prepare_entities=['38', '39'], skip_user_roles=False, strict=False),
            rule.Exec(),
            common.Set(dynamic_values={'values.39.code': 'input.code',
                                       'values.39.description': 'input.description',
                                       'values.39.unit_price': 'input.unit_price',
                                       'values.39.availability': 'input.availability',
                                       'values.39.weight': 'input.weight',
                                       'values.39.weight_uom': 'input.weight_uom',
                                       'values.39.volume': 'input.volume',
                                       'values.39.volume_uom': 'input.volume_uom',
                                       'values.39.low_stock_quantity': 'input.low_stock_quantity',
                                       'values.39.contents': 'input.contents'}),
            product.UpdateSet(kind_id='39')
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(write_entities=['39']),
            common.Write(write_entities=['39']),
            product.WriteImages(kind_id='39'),
            log.Entity(log_entities=['39']),
            log.Write(),
            rule.Read(read_entities=['39']),
            common.Set(dynamic_values={'output.entity': 'entities.39'}),
            blob.Update(),
            callback.Notify(dynamic_data={'caller_entity': 'entities.39.key_urlsafe'}),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'instance_upload_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='39', required=True),
        'images': ndb.SuperLocalStructuredImageProperty(ndb_blob.Image, repeated=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(read_entities={'39': 'input.key'}),
            common.Prepare(kind_id='38', parent_path='entities.39.parent_entity.key_parent'),
            rule.Prepare(prepare_entities=['38', '39'], skip_user_roles=False, strict=False),
            rule.Exec(),
            product.UploadImagesSet(kind_id='39')
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            rule.Write(write_entities=['39']),
            common.Write(write_entities=['39']),
            product.WriteImages(kind='39'),
            log.Entity(log_entities=['39']),
            log.Write(),
            rule.Read(read_entities=['39']),
            common.Set(dynamic_values={'output.entity': 'entities.39'}),
            blob.Update(),
            callback.Notify(dynamic_data={'caller_entity': 'entities.39.key_urlsafe'}),
            callback.Payload(queue='callback',
                             static_data={'action_id': 'process_images', 'action_model': '39'},
                             dynamic_data={'key': 'entities.39.key_urlsafe'}),
            callback.Exec()
            ]
          )
        ]
      ),
     Action(
      key=Action.build_key('38', 'instance_process_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='39', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(read_entities={'39': 'input.key'}),
            common.Prepare(kind_id='38', parent_path='entities.39.parent_entity.key_parent'),
            rule.Prepare(prepare_entities=['38', '39'], skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            product.ProcessImages(kind_id='39'),
            rule.Write(write_entities=['39']),
            common.Write(write_entities=['39']),
            product.WriteImages(kind_id='39'),
            log.Entity(log_entities=['39']),
            log.Write(),
            blob.Update(),
            callback.Notify(dynamic_data={'caller_entity': 'entities.39.key_urlsafe'}),
            callback.Exec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'instance_delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='39', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            common.Context(),
            common.Read(),
            common.Read(read_entities={'39': 'input.key'}),
            common.Prepare(kind_id='38', parent_path='entities.39.parent_entity.key_parent'),
            rule.Prepare(prepare_entities=['38', '39'], skip_user_roles=False, strict=False),
            rule.Exec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            product.DeleteImages(kind_id='39'),
            common.Delete(delete_entities=['39']),
            log.Entity(log_entities=['39']),
            log.Write(),
            rule.Read(read_entities=['39']),
            common.Set(dynamic_values={'output.entity': 'entities.39'}),
            blob.Update(),
            callback.Notify(dynamic_data={'caller_entity': 'entities.39.key_urlsafe'}),
            callback.Exec()
            ]
          )
        ]
      )
    ]
