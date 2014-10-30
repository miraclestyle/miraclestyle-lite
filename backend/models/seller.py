# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import orm, settings

from models.base import *
from plugins.base import *

from models.location import *
from plugins.seller import *


__all__ = ['SellerContentDocument', 'SellerContent', 'SellerFeedbackStats', 'SellerFeedback', 
           'SellerPluginContainer', 'Seller', 'SellerAddress', 'SellerLocation']


class SellerContentDocument(orm.BaseModel):
  
  _kind = 20
  
  _use_rule_engine = False
  
  title = orm.SuperStringProperty('1', required=True, indexed=False)
  body = orm.SuperTextProperty('2', required=True)


class SellerContent(orm.BaseModel):
  
  _kind = 21
  
  _use_rule_engine = False
  
  documents = orm.SuperLocalStructuredProperty(SellerContentDocument, '1', repeated=True)  # @todo Or we could call it pages?
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    seller_key = input.get('seller')
    return cls.build_key(seller_key._id_str, parent=seller_key)


class SellerFeedbackStats(orm.BaseModel):
  
  _kind = 36
  
  _use_record_engine = False
  _use_rule_engine = False
  
  date = orm.SuperDateTimeProperty('1', required=True)
  positive_count = orm.SuperIntegerProperty('2', required=True)
  neutral_count = orm.SuperIntegerProperty('3', required=True)
  negative_count = orm.SuperIntegerProperty('4', required=True)


class SellerFeedback(orm.BaseModel):
  
  _kind = 37
  
  _use_record_engine = False
  _use_rule_engine = False
  
  feedbacks = orm.SuperLocalStructuredProperty(SellerFeedbackStats, '1', repeated=True)
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    seller_key = input.get('seller')
    return cls.build_key(seller_key._id_str, parent=seller_key)


class SellerPluginContainer(orm.BaseModel):
  
  _kind = 22
  
  _use_rule_engine = False
  
  plugins = orm.SuperPluginStorageProperty(('107', '108', '109', '113', '117'), '1', required=True, default=[], compressed=False)
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    seller_key = input.get('seller')
    return cls.build_key(seller_key._id_str, parent=seller_key)
  
  
class SellerLocation(orm.BaseExpando):
  
  _kind = 122
 
  country = orm.SuperStringProperty('1', required=True, indexed=False)
  country_code = orm.SuperStringProperty('2', required=True, indexed=False)
  city = orm.SuperStringProperty('3', required=True, indexed=False)
  postal_code = orm.SuperStringProperty('4', required=True, indexed=False)
  street = orm.SuperStringProperty('5', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'region': orm.SuperStringProperty('6'),
    'region_code': orm.SuperStringProperty('7'),
    'email': orm.SuperStringProperty('8'),
    'telephone': orm.SuperStringProperty('9')
    }
  
  
class SellerAddress(orm.BaseExpando):
  
  _kind = 120
  
  _use_rule_engine = False
 
  country = orm.SuperKeyProperty('1', kind='12', required=True, indexed=False)
  city = orm.SuperStringProperty('2', required=True, indexed=False)
  postal_code = orm.SuperStringProperty('3', required=True, indexed=False)
  street = orm.SuperStringProperty('4', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'region': orm.SuperKeyProperty('5', kind='13'),
    'email': orm.SuperStringProperty('6'),
    'telephone': orm.SuperStringProperty('7')
    }
  
  _virtual_fields = {
    '_country': orm.SuperReferenceStructuredProperty('12', autoload=True, target_field='country'),
    '_region': orm.SuperReferenceStructuredProperty('13', autoload=True, target_field='region')
  }
  
  def get_location(self):
    location = self
    location_country = location.country.get()
    location_region = location.region.get()
    return SellerLocation(country=location_country.name,
                    country_code=location_country.code,
                    region=location_region.name,
                    region_code=location_region.code,
                    city=location.city,
                    postal_code=location.postal_code,
                    street=location.street,
                    email=location.email,
                    telephone=location.telephone)


class Seller(orm.BaseExpando):
  
  _kind = 23
  
  _use_memcache = True
  
  name = orm.SuperStringProperty('1', required=True)
  logo = SuperImageLocalStructuredProperty(Image, '2', required=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'address': orm.SuperLocalStructuredProperty(SellerAddress, '3')  # @todo Not sure if this should be required?
    }
  
  _virtual_fields = {
    '_content': orm.SuperRemoteStructuredProperty(SellerContent),
    '_feedback': orm.SuperRemoteStructuredProperty(SellerFeedback),
    '_plugin_group': orm.SuperRemoteStructuredProperty(SellerPluginContainer),
    '_records': orm.SuperRecordProperty('23')
    }
  
  _global_role = GlobalRole(
    permissions=[
      # @todo We will se if read permission is required by the public audience!
      orm.ActionPermission('23', [orm.Action.build_key('23', 'create'),
                                  orm.Action.build_key('23', 'update'),
                                  orm.Action.build_key('23', 'prepare')], True,
                           'not account._is_guest and entity._original.key_root == account.key'),
      orm.ActionPermission('23', [orm.Action.build_key('23', 'read')], True,
                           'not account._is_guest and entity._original.root_entity._original.state == "active"'),
      orm.ActionPermission('23', [orm.Action.build_key('23', 'cron')], True, 'account._is_taskqueue'),
      orm.FieldPermission('23', ['name', 'logo', 'address', '_content', '_plugin_group', '_records'], True, True,
                          'not account._is_guest and entity._original.key_root == account.key'),
      orm.FieldPermission('23', ['_feedback'], True, True, 'account._is_taskqueue and action.key_id_str == "cron"'),
      orm.FieldPermission('23', ['name', 'logo', 'address', '_feedback'], False, True,
                          'not account._is_guest and entity._original.root_entity._original.state == "active"')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('23', 'read'),
      arguments={
        'account': orm.SuperKeyProperty(kind='11', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            SellerSetupDefaults(),
            Set(cfg={'d': {'output.entity': '_seller'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('23', 'update'),
      arguments={
        'account': orm.SuperKeyProperty(kind='11', required=True),
        'name': orm.SuperStringProperty(required=True),
        'logo': SuperImageLocalStructuredProperty(Image, upload=True, process_config={'measure': False, 'transform': True,
                                                                         'width': 240, 'height': 100,
                                                                         'crop_to_fit': True}),
        'address': orm.SuperLocalStructuredProperty(SellerAddress),
        '_content': orm.SuperLocalStructuredProperty(SellerContent),
        '_plugin_group': orm.SuperLocalStructuredProperty(SellerPluginContainer),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_seller.name': 'input.name',
                           '_seller.logo': 'input.logo',
                           '_seller.address': 'input.address',
                           '_seller._content': 'input._content',
                           '_seller._plugin_group': 'input._plugin_group'}}),
            SellerSetupDefaults(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_seller'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('23', 'cron'),
      arguments={},
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            SellerCronGenerateFeedbackStats(cfg={}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write()
            ]
          )
        ]
      )
    ]
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    account_key = input.get('account')
    return cls.build_key('seller', parent=account_key)
