# -*- coding: utf-8 -*-
'''
Created on May 12, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv.event import Action
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


class Image(ndb_blob.Image):
  
  _kind = 76
  
  def get_output(self):
    dic = super(Image, self).get_output()
    dic['_image_240'] = self.get_serving_url(240)
    dic['_image_600'] = self.get_serving_url(600)
    return dic


class Images(ndb.BaseModel):
  
  _kind = 73
  
  images = ndb.SuperLocalStructuredProperty(Image, '1', repeated=True)  # Soft limit 100 instances.


class Variants(ndb.BaseModel):
  
  _kind = 74
  
  variants = ndb.SuperLocalStructuredProperty(Variant, '1', repeated=True)  # Soft limit 100 instances.


class Contents(ndb.BaseModel):
  
  _kind = 75
  
  contents = ndb.SuperLocalStructuredProperty(Content, '1', repeated=True)  # Soft limit 100 instances.


class Category(ndb.BaseModel):
  
  _kind = 17
  
  parent_record = ndb.SuperKeyProperty('1', kind='17', indexed=False)
  name = ndb.SuperStringProperty('2', required=True)
  complete_name = ndb.SuperTextProperty('3')
  state = ndb.SuperStringProperty('4', required=True, default='searchable')
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('17', [Action.build_key('17', 'update'),
                             Action.build_key('17', 'search')], True, 'context.user._root_admin or context.user._is_taskqueue'),
      FieldPermission('17', ['parent_record', 'name', 'complete_name', 'state'], False, None, 'True'),
      FieldPermission('17', ['parent_record', 'name', 'complete_name', 'state'], True, True,
                      'context.user._root_admin or context.user._is_taskqueue')
      ]
    )
  
  _actions = [  # @todo Do we need read action here?
    Action(
      key=Action.build_key('17', 'update'),
      arguments={},
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        product.CategoryUpdate(file_path=settings.PRODUCT_CATEGORY_DATA_FILE)
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
      _plugins=[
        common.Context(),
        common.Prepare(),
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
    'low_stock_quantity': ndb.SuperDecimalProperty('10', default='0.00')
    }
  
  _virtual_fields = {
    '_images': ndb.SuperLocalStructuredProperty(Image, repeated=True),
    '_contents': ndb.SuperLocalStructuredProperty(Content, repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('39', [Action.build_key('39', 'prepare'),
                              Action.build_key('39', 'create'),
                              Action.build_key('39', 'read'),
                              Action.build_key('39', 'update'),
                              Action.build_key('39', 'upload_images'),
                              Action.build_key('39', 'process_images'),
                              Action.build_key('39', 'delete')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('39', [Action.build_key('39', 'create'),
                              Action.build_key('39', 'update'),
                              Action.build_key('39', 'upload_images')], False, 'context.entity.parent_entity.parent_entity.state != "unpublished"'),
      ActionPermission('39', [Action.build_key('39', 'delete'),
                              Action.build_key('39', 'process_images')], False, 'True'),
      ActionPermission('39', [Action.build_key('39', 'read')], True, 'context.entity.parent_entity.parent_entity.state == "published" or context.entity.parent_entity.parent_entity.state == "discontinued"'),
      ActionPermission('39', [Action.build_key('39', 'delete'),
                              Action.build_key('39', 'process_images')], True, 'context.user._is_taskqueue'),
      FieldPermission('39', ['variant_signature', 'description', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', '_images', '_contents'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('39', ['variant_signature', 'description', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', '_images', '_contents'], False, None,
                      'context.entity.parent_entity.parent_entity.state != "unpublished"'),
      FieldPermission('39', ['variant_signature', 'description', 'unit_price', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', '_images', '_contents'], None, True,
                      'context.entity.parent_entity.parent_entity.state == "published" or context.entity.parent_entity.parent_entity.state == "discontinued"'),
      FieldPermission('39', ['variant_signature', 'description', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', '_images', '_contents'], None, True,
                      'context.user._is_taskqueue or context.user._root_admin')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('39', 'prepare'),
      arguments={
        'parent': ndb.SuperKeyProperty(kind='38', required=True),
        'upload_url': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        product.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        blob.URL(gs_bucket_name=settings.PRODUCT_INSTANCE_BUCKET),
        common.Set(dynamic_values={'output.entity': 'entities.39'})
        ]
      ),
    Action(
      key=Action.build_key('39', 'create'),
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
        'low_stock_quantity': ndb.SuperDecimalProperty(default='0.00'),
        'parent': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugins=[
        common.Context(),
        product.InstancePrepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
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
                                   'values.39.low_stock_quantity': 'input.low_stock_quantity'}),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.39'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.39.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('39', 'read'),
      arguments={
        'variant_signature': ndb.SuperJsonProperty(required=True),
        'parent': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugins=[
        common.Context(),
        product.InstanceRead(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.39'})
        ]
      ),
    Action(
      key=Action.build_key('39', 'update'),
      arguments={
        '_contents': ndb.SuperLocalStructuredProperty(Content, repeated=True),
        '_images': ndb.SuperLocalStructuredProperty(Image, repeated=True),
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
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
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
                                   'values.39._images': 'input._images',
                                   'values.39._contents': 'input._contents'}),
        product.UpdateSet(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        product.WriteImages(transactional=True),
        product.WriteContents(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.39'}),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.39.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('39', 'upload_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='39', required=True),
        '_images': ndb.SuperLocalStructuredImageProperty(Image, repeated=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        product.UploadImagesSet(),
        rule.Write(transactional=True),
        product.WriteImages(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.39'}),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.39.key_urlsafe'}),
        callback.Payload(transactional=True, queue='callback',
                         static_data={'action_id': 'process_images', 'action_model': '39'},
                         dynamic_data={'key': 'entities.39.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
     Action(
      key=Action.build_key('39', 'process_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='39', required=True),
        'caller_user': ndb.SuperKeyProperty(kind='0', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        product.ProcessImages(transactional=True),
        rule.Write(transactional=True),
        product.WriteImages(transactional=True),
        log.Write(transactional=True),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.39.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('39', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='39', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        product.DeleteImages(transactional=True),
        product.DeleteContents(transactional=True),
        common.Delete(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.39'}),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.39.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      )
    ]


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
    'low_stock_quantity': ndb.SuperDecimalProperty('12', default='0.00')  # Notify store manager when quantity drops below X quantity.
    }
  
  _virtual_fields = {
    '_images': ndb.SuperLocalStructuredProperty(Image, repeated=True),
    '_contents': ndb.SuperLocalStructuredProperty(Content, repeated=True),
    '_variants': ndb.SuperLocalStructuredProperty(Variant, repeated=True),
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
                              Action.build_key('38', 'process_images'),
                              Action.build_key('38', 'delete'),
                              Action.build_key('38', 'search'),
                              Action.build_key('38', 'read_records'),
                              Action.build_key('38', 'read_instances'),
                              Action.build_key('38', 'duplicate')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('38', [Action.build_key('38', 'create'),
                              Action.build_key('38', 'update'),
                              Action.build_key('38', 'upload_images'),
                              Action.build_key('38', 'duplicate')], False, 'context.entity.parent_entity.state != "unpublished"'),
      ActionPermission('38', [Action.build_key('38', 'delete'),
                              Action.build_key('38', 'process_images')], False, 'True'),
      ActionPermission('38', [Action.build_key('38', 'read'),
                              Action.build_key('38', 'read_instances')], True, 'context.entity.parent_entity.state == "published" or context.entity.parent_entity.state == "discontinued"'),
      ActionPermission('38', [Action.build_key('38', 'delete'),
                              Action.build_key('38', 'process_images')], True, 'context.user._is_taskqueue'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', '_images', '_contents', '_variants', '_instances', '_records'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', '_images', '_contents', '_variants', '_instances', '_records'], False, None,
                      'context.entity.parent_entity.state != "unpublished"'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', '_images', '_contents', '_variants', '_instances'], None, True,
                      'context.entity.parent_entity.state == "published" or context.entity.parent_entity.state == "discontinued"'),
      FieldPermission('38', ['product_category', 'name', 'description', 'product_uom', 'unit_price', 'availability', 'code',
                             'weight', 'weight_uom', 'volume', 'volume_uom', 'low_stock_quantity', '_images', '_contents', '_variants', '_instances', '_records'], None, True,
                      'context.user._is_taskqueue or context.user._root_admin')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('38', 'prepare'),
      arguments={
        'parent': ndb.SuperKeyProperty(kind='35', required=True),
        'upload_url': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        product.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        blob.URL(gs_bucket_name=settings.PRODUCT_TEMPLATE_BUCKET),
        common.Set(dynamic_values={'output.entity': 'entities.38'})
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
        'low_stock_quantity': ndb.SuperDecimalProperty(default='0.00'),
        'parent': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugins=[
        common.Context(),
        product.Prepare(),
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
                                   'values.38.low_stock_quantity': 'input.low_stock_quantity'}),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.38'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.38.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.38'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'update'),
      arguments={
        '_variants': ndb.SuperLocalStructuredProperty(Variant, repeated=True),
        '_contents': ndb.SuperLocalStructuredProperty(Content, repeated=True),
        '_images': ndb.SuperLocalStructuredProperty(Image, repeated=True),
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
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
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
                                   'values.38._images': 'input._images',
                                   'values.38._variants': 'input._variants',
                                   'values.38._contents': 'input._contents'}),
        product.UpdateSet(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        product.WriteImages(transactional=True),
        product.WriteVariants(transactional=True),
        product.WriteContents(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.38'}),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.38.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'upload_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        '_images': ndb.SuperLocalStructuredImageProperty(Image, repeated=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        product.UploadImagesSet(),
        rule.Write(transactional=True),
        product.WriteImages(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.38'}),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.38.key_urlsafe'}),
        callback.Payload(transactional=True, queue='callback',
                         static_data={'action_id': 'process_images', 'action_model': '38'},
                         dynamic_data={'key': 'entities.38.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'process_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        'caller_user': ndb.SuperKeyProperty(kind='0', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        product.ProcessImages(transactional=True),
        rule.Write(transactional=True),
        product.WriteImages(transactional=True),
        log.Write(transactional=True),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.38.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        product.DeleteImages(transactional=True),
        product.DeleteVariants(transactional=True),
        product.DeleteContents(transactional=True),
        common.Delete(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.38'}),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.38.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'search'),
      arguments={
        'parent': ndb.SuperKeyProperty(kind='35', required=True),
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'desc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'product_category': {'operators': ['==', '!='], 'type': ndb.SuperKeyProperty(kind='17')}
            },
          indexes=[
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['product_category'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name', 'product_category'],
             'order_by': [['name', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
            }
          ),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        product.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(page_size=settings.SEARCH_PAGE),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities',
                                   'output.search_cursor': 'search_cursor',
                                   'output.search_more': 'search_more'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
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
      ),
    Action(
      key=Action.build_key('38', 'read_instances'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        'instances_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
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
      ),
    Action(
      key=Action.build_key('38', 'duplicate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugins=[]
      )
    ]
