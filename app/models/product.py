# -*- coding: utf-8 -*-
'''
Created on May 12, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins import product


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
      FieldPermission('17', ['parent_record', 'name', 'complete_name', 'state'], False, True, 'True'),
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
            Context(),
            Prepare(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec(),
            product.CategoryUpdate(file_path=settings.PRODUCT_CATEGORY_DATA_FILE)
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('17', 'search'),
      arguments={  # @todo Add default filter to list active ones.
        'search': ndb.SuperSearchProperty(
          default={'filters': [{'field': 'state', 'value': 'indexable', 'operator': '=='}], 'order_by': {'field': 'name', 'operator': 'asc'}},
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
            Context(),
            Prepare(),
            RulePrepare(config={'skip_user_roles': True}),
            RuleExec(),
            Search(config={'page': settings.SEARCH_PAGE}),
            RulePrepare(config={'to': 'entities', 'skip_user_roles': True}),
            RuleRead(config={'path': 'entities'}),
            Set(config={'d': {'output.entities': 'entities',
                              'output.search_cursor': 'search_cursor',
                              'output.search_more': 'search_more'}})
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
    'images': ndb.SuperLocalStructuredProperty(Image, '10', repeated=True),
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
    'images': ndb.SuperLocalStructuredProperty(Image, '12', repeated=True),
    'contents': ndb.SuperLocalStructuredProperty(Content, '13', repeated=True),
    'variants': ndb.SuperLocalStructuredProperty(Variant, '14', repeated=True),
    'low_stock_quantity': ndb.SuperDecimalProperty('15', default='0.00')  # Notify store manager when quantity drops below X quantity.
    }
  
  _virtual_fields = {
    '_records': SuperLocalStructuredRecordProperty('38', repeated=True),
    '_instances': ndb.SuperLocalStructuredProperty(Instance, repeated=True),
    '_instance': ndb.SuperLocalStructuredProperty(Instance)
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
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents', 'variants', '_instances', '_records', '_instance'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents', 'variants', '_instances', '_records', '_instance'], False, None,
                      'context.entity.parent_entity.state != "unpublished"'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'images', 'contents', 'variants', '_instances', '_instance'], None, True,
                      'context.entity.parent_entity.state == "published" or context.entity.parent_entity.state == "discontinued"'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents', 'variants', '_instances', '_records', '_instance'], None, True,
                      'context.user._is_taskqueue or context.user._root_admin'),
      FieldPermission('38', ['images'], True, None,
                      'context.action.key_id_str == "process_images" and (context.user._is_taskqueue or context.user._root_admin)'),
      FieldPermission('38', ['_instance.images'], True, None,
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
            Context(),
            Prepare(config=[{'model': 'models.38', 'parent': 'input.parent', 'namespace': 'namespace',
                             'save': 'entities.38', 'copy': 'values.38'}]),
            RulePrepare(),
            RuleExec(),
            BlobURL(config={'bucket': settings.PRODUCT_TEMPLATE_BUCKET})
            Set(config={'d': {'output.entity': 'entities.38',
                              'output.upload_url': 'blob_url'}})
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
            Context(),
            Prepare(config=[{'model': 'models.38', 'parent': 'input.parent', 'namespace': 'namespace',
                             'save': 'entities.38', 'copy': 'values.38'}]),
            RulePrepare(),
            RuleExec(),
            Set(config={'d': {'values.38.product_category': 'input.product_category',
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
                              'values.38.low_stock_quantity': 'input.low_stock_quantity'}})
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(config={'paths': ['entities.38']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}}),
            CallbackNotify(),
            CallbackExec()
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
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}})
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
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(config={'d': {'values.38.product_category': 'input.product_category',
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
                              'values.38.low_stock_quantity': 'input.low_stock_quantity'}}),
            product.UpdateSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            product.WriteImages(),
            RecordWrite(config={'paths': ['entities.38']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'upload_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        'images': ndb.SuperLocalStructuredImageProperty(Image, repeated=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            product.UploadImagesSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(config={'paths': ['entities.38']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec(config=[('callback',
                                  {'action_id': 'process_images', 'action_model': '38'},
                                  {'key': 'entities.38.key_urlsafe'})])
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
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            product.ProcessImages(),
            RuleWrite(),
            Write(),
            product.WriteImages(),
            RecordWrite(config={'paths': ['entities.38']}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec()
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
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            product.TemplateReadInstances(read_all=True)
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            product.TemplateDelete(),
            product.DeleteImages(),
            Delete(),
            RecordWrite(config={'paths': ['entities.38']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec()
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
            Context(),
            Prepare(config=[{'model': 'models.38', 'parent': 'input.parent', 'namespace': 'namespace',
                             'save': 'entities.38', 'copy': 'values.38'}]),
            RulePrepare(),
            RuleExec(),
            Search(config={'page': settings.SEARCH_PAGE}),
            RulePrepare(config={'to': 'entities'}),
            RuleRead(config={'path': 'entities'}),
            Set(config={'d': {'output.entities': 'entities',
                              'output.search_cursor': 'search_cursor',
                              'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RecordRead(config={'page': settings.RECORDS_PAGE}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38',
                              'output.search_cursor': 'search_cursor',
                              'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'read_instances'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            product.TemplateReadInstances(page_size=settings.SEARCH_PAGE),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38',
                              'output.search_cursor': 'search_cursor',
                              'output.search_more': 'search_more'}})
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
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}}),
            CallbackNotify(),
            CallbackExec(config=[('callback',
                                  {'action_id': 'process_duplicate', 'action_model': '38'},
                                  {'key': 'entities.38.key_urlsafe'})])
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
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            product.TemplateReadInstances(read_all=True)
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            product.DuplicateWrite(),
            RecordWrite(),
            CallbackNotify(),
            CallbackExec()
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
            Context(),
            Read(config=[{'source': 'input.parent', 'save': 'entities.38', 'copy': 'values.38'}]),
            product.InstancePrepare(),
            RulePrepare(),
            RuleExec(),
            Set(config={'d': {'values.38._instance.variant_signature': 'input.variant_signature',
                              'values.38._instance.code': 'input.code',
                              'values.38._instance.description': 'input.description',
                              'values.38._instance.unit_price': 'input.unit_price',
                              'values.38._instance.availability': 'input.availability',
                              'values.38._instance.weight': 'input.weight',
                              'values.38._instance.weight_uom': 'input.weight_uom',
                              'values.38._instance.volume': 'input.volume',
                              'values.38._instance.volume_uom': 'input.volume_uom',
                              'values.38._instance.contents': 'input.contents',
                              'values.38._instance.low_stock_quantity': 'input.low_stock_quantity'}})
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(config={'paths': ['entities.38._instance']}),
            RecordWrite(config={'paths': ['entities.38._instance']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}}),
            CallbackNotify(),
            CallbackExec()
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
            Context(),
            Read(config=[{'source': 'input.parent', 'save': 'entities.38', 'copy': 'values.38'}]),
            product.InstanceRead(),
            RulePrepare(),
            RuleExec(),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}})
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
        'variant_signature': ndb.SuperJsonProperty(required=True),
        'parent': ndb.SuperKeyProperty(kind='38', required=True)
        #'key': ndb.SuperKeyProperty(kind='39', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(config=[{'source': 'input.parent', 'save': 'entities.38', 'copy': 'values.38'}]),
            product.InstanceRead(),
            RulePrepare(),
            RuleExec(),
            Set(config={'d': {'values.38._instance.code': 'input.code',
                              'values.38._instance.description': 'input.description',
                              'values.38._instance.unit_price': 'input.unit_price',
                              'values.38._instance.availability': 'input.availability',
                              'values.38._instance.weight': 'input.weight',
                              'values.38._instance.weight_uom': 'input.weight_uom',
                              'values.38._instance.volume': 'input.volume',
                              'values.38._instance.volume_uom': 'input.volume_uom',
                              'values.38._instance.contents': 'input.contents',
                              'values.38._instance.low_stock_quantity': 'input.low_stock_quantity'}}),
            product.InstanceUpdateSet(),
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(config={'paths': ['entities.38._instance']}),
            RecordWrite(config={'paths': ['entities.38._instance']}),
            product.InstanceWriteImages(),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'instance_upload_images'),
      arguments={
        #'key': ndb.SuperKeyProperty(kind='39', required=True),
        'variant_signature': ndb.SuperJsonProperty(required=True),
        'parent': ndb.SuperKeyProperty(kind='38', required=True),
        'images': ndb.SuperLocalStructuredImageProperty(Image, repeated=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(config=[{'source': 'input.parent', 'save': 'entities.38', 'copy': 'values.38'}]),
            product.InstanceRead(),
            RulePrepare(),
            RuleExec(),
            product.InstanceUploadImagesSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(config={'paths': ['entities.38._instance']}),
            RecordWrite(config={'paths': ['entities.38._instance']}),
            product.InstanceWriteImages(),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec(config=[('callback',
                                  {'action_id': 'instance_process_images', 'action_model': '38'},
                                  {'parent': 'entities.38.key_urlsafe',
                                   'variant_signature': 'entities.38._instance.variant_signature'})])
            ]
          )
        ]
      ),
     Action(
      key=Action.build_key('38', 'instance_process_images'),
      arguments={
        #'key': ndb.SuperKeyProperty(kind='39', required=True),
        'variant_signature': ndb.SuperJsonProperty(required=True),
        'parent': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(config=[{'source': 'input.parent', 'save': 'entities.38', 'copy': 'values.38'}]),
            product.InstanceRead(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            product.InstanceProcessImages(),
            RuleWrite(),
            Write(config={'paths': ['entities.38._instance']}),
            RecordWrite(config={'paths': ['entities.38._instance']}),
            product.InstanceWriteImages(),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('38', 'instance_delete'),
      arguments={
        #'key': ndb.SuperKeyProperty(kind='39', required=True),
        'variant_signature': ndb.SuperJsonProperty(required=True),
        'parent': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(config=[{'source': 'input.parent', 'save': 'entities.38', 'copy': 'values.38'}]),
            product.InstanceRead(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            product.InstanceDeleteImages(),
            RecordWrite(config={'paths': ['entities.38._instance']}),
            Delete(config={'paths': ['entities.38._instance']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.38'}}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      )
    ]
