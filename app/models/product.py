# -*- coding: utf-8 -*-
'''
Created on May 12, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib

from app import orm, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.product import *


class Content(orm.BaseModel):
  
  _kind = 43
  
  title = orm.SuperStringProperty('1', required=True, indexed=False)
  body = orm.SuperTextProperty('2', required=True)


class Variant(orm.BaseModel):
  
  _kind = 42
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  description = orm.SuperTextProperty('2')
  options = orm.SuperStringProperty('3', repeated=True, indexed=False)
  allow_custom_value = orm.SuperBooleanProperty('4', required=True, indexed=False, default=False)


class Category(orm.BaseModel):
  
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
  
  _actions = [  # @todo Do we need read action here?
    orm.Action(
      key=orm.Action.build_key('17', 'update'),  # @todo In order to warrant idempotency, this action has to produce custom key for each commited entry.
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            CategoryUpdateWrite(cfg={'file': settings.PRODUCT_CATEGORY_DATA_FILE})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('17', 'search'),
      arguments={  # @todo Add default filter to list active ones.
        'search': orm.SuperSearchProperty(
          default={'filters': [{'field': 'state', 'value': 'indexable', 'operator': '=='}], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['IN'], 'type': orm.SuperKeyProperty(kind='17', repeated=True)},
            'name': {'operators': ['==', '!=', 'contains'], 'type': orm.SuperStringProperty(value_filters=[lambda p, s: s.capitalize()])},
            'state': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()}
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
        'cursor': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Search(cfg={'page': settings.SEARCH_PAGE}),
            RulePrepare(cfg={'path': '_entities', 'skip_user_roles': True}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      )
    ]


class Instance(orm.BaseExpando):
  
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
    'images': orm.SuperLocalStructuredProperty(Image, '10', repeated=True),
    'contents': orm.SuperLocalStructuredProperty(Content, '11', repeated=True),
    'low_stock_quantity': orm.SuperDecimalProperty('12', default='0.00')
    }
  
  def prepare_key(self, **kwargs):
    variant_signature = self.variant_signature
    key_id = hashlib.md5(json.dumps(variant_signature)).hexdigest()
    product_instance_key = self.build_key(key_id, parent=kwargs.get('parent'))
    return product_instance_key


class Template(orm.BaseExpando):
  
  _kind = 38
  
  product_category = orm.SuperKeyProperty('1', kind='17', required=True)
  name = orm.SuperStringProperty('2', required=True)
  description = orm.SuperTextProperty('3', required=True)  # Soft limit 64kb.
  product_uom = orm.SuperKeyProperty('4', kind='19', required=True, indexed=False)
  unit_price = orm.SuperDecimalProperty('5', required=True, indexed=False)
  availability = orm.SuperStringProperty('6', required=True, indexed=False, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock'])
  code = orm.SuperStringProperty('7', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'weight': orm.SuperDecimalProperty('8'),
    'weight_uom': orm.SuperKeyProperty('9', kind='19'),
    'volume': orm.SuperDecimalProperty('10'),
    'volume_uom': orm.SuperKeyProperty('11', kind='19'),
    'images': orm.SuperLocalStructuredProperty(Image, '12', repeated=True),
    'contents': orm.SuperLocalStructuredProperty(Content, '13', repeated=True),
    'variants': orm.SuperLocalStructuredProperty(Variant, '14', repeated=True),
    'low_stock_quantity': orm.SuperDecimalProperty('15', default='0.00')  # Notify store manager when quantity drops below X quantity.
    }
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('38'),
    '_instances': orm.SuperLocalStructuredProperty(Instance, repeated=True)  # @todo Implement Storage PRoperty here!
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('38', [orm.Action.build_key('38', 'prepare'),
                                  orm.Action.build_key('38', 'create'),
                                  orm.Action.build_key('38', 'read'),
                                  orm.Action.build_key('38', 'update'),
                                  orm.Action.build_key('38', 'upload_images'),
                                  orm.Action.build_key('38', 'search'),
                                  orm.Action.build_key('38', 'duplicate')], False, 'entity.namespace_entity.state != "active"'),
      orm.ActionPermission('38', [orm.Action.build_key('38', 'create'),
                                  orm.Action.build_key('38', 'update'),
                                  orm.Action.build_key('38', 'upload_images'),
                                  orm.Action.build_key('38', 'duplicate')], False, 'entity.parent_entity.state != "unpublished"'),
      orm.ActionPermission('38', [orm.Action.build_key('38', 'delete'),
                                  orm.Action.build_key('38', 'process_images'),
                                  orm.Action.build_key('38', 'process_duplicate')], False, 'True'),
      orm.ActionPermission('38', [orm.Action.build_key('38', 'read')], True, 'entity.parent_entity.state == "published" or entity.parent_entity.state == "discontinued"'),
      orm.ActionPermission('38', [orm.Action.build_key('38', 'delete'),
                                  orm.Action.build_key('38', 'process_images'),
                                  orm.Action.build_key('38', 'process_duplicate')], True, 'user._is_taskqueue'),
      orm.FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                                 'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents', 'variants', '_instances', '_records', '_instance'], False, False,
                          'entity.namespace_entity.state != "active"'),
      orm.FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                                 'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents', 'variants', '_instances', '_records', '_instance'], False, None,
                          'entity.parent_entity.state != "unpublished"'),
      orm.FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                                 'weight', 'weight_uom', 'volume', 'volume_uom', 'images', 'contents', 'variants', '_instances', '_instance'], None, True,
                          'entity.parent_entity.state == "published" or entity.parent_entity.state == "discontinued"'),
      orm.FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                                 'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', 'images', 'contents', 'variants', '_instances', '_records', '_instance'], None, True,
                          'user._is_taskqueue or user._root_admin'),
      orm.FieldPermission('38', ['images'], True, None,
                          'action.key_id_str == "process_images" and (user._is_taskqueue or user._root_admin)'),
      orm.FieldPermission('38', ['_instance.images'], True, None,
                          'action.key_id_str == "instance_process_images" and (user._is_taskqueue or user._root_admin)')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('38', 'prepare'),
      arguments={
        'parent': orm.SuperKeyProperty(kind='35', required=True),
        'upload_url': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(cfg={'parent': 'input.parent'}),
            RulePrepare(),
            RuleExec(),
            BlobURL(cfg={'bucket': settings.PRODUCT_TEMPLATE_BUCKET}),
            Set(cfg={'d': {'output.entity': '_template',
                           'output.upload_url': '_blob_url'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('38', 'create'),
      arguments={
        'product_category': orm.SuperKeyProperty(kind='17', required=True),
        'name': orm.SuperStringProperty(required=True),
        'description': orm.SuperTextProperty(required=True),
        'product_uom': orm.SuperKeyProperty(kind='19', required=True),
        'unit_price': orm.SuperDecimalProperty(required=True),
        'availability': orm.SuperStringProperty(required=True, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
        'code': orm.SuperStringProperty(required=True),
        'weight': orm.SuperDecimalProperty(required=True),
        'weight_uom': orm.SuperKeyProperty(kind='19', required=True),
        'volume': orm.SuperDecimalProperty(required=True),
        'volume_uom': orm.SuperKeyProperty(kind='19', required=True),
        'variants': orm.SuperLocalStructuredProperty(Variant, repeated=True),
        'contents': orm.SuperLocalStructuredProperty(Content, repeated=True),
        'low_stock_quantity': orm.SuperDecimalProperty(default='0.00'),
        'parent': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(cfg={'parent': 'input.parent'}),
            Set(cfg={'d': {'_template.product_category': 'input.product_category',
                           '_template.name': 'input.name',
                           '_template.description': 'input.description',
                           '_template.product_uom': 'input.product_uom',
                           '_template.unit_price': 'input.unit_price',
                           '_template.availability': 'input.availability',
                           '_template.code': 'input.code',
                           '_template.weight': 'input.weight',
                           '_template.weight_uom': 'input.weight_uom',
                           '_template.volume': 'input.volume',
                           '_template.volume_uom': 'input.volume_uom',
                           '_template.variants': 'input.variants',
                           '_template.contents': 'input.contents',
                           '_template.low_stock_quantity': 'input.low_stock_quantity'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_template'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('38', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='38', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_template'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('38', 'update'),
      arguments={
        'variants': orm.SuperLocalStructuredProperty(Variant, repeated=True),
        'contents': orm.SuperLocalStructuredProperty(Content, repeated=True),
        'sort_images': orm.SuperStringProperty(repeated=True),
        'product_category': orm.SuperKeyProperty(kind='17', required=True),
        'name': orm.SuperStringProperty(required=True),
        'description': orm.SuperTextProperty(required=True),
        'product_uom': orm.SuperKeyProperty(kind='19', required=True),
        'unit_price': orm.SuperDecimalProperty(required=True),
        'availability': orm.SuperStringProperty(required=True, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
        'code': orm.SuperStringProperty(required=True),
        'weight': orm.SuperDecimalProperty(required=True),
        'weight_uom': orm.SuperKeyProperty(kind='19', required=True),
        'volume': orm.SuperDecimalProperty(required=True),
        'volume_uom': orm.SuperKeyProperty(kind='19', required=True),
        'low_stock_quantity': orm.SuperDecimalProperty(default='0.00'),
        'key': orm.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_template.product_category': 'input.product_category',
                           '_template.name': 'input.name',
                           '_template.description': 'input.description',
                           '_template.product_uom': 'input.product_uom',
                           '_template.unit_price': 'input.unit_price',
                           '_template.availability': 'input.availability',
                           '_template.code': 'input.code',
                           '_template.weight': 'input.weight',
                           '_template.weight_uom': 'input.weight_uom',
                           '_template.volume': 'input.volume',
                           '_template.volume_uom': 'input.volume_uom',
                           '_template.variants': 'input.variants',
                           '_template.contents': 'input.contents',
                           '_template.low_stock_quantity': 'input.low_stock_quantity'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_template'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('38', 'upload_images'),  # @todo Do we implement image uploading into update action!?
      arguments={
        'key': orm.SuperKeyProperty(kind='38', required=True),
        'images': orm.SuperLocalStructuredImageProperty(Image, repeated=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_template.images': 'input.images'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_template'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'process_images', 'action_model': '38'},
                               {'key': '_template.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('38', 'process_images'),  # @todo Implement Image Processing here!
      arguments={
        'key': orm.SuperKeyProperty(kind='38', required=True)
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
            Write(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('38', 'delete'),
      arguments={
        'key': orm.SuperKeyProperty(kind='38', required=True)
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
            Set(cfg={'d': {'output.entity': '_template'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('38', 'search'),
      arguments={
        'parent': orm.SuperKeyProperty(kind='35', required=True),  # This argument is used for access control.
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'desc'}},
          filters={
            'ancestor': {'operators': ['=='], 'type': orm.SuperKeyProperty(kind='35')},
            'product_category': {'operators': ['==', '!='], 'type': orm.SuperKeyProperty(kind='17')}
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
        'cursor': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(cfg={'parent': 'input.parent'}),
            RulePrepare(),
            RuleExec(),
            Search(cfg={'page': settings.SEARCH_PAGE}),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('38', 'duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='38', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_template'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'process_duplicate', 'action_model': '38'},
                               {'key': '_template.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('38', 'process_duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='38', required=True)
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
            Duplicate(),  # @todo Not sure about this!!
            Write(),  # @todo Not sure about this!!
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      )
    ]
