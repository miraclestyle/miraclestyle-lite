# -*- coding: utf-8 -*-
'''
Created on May 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime
import json

import orm, settings, mem
from models.base import *
from plugins.base import *
from plugins.catalog import *
from util import *


__all__ = ['CatalogProductCategory', 'CatalogProductContent', 'CatalogProductVariant', 'CatalogProductInstance',
           'CatalogProduct', 'CatalogPricetag', 'CatalogImage', 'Catalog']


class CatalogProductCategory(orm.BaseModel):
  
  _kind = 24
  
  _use_record_engine = False
  
  parent_record = orm.SuperKeyProperty('1', kind='24', indexed=False)
  name = orm.SuperStringProperty('2', required=True)
  complete_name = orm.SuperTextProperty('3', required=True)
  state = orm.SuperStringProperty('4', required=True, default='indexable')
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('24', [orm.Action.build_key('24', 'update')], True,
                           'account._root_admin or account._is_taskqueue'),
      orm.ActionPermission('24', [orm.Action.build_key('24', 'search')], True, 'not account._is_guest'),
      orm.FieldPermission('24', ['parent_record', 'name', 'complete_name', 'state'], False, True, 'True'),
      orm.FieldPermission('24', ['parent_record', 'name', 'complete_name', 'state'], True, True,
                          'account._root_admin or account._is_taskqueue')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('24', 'update'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogProductCategoryUpdateWrite(cfg={'file': settings.PRODUCT_CATEGORY_DATA_FILE,
                                                   'prod_env': settings.DEVELOPMENT_SERVER})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('24', 'search'),  # @todo Search is very inaccurate when using 'contains' filter. so we will have to use here document search i think.
      arguments={  # @todo Add default filter to list active ones.
        'search': orm.SuperSearchProperty(
          default={'filters': [{'field': 'state', 'value': 'indexable', 'operator': '=='}], 'orders': [{'field': 'name', 'operator': 'asc'}]},
          cfg={
            'search_arguments': {'kind': '24', 'options': {'limit': settings.SEARCH_PAGE}},
            'search_by_keys': True,
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
      )
    ]


class CatalogProductContent(orm.BaseModel):
  
  _kind = 25
  
  _use_rule_engine = False
  
  title = orm.SuperStringProperty('1', required=True, indexed=False)
  body = orm.SuperTextProperty('2', required=True)


class CatalogProductVariant(orm.BaseModel):
  
  _kind = 26
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  description = orm.SuperTextProperty('2')
  options = orm.SuperStringProperty('3', repeated=True, indexed=False)
  allow_custom_value = orm.SuperBooleanProperty('4', required=True, indexed=False, default=False)


class CatalogProductInstance(orm.BaseExpando):
  
  _kind = 27
  
  _use_rule_engine = False
  
  variant_signature = orm.SuperJsonProperty('1', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'description': orm.SuperTextProperty('2'),
    'unit_price': orm.SuperDecimalProperty('3'),
    'availability': orm.SuperStringProperty('4', default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder']),
    'code': orm.SuperStringProperty('5'),
    'weight': orm.SuperDecimalProperty('6'),
    'weight_uom': orm.SuperKeyProperty('7', kind='17'),
    'volume': orm.SuperDecimalProperty('8'),
    'volume_uom': orm.SuperKeyProperty('9', kind='17'),
    'images': SuperImageLocalStructuredProperty(Image, '10', repeated=True),
    'contents': orm.SuperLocalStructuredProperty(CatalogProductContent, '11', repeated=True)
    }
  
  _virtual_fields = {
    '_weight_uom': orm.SuperReferenceStructuredProperty('17', target_field='weight_uom'),
    '_volume_uom': orm.SuperReferenceStructuredProperty('17', target_field='volume_uom')
    }
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    variant_signature = input.get('variant_signature')  # @todo This variant signature has to be filtered to remove custom variant values!
    key_id = hashlib.md5(json.dumps(variant_signature)).hexdigest()
    product_instance_key = cls.build_key(key_id, parent=kwargs.get('parent'))
    return product_instance_key
  
  def prepare(self, **kwargs):
    self.key = self.prepare_key({'variant_signature': self.variant_signature}, **kwargs)


class CatalogProduct(orm.BaseExpando):
  
  _kind = 28
  
  _use_rule_engine = False
  
  product_category = orm.SuperKeyProperty('1', kind='24', required=True, searchable=True)
  name = orm.SuperStringProperty('2', required=True, searchable=True)
  description = orm.SuperTextProperty('3', required=True, searchable=True)  # Soft limit 64kb.
  product_uom = orm.SuperKeyProperty('4', kind='17', required=True, indexed=False)
  unit_price = orm.SuperDecimalProperty('5', required=True, indexed=False)
  availability = orm.SuperStringProperty('6', required=True, indexed=False, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder'])
  code = orm.SuperStringProperty('7', required=True, indexed=False, searchable=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'weight': orm.SuperDecimalProperty('8'),
    'weight_uom': orm.SuperKeyProperty('9', kind='17'),
    'volume': orm.SuperDecimalProperty('10'),
    'volume_uom': orm.SuperKeyProperty('11', kind='17'),
    'images': SuperImageLocalStructuredProperty(Image, '12', repeated=True),
    'contents': orm.SuperLocalStructuredProperty(CatalogProductContent, '13', repeated=True),
    'variants': orm.SuperLocalStructuredProperty(CatalogProductVariant, '14', repeated=True)
    }
  
  _virtual_fields = {
    '_instances': orm.SuperRemoteStructuredProperty(CatalogProductInstance, repeated=True),
    '_product_category': orm.SuperReferenceStructuredProperty(CatalogProductCategory, target_field='product_category'),
    '_weight_uom': orm.SuperReferenceStructuredProperty('17', target_field='weight_uom'),
    '_volume_uom': orm.SuperReferenceStructuredProperty('17', target_field='volume_uom')
    }


class CatalogPricetag(orm.BaseModel):
  
  _kind = 29
  
  _use_rule_engine = False
  
  product = orm.SuperKeyProperty('1', kind='28', required=True, indexed=False)
  image_width = orm.SuperIntegerProperty('2', required=True, indexed=False)  # @todo We will test pricetag positioning without these values!
  image_height = orm.SuperIntegerProperty('3', required=True, indexed=False)  # @todo We will test pricetag positioning without these values!
  position_top = orm.SuperFloatProperty('4', required=True, indexed=False)
  position_left = orm.SuperFloatProperty('5', required=True, indexed=False)
  value = orm.SuperStringProperty('6', required=True, indexed=False)


class CatalogImage(Image):
  
  _kind = 30
  
  _use_rule_engine = False
  
  sequence = orm.SuperIntegerProperty('7', required=True, indexed=True)
  pricetags = orm.SuperLocalStructuredProperty(CatalogPricetag, '8', repeated=True)
  
  def prepare(self, **kwds):
    key_id = self.key_id
    self.set_key(key_id, parent=kwds.get('parent'))
    if key_id is None and self.sequence is None:
      key = 'prepare_%s' % self.key.urlsafe()
      sequence = mem.temp_get(key, Nonexistent)
      if sequence is Nonexistent:
        entity = self.query(ancestor=self.key.parent()).order(-self.__class__.sequence).get()
        if not entity:
          sequence = 0
        else:
          sequence = entity.sequence
        mem.temp_set(key, sequence)
      self.sequence = self._sequence + sequence


class Catalog(orm.BaseExpando):
  
  _kind = 31
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True, searchable=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True, searchable=True)
  name = orm.SuperStringProperty('3', required=True, searchable=True)
  publish_date = orm.SuperDateTimeProperty('4', required=True, searchable=True)
  discontinue_date = orm.SuperDateTimeProperty('5', required=True, searchable=True)
  state = orm.SuperStringProperty('6', required=True, default='draft',
                                  choices=['draft', 'published', 'discontinued'], searchable=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'cover': SuperImageLocalStructuredProperty(CatalogImage, '7', process_config={'copy': True, 'copy_name': 'cover',
                                                                                  'transform': True, 'width': 240,
                                                                                  'height': 360, 'crop_to_fit': True}),
    'cost': orm.SuperDecimalProperty('8')
    }
  
  _virtual_fields = {
    '_images': SuperImageRemoteStructuredProperty(CatalogImage, repeated=True,
                                                  read_arguments={'config': {'order': {'field': 'sequence',
                                                                                       'direction': 'desc'}}}),
    '_products': orm.SuperRemoteStructuredProperty(CatalogProduct, repeated=True,
                                                  read_arguments={'config': {'order': {'field': 'name',
                                                                                       'direction': 'asc'}}}),
    '_records': orm.SuperRecordProperty('31')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('31', [orm.Action.build_key('31', 'prepare')], True, 'not account._is_guest'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'create'),
                                  orm.Action.build_key('31', 'read')], True,
                           'not account._is_guest and entity._original.key_root == account.key'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'search')], True,
                           'account._root_admin or (not account._is_guest and (entity._original.key_root == account.key)) \
                           or (action.key_id == "search" and input["search"]["ancestor"]._root == account.key)'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'read')], True,
                           'entity._original.state == "published" or entity._original.state == "discontinued"'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'update'),
                                  orm.Action.build_key('31', 'catalog_upload_images'),
                                  orm.Action.build_key('31', 'product_upload_images'),
                                  orm.Action.build_key('31', 'product_instance_upload_images'),
                                  orm.Action.build_key('31', 'product_duplicate')], True,
                           'not account._is_guest and entity._original.key_root == account.key \
                           and entity._original.state == "draft"'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'discontinue'),
                                  orm.Action.build_key('31', 'catalog_duplicate')], True,
                           'not account._is_guest and entity._original.key_root == account.key \
                           and entity._original.state == "published"'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'publish')], True,
                           '(account._is_taskqueue or account._root_admin) and entity._original.state != "published"'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'discontinue')], True,
                           'account._is_taskqueue and entity._original.state != "discontinued"'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'account_discontinue')], True, 'account._root_admin'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'sudo')], True, 'account._root_admin'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'catalog_process_duplicate'),
                                  orm.Action.build_key('31', 'product_process_duplicate'),
                                  orm.Action.build_key('31', 'delete'),
                                  orm.Action.build_key('31', 'index'),
                                  orm.Action.build_key('31', 'unindex'),
                                  orm.Action.build_key('31', 'cron')], True, 'account._is_taskqueue'),
      orm.ActionPermission('31', [orm.Action.build_key('31', 'public_search')], True, 'True'),
      orm.FieldPermission('31', ['created', 'updated', 'name', 'publish_date', 'discontinue_date',
                                 'state', 'cover', 'cost', '_images', '_products', '_records'], False, True,
                          'account._is_taskqueue or account._root_admin or (not account._is_guest \
                          and entity._original.key_root == account.key)'),
      orm.FieldPermission('31', ['name', 'publish_date', 'discontinue_date',
                                 'cover', '_images', '_products', '_records'], True, True,
                          'not account._is_guest and entity._original.key_root == account.key \
                          and entity._original.state == "draft"'),
      orm.FieldPermission('31', ['state'], True, True,
                          '(action.key_id_str == "create" and entity.state == "draft") \
                          or (action.key_id_str == "publish" and entity.state == "published") \
                          or (action.key_id_str == "discontinue" and entity.state == "discontinued") \
                          or (action.key_id_str == "sudo" and entity.state != "draft")'),
      orm.FieldPermission('31', ['name', 'publish_date', 'discontinue_date',
                                 'state', 'cover', '_images', '_products'], False, True,
                          'entity._original.state == "published" or entity._original.state == "discontinued"'),
      orm.FieldPermission('31', ['_records.note'], True, True, 'account._root_admin'),
      orm.FieldPermission('31', ['_records.note'], False, False, 'not account._root_admin'),
      orm.FieldPermission('31', ['_images.image', '_images.content_type', '_images.size', '_images.gs_object_name', '_images.serving_url',
                                 '_products.images.image', '_products.images.content_type', '_products.images.size', '_images.proportion',
                                 '_products.images.gs_object_name', '_products.images.serving_url', '_products.images.proportion',
                                 '_products._instances.images.image', '_products._instances.images.content_type', '_products._instances.images.size',
                                 '_products._instances.images.gs_object_name', '_products._instances.images.serving_url', '_products._instances.images.proportion'], False, None,
                          '(action.key_id_str not in ["catalog_upload_images", "product_upload_images", \
                          "product_instance_upload_images", "catalog_process_duplicate", "product_process_duplicate"])'),
      orm.FieldPermission('31', ['created', 'updated', 'name', 'publish_date', 'discontinue_date',
                                 'state', 'cover', 'cost', '_images', '_products'], True, True,
                          '(action.key_id_str in ["catalog_process_duplicate", "product_process_duplicate"])')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('31', 'prepare'),
      arguments={
        'seller': orm.SuperKeyProperty(kind='23', required=True)
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
      key=orm.Action.build_key('31', 'create'),
      arguments={
        'seller': orm.SuperKeyProperty(kind='23', required=True),
        'name': orm.SuperStringProperty(required=True),
        'publish_date': orm.SuperDateTimeProperty(required=True),
        'discontinue_date': orm.SuperDateTimeProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_catalog.state': 'draft'},
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
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True),
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
      key=orm.Action.build_key('31', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True),
        'name': orm.SuperStringProperty(required=True),
        'publish_date': orm.SuperDateTimeProperty(required=True),
        'discontinue_date': orm.SuperDateTimeProperty(required=True),
        '_images': SuperImageRemoteStructuredProperty(CatalogImage, repeated=True),
        '_products': orm.SuperRemoteStructuredProperty(CatalogProduct, repeated=True),
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
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'catalog_upload_images'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True),
        '_images': SuperImageLocalStructuredProperty(CatalogImage, upload=True, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            UploadImages(cfg={'path': '_catalog._images',
                              'images_path': 'input._images'}),
            CatalogProcessCoverSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'product_upload_images'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True),
        'images': SuperImageLocalStructuredProperty(Image, upload=True, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            UploadImages(cfg={'path': '_catalog._products.value.0.images',
                              'images_path': 'input.images'}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'product_instance_upload_images'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True),
        'images': SuperImageLocalStructuredProperty(Image, upload=True, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            UploadImages(cfg={'path': '_catalog._products.value.0._instances.value.0.images',
                              'images_path': 'input.images'}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      # marketing.Delete() plugin deems this action to allways execute in taskqueue!
      key=orm.Action.build_key('31', 'delete'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True)
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
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'orders': [{'field': 'created', 'operator': 'desc'}]},
          cfg={
            'search_arguments': {'kind': '31', 'options': {'limit': settings.SEARCH_PAGE}},
            'ancestor_kind': '23',
            'search_by_keys': True,
            'filters': {'name': orm.SuperStringProperty(),
                        'state': orm.SuperStringProperty(choices=['invited', 'accepted'])},
            'indexes': [{'ancestor': True, 'orders': [('name', ['asc', 'desc'])]},
                        {'ancestor': True, 'orders': [('created', ['asc', 'desc'])]},
                        {'ancestor': True, 'orders': [('updated', ['asc', 'desc'])]},
                        {'orders': [('name', ['asc', 'desc'])]},
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
            RulePrepare(cfg={'d': {'input': 'input'}}),
            RuleExec(),
            # @todo We will try to let the rule engine handle ('d': {'ancestor': 'account.key'}).
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
      key=orm.Action.build_key('31', 'publish'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True)
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
            Write(),
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'index', 'action_model': '31'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'discontinue'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True)
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
            Write(),
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'unindex', 'action_model': '31'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'account_discontinue'),
      arguments={
        'account': orm.SuperKeyProperty(kind='11', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogDiscontinue(cfg={'page': 100}),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'sudo'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True),
        'state': orm.SuperStringProperty(required=True, choices=['published', 'discontinued']),
        'index_state': orm.SuperStringProperty(choices=['index', 'unindex']),
        'message': orm.SuperTextProperty(required=True),
        'note': orm.SuperTextProperty(required=True)
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
            Write(),  # 'index_state': 'input.index_state',  # @todo We embed this field on the fly, to indicate what administrator has chosen!
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            # @todo Finish Notify plugins!
            Notify(cfg={'condition': 'entity.state == "discontinued"',
                        'd': {'recipient': 'entity.root_entity._primary_email',
                              'subject': 'Catalog Discontinued by Admin.',
                              'body': 'input.message'}}),
            Notify(cfg={'d': {'recipient': 'account._primary_email',
                              'subject': 'Admin Note',
                              'body': 'input.note'}}),
            CallbackExec(cfg=[('callback',
                               {'action_model': '31'},
                               {'action_id': 'input.index_state', 'key': '_catalog.key_urlsafe'})])  # @todo What happens if input.index_state is not supplied (e.g. None)?
            ]
          )
        ]
      ),
    orm.Action(
      # marketing.SearchWrite() plugin deems this action to allways execute in taskqueue!
      key=orm.Action.build_key('31', 'index'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True)
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
            Write(cfg={'sra': {'log_entity': False}})  # @todo Perhaps entity should be logged in order to refresh updated field? - 'd': {'message': 'tmp.message'}
            ]
          )
        ]
      ),
    orm.Action(
      # marketing.SearchDelete() plugin deems this action to allways execute in taskqueue!
      key=orm.Action.build_key('31', 'unindex'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True)
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
            Write(cfg={'sra': {'log_entity': False}})  # @todo Perhaps entity should be logged in order to refresh updated field? - 'd': {'message': 'tmp.message'}
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'cron'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogCronDiscontinue(cfg={'page': 100}),
            CatalogCronDelete(cfg={'page': 100,
                                   'unpublished_life': settings.CATALOG_UNPUBLISHED_LIFE,
                                   'discontinued_life': settings.CATALOG_DISCONTINUED_LIFE}),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'catalog_duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'catalog_process_duplicate', 'action_model': '31'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'catalog_process_duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True)
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
            Set(cfg={'s': {'_catalog.state': 'draft'}, 'rm': ['_catalog.created']}),
            Write()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'product_duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True),
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
            CallbackExec(cfg=[('callback',
                               {'action_id': 'product_process_duplicate', 'action_model': '31'},
                               {'key': '_catalog.key_urlsafe', 'read_arguments': 'input.read_arguments'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('31', 'product_process_duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='31', required=True),
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
            Duplicate(cfg={'copy_path': '_products.value.0'}),
            Write()
            ]
          )
        ]
      ),
    # @todo 'indexes' will need optimization!
    orm.Action(
      key=orm.Action.build_key('31', 'public_search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'kind': '31', 'orders': [{'field': 'created', 'operator': 'desc'}]},
          cfg={
            'search_arguments': {'kind': '31', 'options': {'limit': settings.SEARCH_PAGE}},
            'use_search_engine': True,
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
  
  def duplicate(self):
    duplicated_entity = super(Catalog, self).duplicate()
    if duplicated_entity._images.value:
      for image in duplicated_entity._images.value:
        if image.pricetags.value:
          for tag in image.pricetags.value:
            tag.product = CatalogProduct.build_key(duplicated_entity.duplicate_key_id(tag.product), parent=duplicated_entity.key, namespace=duplicated_entity.key.namespace())
    return duplicated_entity
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    seller_key = input.get('seller')
    return cls.build_key(None, parent=seller_key)
