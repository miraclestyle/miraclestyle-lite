# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models import *
from app.plugins import *


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


class SellerPluginContainer(orm.BaseModel):
  
  _kind = 22
  
  _use_rule_engine = False
  
  plugins = orm.SuperPluginStorageProperty(('0',), '1', required=True, default=[], compressed=False)
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    seller_key = input.get('seller')
    return cls.build_key(seller_key._id_str, parent=seller_key)


class Seller(orm.BaseExpando):
  
  _kind = 23
  
  _use_memcache = True
  
  name = orm.SuperStringProperty('1', required=True)
  logo = SuperImageLocalStructuredProperty(Image, '2', required=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'address': orm.SuperLocalStructuredProperty(Address, '3')  # @todo Not sure if this should be required?
    }
  
  _virtual_fields = {
    '_content': SuperRemoteStructuredProperty(SellerContent),
    '_plugin_group': SuperRemoteStructuredProperty(SellerPluginContainer),
    '_records': orm.SuperRecordProperty('23')
    }
  
  _global_role = GlobalRole(
    permissions=[
      # @todo We will se if read permission is required by the public audience!
      orm.ActionPermission('23', [orm.Action.build_key('23', 'create'),
                                  orm.Action.build_key('23', 'update')], True,
                           'not account._is_guest and entity._original.key_root == account.key'),
      orm.ActionPermission('23', [orm.Action.build_key('23', 'read')], True,
                           'not account._is_guest and entity._original.parent_entity._original.state == "active"'),
      orm.FieldPermission('22', ['name', 'logo', 'address', '_content', '_plugin_group', '_records'], True, True,
                          'not account._is_guest and entity._original.key_root == account.key'),
      orm.FieldPermission('22', ['name', 'logo', 'address'], False, True,
                          'not account._is_guest and entity._original.parent_entity._original.state == "active"')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('23', 'create'),
      arguments={
        'account': orm.SuperKeyProperty(kind='11', required=True),
        'name': orm.SuperStringProperty(required=True),
        'logo': SuperImageLocalStructuredProperty(Image, required=True,
                                                  process_config={'measure': False, 'transform': True,
                                                                  'width': 240, 'height': 100,
                                                                  'crop_to_fit': True}),
        'address': orm.SuperLocalStructuredProperty(Address)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_seller.name': 'input.name',
                           '_seller.logo': 'input.logo',
                           '_seller.address': 'input.address'}}),
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
      key=orm.Action.build_key('23', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='23', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_seller'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('23', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='23', required=True),
        'name': orm.SuperStringProperty(required=True),
        'logo': SuperImageLocalStructuredProperty(Image, process_config={'measure': False, 'transform': True,
                                                                         'width': 240, 'height': 100,
                                                                         'crop_to_fit': True}),
        'address': orm.SuperLocalStructuredProperty(Address),
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
      )
    ]
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    account_key = input.get('account')
    return cls.build_key('seller', parent=account_key)
