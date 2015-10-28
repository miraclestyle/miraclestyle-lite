# -*- coding: utf-8 -*-
'''
Created on May 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime
import json
import hashlib

import decimal
import orm
import settings
import notifications
import tools
from models.unit import *
from plugins.base import *
from plugins.catalog import *


__all__ = ['CatalogProductCategory', 'CatalogProductContent', 'CatalogProductVariant', 'CatalogProductInstance',
           'CatalogProduct', 'CatalogPricetag', 'CatalogImage', 'Catalog']


class CatalogProductCategory(orm.BaseModel):

  _kind = 24

  _use_record_engine = False
  _use_search_engine = True

  parent_record = orm.SuperKeyProperty('1', kind='24', searchable=True, indexed=False)
  name = orm.SuperStringProperty('2', searchable=True, indexed=False, required=True)
  state = orm.SuperStringProperty('3', searchable=True, indexed=False, repeated=True)

  def condition_root_or_taskqueue(account, **kwargs):
    return account._root_admin or account._is_taskqueue

  def condition_not_guest(account, **kwargs):
    return not account._is_guest

  def condition_true(**kwargs):
    return True

  _permissions = [
      orm.ExecuteActionPermission('update', condition_root_or_taskqueue),
      orm.ExecuteActionPermission('search', condition_not_guest),
      orm.ReadFieldPermission(('parent_record', 'name', 'state'), condition_true)
  ]

  _actions = [
      orm.Action(
          id='update',
          arguments={},
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      RulePrepare(),
                      RuleExec(),
                      CatalogProductCategoryUpdateWrite(cfg={'file': settings.PRODUCT_CATEGORY_DATA_FILE,
                                                             'debug_environment': settings.DEBUG})
                  ]
              )
          ]
      ),
      orm.Action(
          id='search',
          arguments={
              'search': orm.SuperSearchProperty(
                  default={'filters': [{'field': 'state', 'value': 'indexable visible', 'operator': '=='}],
                           'orders': [{'field': 'name', 'operator': 'asc'}]},
                  cfg={
                      'search_arguments': {'kind': '24', 'options': {'limit': 1000}},
                      'search_by_keys': True,
                      'use_search_engine': True,
                      'filters': {'name': orm.SuperStringProperty(),
                                  'state': orm.SuperStringProperty(choices=('indexable visible', 'indexable')),
                                  'parent_record': orm.SuperStringProperty()},
                      'indexes': [{'filters': [('state', ['==']), ('parent_record', ['==', '!='])],
                                   'orders': [('name', ['asc', 'desc'])]},
                                   {'filters': [('state', ['=='])],
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
  options = orm.SuperStringProperty('2', repeated=True, indexed=False)
  description = orm.SuperTextProperty('3')
  allow_custom_value = orm.SuperBooleanProperty('4', required=True, indexed=False, default=False)


class CatalogProductStock(orm.BaseModel):

  _kind = 133

  _use_rule_engine = False

  variant_signature = orm.SuperJsonProperty('1', required=True, default=[], indexed=False)
  availability = orm.SuperStringProperty('2', required=True, indexed=False, choices=('in stock', 'available for order', 'out of stock', 'preorder'))

  @classmethod
  def hash_signature(cls, variant_signature):
    return hashlib.md5(json.dumps(variant_signature)).hexdigest()

  @classmethod
  def prepare_key(cls, input, **kwargs):
    return cls.build_key(cls.hash_signature(input.get('variant_signature')), parent=kwargs.get('parent'))

  def prepare(self, **kwargs):
    self.key = self.prepare_key({'variant_signature': self.variant_signature}, parent=kwargs.get('parent')) # we always no matter what set the id to this


class CatalogProductStockContainer(orm.BaseModel):

  _kind = 134

  _use_rule_engine = False

  stocks = orm.SuperLocalStructuredProperty(CatalogProductStock, '1', repeated=True, indexed=False)


class CatalogProductInstance(orm.BaseExpando):

  _kind = 27

  _use_rule_engine = False

  sequence = orm.SuperIntegerProperty('1', required=True, indexed=True)
  variant_options = orm.SuperStringProperty('2', repeated=True, indexed=True)

  _default_indexed = False

  _expando_fields = {
      'code': orm.SuperStringProperty('3'),
      'description': orm.SuperTextProperty('4'),
      'unit_price': orm.SuperDecimalProperty('5'),
      'weight': orm.SuperDecimalProperty('6'),
      'volume': orm.SuperDecimalProperty('7'),
      'images': orm.SuperImageLocalStructuredProperty(orm.Image, '8', repeated=True),
      'contents': orm.SuperLocalStructuredProperty(CatalogProductContent, '9', repeated=True)
  }

  @classmethod
  def prepare_key(cls, input, **kwargs):
    return cls.build_key(None, parent=kwargs.get('parent'))

  def prepare(self, **kwargs):
    parent = kwargs.get('parent')
    if not self.key_id:
      self.key = self.prepare_key({}, parent=parent)
    else:
      self.key = self.build_key(self.key_id, parent=parent)
    if self.key_id is None and self.sequence is None:
      key = 'prepare_%s' % self.key.urlsafe()
      sequence = tools.mem_temp_get(key, tools.Nonexistent)
      if sequence is tools.Nonexistent:
        entity = self.query(ancestor=self.key.parent()).order(-self.__class__.sequence).get()
        if not entity:
          sequence = 0
        else:
          sequence = entity.sequence
        tools.mem_temp_set(key, sequence)
      else:
        tools.mem_temp_set(key, sequence + 1)
      if self._sequence is None:
        self._sequence = 0
      self.sequence = self._sequence + sequence + 1


class CatalogProduct(orm.BaseExpando):

  _kind = 28

  _use_rule_engine = False

  category = orm.SuperKeyProperty('1', kind='24', required=True, indexed=False, searchable=True)
  name = orm.SuperStringProperty('2', required=True, indexed=False, searchable=True)
  uom = orm.SuperKeyProperty('3', kind='17', default=Unit.build_key('unit'), required=True, indexed=False)
  code = orm.SuperStringProperty('4', required=True, indexed=False, searchable=True)
  description = orm.SuperTextProperty('5', required=True, searchable=True)  # Soft limit 64kb.
  unit_price = orm.SuperDecimalProperty('6', required=True, indexed=False)

  _default_indexed = False

  _expando_fields = {
      'weight': orm.SuperDecimalProperty('7'),
      'volume': orm.SuperDecimalProperty('8'),
      'images': orm.SuperImageLocalStructuredProperty(orm.Image, '9', repeated=True),
      'contents': orm.SuperLocalStructuredProperty(CatalogProductContent, '10', repeated=True),
      'variants': orm.SuperLocalStructuredProperty(CatalogProductVariant, '11', repeated=True)
  }

  _virtual_fields = {  # sorting must be done by code?
      '_instances': orm.SuperRemoteStructuredProperty('27',
                                                      name='12',
                                                      repeated=True,
                                                      search={'default': {'filters': [], 'orders': [{'field': 'sequence', 'operator': 'desc'}]},
                                                              'cfg': {
                                                          'filters': {'variant_options': orm.SuperStringProperty(repeated=True)},
                                                          'indexes': [{'ancestor': True, 'filters': [('variant_options', ['ALL_IN'])], 'orders': [('sequence', ['desc'])]},
                                                                      {'ancestor': True, 'filters': [], 'orders': [('sequence', ['desc'])]}],
                                                      }}),
      '_stock': orm.SuperRemoteStructuredProperty(CatalogProductStockContainer, name='13', autoload=True),
      '_category': orm.SuperReferenceStructuredProperty(CatalogProductCategory, target_field='category'),
      '_uom': orm.SuperReferenceStructuredProperty('17', target_field='uom', autoload=True)
  }

  def prepare(self, **kwargs):
    parent = kwargs.get('parent')
    self.key = self.build_key(parent._id_str, parent=parent)

  @classmethod
  def get_complete_key_path(cls, image_key, product_key):
    product_key_flat = list(product_key.flat())
    complete_key_path = []
    complete_key_path.extend(image_key.flat())
    complete_key_path.extend(product_key_flat[-4:])
    return orm.Key(*complete_key_path)


class CatalogPricetag(orm.BaseModel):

  _kind = 29

  _use_rule_engine = False

  image_width = orm.SuperIntegerProperty('1', required=True, indexed=False)
  image_height = orm.SuperIntegerProperty('2', required=True, indexed=False)
  position_top = orm.SuperFloatProperty('3', required=True, indexed=False)
  position_left = orm.SuperFloatProperty('4', required=True, indexed=False)
  value = orm.SuperJsonProperty('5', required=True, indexed=False)

  _virtual_fields = {
      '_product': orm.SuperRemoteStructuredProperty(CatalogProduct, required=False),  # this cant be required, because every time we need to save a pricetag, we would have to load the product
  }

  def prepare(self, **kwargs):
    self.key = self.build_key(self.key_id_str, parent=kwargs.get('parent').parent())


class CatalogImage(orm.Image):

  _kind = 30

  _use_rule_engine = False

  sequence = orm.SuperIntegerProperty('7', required=True, indexed=True)
  pricetags = orm.SuperLocalStructuredProperty(CatalogPricetag, '8', repeated=True)

  def prepare(self, **kwds):
    key_id = self.key_id
    parent = kwds.get('parent')
    self.set_key(key_id, parent=parent)
    if key_id is None and self.sequence is None:
      key = 'prepare_%s' % self.key.urlsafe()
      sequence = tools.mem_temp_get(key, tools.Nonexistent)
      if sequence is tools.Nonexistent:
        entity = self.query(ancestor=self.key.parent()).order(-self.__class__.sequence).get()
        if not entity:
          sequence = 0
        else:
          sequence = entity.sequence
        tools.mem_temp_set(key, sequence)
      self.sequence = self._sequence + sequence + 1


class Catalog(orm.BaseExpando):

  _kind = 31

  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True, searchable=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True, searchable=True)
  name = orm.SuperStringProperty('3', required=True, searchable=True)
  published_date = orm.SuperDateTimeProperty('4', required=False, searchable=True)
  discontinue_date = orm.SuperDateTimeProperty('5', required=True, searchable=True)
  state = orm.SuperStringProperty('6', required=True, default='draft',
                                  choices=('draft', 'published', 'indexed', 'discontinued'), searchable=True)

  _default_indexed = False

  _expando_fields = {
      'cover': orm.SuperImageLocalStructuredProperty(CatalogImage, '7', process_config={'copy': True, 'copy_name': 'cover',
                                                                                        'transform': True, 'width': 240,
                                                                                        'height': 240, 'crop_to_fit': True})
  }

  _virtual_fields = {
      '_images': orm.SuperImageRemoteStructuredProperty(CatalogImage, repeated=True,
                                                        search={
                                                            'default': {
                                                                'filters': [],
                                                                'orders': [{
                                                                    'field': 'sequence',
                                                                    'operator': 'desc'
                                                                }]
                                                            },
                                                            'cfg': {
                                                                'indexes': [{
                                                                    'ancestor': True,
                                                                    'filters': [],
                                                                    'orders': [('sequence', ['desc'])]
                                                                }],
                                                            }
                                                        }),
      '_seller': orm.SuperReferenceStructuredProperty('23', callback=lambda self: self.key.parent().get_async()),
      '_records': orm.SuperRecordProperty('31')
  }

  def condition_not_guest(account, **kwargs):
    return not account._is_guest

  def condition_not_guest_and_owner_or_root(account, entity, **kwargs):
    return not account._is_guest and (entity._original.key_root == account.key or account._root_admin)

  def condition_search(account, entity, action, input, **kwargs):
    def valid_search():
      if action.key_id == 'search':
        _ancestor = input['search']['ancestor']
        _filters = input['search']['filters']
        if _filters:
          field = _filters[0]['field']
          op = _filters[0]['operator']
          value = _filters[0]['value']
          if field == 'state':
            if op == '==' and value == 'indexed':
              return True
            else:
              if _ancestor:
                if op == '!=' and value == 'discontinued':
                  if _ancestor._root == account.key:
                    return True
                elif op == 'IN' and ('published' in value or 'indexed' in value):
                  return True
      return False
    return not account._is_guest and (account._root_admin or valid_search())

  def condition_published_or_discontinued(entity, **kwargs):
    return entity._original.state in ("published", "discontinued", "indexed")

  def condition_update(account, entity, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key \
        and (entity._original.state in ("draft", "published", "indexed"))

  def condition_not_guest_and_owner_and_draft(account, entity, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key \
        and entity._original.state == "draft"

  def condition_deny_write_field_permission(account, entity, action, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key \
        and entity._original.state == "draft" and action.key_id_str == "update"

  def condition_not_guest_and_owner_and_published(account, entity, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key \
        and entity._original.state in ("published", "indexed")

  def condition_publish(account, entity, **kwargs):
    return account._is_taskqueue and entity._original.state not in ("published", "indexed")

  def condition_discontinue(account, entity, **kwargs):
    return account._is_taskqueue and entity._original.state != "discontinued"

  def condition_root(account, **kwargs):
    return account._root_admin

  def condition_taskqueue(account, **kwargs):
    return account._is_taskqueue

  def condition_true(**kwargs):
    return True

  def condition_write_images(account, entity, action, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key \
        and entity._original.state == "draft" \
        and action.key_id_str \
        in ("read", "catalog_upload_images", "product_upload_images", "product_instance_upload_images", "prepare")

  def condition_write_state(account, entity, action, **kwargs):
    return (action.key_id_str == "create" and entity.state == "draft") \
        or (action.key_id_str == "publish" and entity.state == "published") \
        or (action.key_id_str == "discontinue" and entity.state == "discontinued") \
        or (action.key_id_str == "sudo" and entity.state != "draft")

  def condition_duplicate(action, **kwargs):
    return action.key_id_str in ("catalog_process_duplicate", "catalog_pricetag_process_duplicate")

  _permissions = [
      orm.ExecuteActionPermission('prepare', condition_not_guest),
      orm.ExecuteActionPermission(('create', 'read'), condition_not_guest_and_owner_or_root),
      orm.ExecuteActionPermission('search', condition_search),
      orm.ExecuteActionPermission('read', condition_published_or_discontinued),
      orm.ExecuteActionPermission('update', condition_update),
      orm.ExecuteActionPermission(('publish', 'catalog_upload_images', 'product_upload_images',
                                   'product_instance_upload_images', 'catalog_pricetag_duplicate'), condition_not_guest_and_owner_and_draft),
      orm.ExecuteActionPermission(('discontinue', 'catalog_duplicate'), condition_not_guest_and_owner_and_published),
      orm.ExecuteActionPermission('publish', condition_publish),
      orm.ExecuteActionPermission('discontinue', condition_discontinue),
      orm.ExecuteActionPermission('account_discontinue', condition_taskqueue),
      orm.ExecuteActionPermission('sudo', condition_root),
      orm.ExecuteActionPermission(('catalog_process_duplicate', 'catalog_pricetag_process_duplicate',
                                   'delete', 'index', 'unindex', 'cron'), condition_taskqueue),
      orm.ExecuteActionPermission('public_search', condition_true),
      # field permissions
      orm.ReadFieldPermission(('created', 'updated', 'name', 'published_date', 'discontinue_date',
                               'state', 'cover', '_images'), condition_not_guest_and_owner_or_root),
      orm.WriteFieldPermission(('name', 'published_date', 'discontinue_date', 'cover',
                                '_images', '_images.pricetags', '_records'), condition_not_guest_and_owner_and_draft),
      orm.DenyWriteFieldPermission(('_images.image', '_images.content_type',
                                    '_images.size', '_images.gs_object_name',
                                    '_images.serving_url',
                                    '_images.pricetags._product.images.image', '_images.pricetags._product.images.content_type',
                                    '_images.pricetags._product.images.size', '_images.pricetags._product.images.gs_object_name',
                                    '_images.pricetags._product.images.serving_url',
                                    '_images.pricetags._product._instances.images.image', '_images.pricetags._product._instances.images.content_type',
                                    '_images.pricetags._product._instances.images.size', '_images.pricetags._product._instances.images.gs_object_name',
                                    '_images.pricetags._product._instances.images.serving_url'), condition_deny_write_field_permission),
      orm.WriteFieldPermission(('_images'), condition_write_images),
      orm.WriteFieldPermission(('_records', '_images.pricetags._product._stock'), condition_not_guest_and_owner_and_published),
      orm.WriteFieldPermission('state', condition_write_state),
      orm.ReadFieldPermission(('name', 'published_date', 'discontinue_date',
                               'state', 'cover', '_images'), condition_published_or_discontinued),
      orm.ReadFieldPermission('_records', condition_root),
      orm.WriteFieldPermission('_records', condition_root),
      orm.ReadFieldPermission(('_seller.name', '_seller.logo', '_seller._content', '_seller._feedback',
                               '_seller._follower_count', '_seller._notified_followers_count', '_seller._currency'), condition_true),
      orm.WriteFieldPermission(('created', 'updated', 'name', 'published_date', 'discontinue_date',
                                'state', 'cover', 'cost', '_images'), condition_duplicate)
  ]

  _actions = [
      orm.Action(
          id='prepare',
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
          id='create',
          arguments={
              'seller': orm.SuperKeyProperty(kind='23', required=True),
              'name': orm.SuperStringProperty(required=True),
              'discontinue_date': orm.SuperDateTimeProperty(required=True)
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      Set(cfg={'s': {'_catalog.state': 'draft'},
                               'd': {'_catalog.name': 'input.name',
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
          id='read',
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
          id='update',
          arguments={
              'key': orm.SuperKeyProperty(kind='31', required=True),
              'name': orm.SuperStringProperty(required=True),
              'discontinue_date': orm.SuperDateTimeProperty(required=True),
              '_images': orm.SuperImageRemoteStructuredProperty(CatalogImage, repeated=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      Set(cfg={'d': {'_catalog.name': 'input.name',
                                     '_catalog.discontinue_date': 'input.discontinue_date',
                                     '_catalog._images': 'input._images'}}),
                      CatalogProcessCoverSet(),
                      CatalogProcessPricetags(),
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
          id='catalog_upload_images',
          arguments={
              'key': orm.SuperKeyProperty(kind='31', required=True),
              '_images': orm.SuperImageLocalStructuredProperty(CatalogImage, upload=True, repeated=True),
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
          id='product_upload_images',
          arguments={
              'key': orm.SuperKeyProperty(kind='31', required=True),
              'images': orm.SuperImageLocalStructuredProperty(orm.Image, upload=True, repeated=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      UploadImages(cfg={'path': '_catalog._images.value.0.pricetags.read_value.0._product.value.images',
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
          id='product_instance_upload_images',
          arguments={
              'key': orm.SuperKeyProperty(kind='31', required=True),
              'images': orm.SuperImageLocalStructuredProperty(orm.Image, upload=True, repeated=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      UploadImages(cfg={'path': '_catalog._images.value.0.pricetags.read_value.0._product.value._instances.value.0.images',
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
          id='delete',
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
          id='search',
          arguments={
              'search': orm.SuperSearchProperty(
                  default={'filters': [], 'orders': [{'field': 'created', 'operator': 'desc'}]},
                  cfg={
                      'search_arguments': {'kind': '31', 'options': {'limit': settings.SEARCH_PAGE}},
                      'ancestor_kind': '23',
                      'search_by_keys': True,
                      'filters': {'name': orm.SuperStringProperty(),
                                  'key': orm.SuperVirtualKeyProperty(kind='31', searchable=False),
                                  'state': orm.SuperStringProperty(choices=('published', 'indexed', 'discontinued', 'draft'))},
                      'indexes': [{'ancestor': True, 'orders': [('created', ['asc', 'desc'])]},
                                  {'ancestor': True, 'filters': [('state', ['IN'])], 'orders': [('created', ['desc']), ('key', ['desc'])]},
                                  {'ancestor': True, 'filters': [('state', ['IN'])], 'orders': [('published_date', ['desc']), ('key', ['desc'])]},
                                  {'orders': [('created', ['asc', 'desc'])]},
                                  {'orders': [('updated', ['asc', 'desc'])]},
                                  {'orders': [('published_date', ['asc', 'desc'])]},
                                  {'orders': [('discontinue_date', ['asc', 'desc'])]},
                                  {'filters': [('state', ['=='])],
                                   'orders': [('published_date', ['desc'])]},
                                  {'filters': [('key', ['=='])]}]
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
          id='publish',
          arguments={
              'key': orm.SuperKeyProperty(kind='31', required=True)
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      Set(cfg={'s': {'_catalog.state': 'published', '_catalog.published_date': datetime.datetime.now()}}),
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
                      # notify when user publishes catalog
                      Notify(cfg={'s': {'subject': notifications.CATALOG_PUBLISH_SUBJECT,
                                        'body': notifications.CATALOG_PUBLISH_BODY,
                                        'sender': settings.NOTIFY_EMAIL},
                                  'd': {'recipient': '_catalog.root_entity._primary_email'}})
                  ]
              )
          ]
      ),
      orm.Action(
          id='discontinue',
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
                      # notify owner when catalog gets discontinued
                      Notify(cfg={'s': {'subject': notifications.CATALOG_DISCONTINUE_SUBJECT,
                                        'body': notifications.CATALOG_DISCONTINUE_BODY, 'sender': settings.NOTIFY_EMAIL},
                                  'd': {'recipient': '_catalog.root_entity._primary_email'}}),
                      CallbackExec(cfg=[('callback',
                                         {'action_id': 'unindex', 'action_model': '31'},
                                         {'key': '_catalog.key_urlsafe'},
                                         None)])
                  ]
              )
          ]
      ),
      orm.Action(
          id='account_discontinue',
          arguments={
              'account': orm.SuperKeyProperty(kind='11', required=True)
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
                      CatalogDiscontinue(),
                      CallbackExec()
                  ]
              )
          ]
      ),
      orm.Action(
          id='sudo',
          arguments={
              'key': orm.SuperKeyProperty(kind='31', required=True),
              'state': orm.SuperStringProperty(required=True, choices=('published', 'discontinued', 'indexed')),
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
                      Write(),
                      RulePrepare(),
                      Set(cfg={'d': {'output.entity': '_catalog'}}),
                      # use 1 notify plugin with dynamic email
                      Notify(cfg={'s': {'subject': notifications.CATALOG_SUDO_SUBJECT,
                                        'body': notifications.CATALOG_SUDO_BODY, 'sender': settings.NOTIFY_EMAIL},
                                  'd': {'recipient': '_catalog.root_entity._primary_email'}}),
                      CallbackExec(cfg=[('callback',
                                         {'action_model': '31', 'action_id': 'index'},
                                         {'key': '_catalog.key_urlsafe'},
                                         lambda entity: entity.state == 'indexed')]),
                      CallbackExec(cfg=[('callback',
                                         {'action_model': '31', 'action_id': 'unindex'},
                                         {'key': '_catalog.key_urlsafe'},
                                         lambda entity: entity.state in ('published', 'discontinued'))])
                  ]
              )
          ]
      ),
      orm.Action(
          id='index',
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
                      Write()
                  ]
              )
          ]
      ),
      orm.Action(
          # marketing.SearchDelete() plugin deems this action to allways execute in taskqueue!
          id='unindex',
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
                      Write()
                  ]
              )
          ]
      ),
      orm.Action(
          id='cron',
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
          id='catalog_duplicate',
          arguments={
              'key': orm.SuperKeyProperty(kind='31', required=True),
              'channel': orm.SuperStringProperty(required=True)
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
                                         {'key': '_catalog.key_urlsafe',
                                          'channel': 'input.channel'},
                                         None)])
                  ]
              )
          ]
      ),
      orm.Action(
          id='catalog_process_duplicate',
          arguments={
              'key': orm.SuperKeyProperty(kind='31', required=True),
              'channel': orm.SuperStringProperty(required=True)
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
                      Write(),
                      # notify duplication process complete via channel
                      Notify(cfg={'s': {'sender': settings.NOTIFY_EMAIL},
                                  'd': {'recipient': 'input.channel', 'catalog_key': '_catalog.key_urlsafe'},
                                  'method': 'channel'})
                  ]
              )
          ]
      ),
      orm.Action(
          id='catalog_pricetag_duplicate',
          arguments={
              'key': orm.SuperKeyProperty(kind='31', required=True),
              'channel': orm.SuperStringProperty(required=True),
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
                                         {'action_id': 'catalog_pricetag_process_duplicate', 'action_model': '31'},
                                         {'key': '_catalog.key_urlsafe',
                                          'channel': 'input.channel',
                                          'read_arguments': 'input.read_arguments'},
                                         None)])
                  ]
              )
          ]
      ),
      orm.Action(
          id='catalog_pricetag_process_duplicate',
          arguments={
              'key': orm.SuperKeyProperty(kind='31', required=True),
              'channel': orm.SuperStringProperty(required=True),
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
                      Duplicate(cfg={'duplicate_path': '_images.value.0.pricetags.read_value.0'}),
                      CatalogPricetagSetDuplicatedPosition(),
                      Write(),
                      # notify duplication process complete via channel
                      Notify(cfg={'s': {'sender': settings.NOTIFY_EMAIL},
                                  'd': {'recipient': 'input.channel',
                                        'catalog_key': '_catalog.key_urlsafe',
                                        'pricetag_key': 'duplicated_entity.key_urlsafe',
                                        'image_key': '_catalog._images.value.0.key_urlsafe'},
                                  'method': 'channel'})
                  ]
              )
          ]
      ),
      orm.Action(
          id='public_search',
          arguments={
              'search': orm.SuperSearchProperty(
                  default={'kind': '31', 'orders': [{'field': 'created', 'operator': 'desc'}]},
                  cfg={
                      'search_arguments': {'kind': '31', 'options': {'limit': settings.SEARCH_PAGE}},
                      'use_search_engine': True,
                      'filters': {'ancestor': orm.SuperStringProperty(repeated=True),
                                  'seller_account_key': orm.SuperStringProperty(repeated=True)},
                      'orders': {'created': {'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}},
                                 'updated': {'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}}},
                      'indexes': [{'filters': [],
                                   'orders': [('created', ['asc', 'desc'])]},
                                  {'filters': [('ancestor', ['IN'])],
                                   'orders': [('created', ['asc', 'desc'])]},
                                  {'filters': [('seller_account_key', ['IN'])],
                                   'orders': [('created', ['asc', 'desc'])]}]
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

  @classmethod
  def prepare_key(cls, input, **kwargs):
    return cls.build_key(None, parent=input.get('seller'))
