# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import orm
import settings
import tools
from plugins.base import *
from models.location import *
from plugins.seller import *


__all__ = ['SellerContentDocument', 'SellerContent',
           'SellerPluginContainer', 'Seller']


class SellerContentDocument(orm.BaseModel):

  _kind = 20

  _use_rule_engine = False

  title = orm.SuperStringProperty('1', required=True, indexed=False)
  body = orm.SuperTextProperty('2', required=True)


class SellerContent(orm.BaseModel):

  _kind = 21

  _use_rule_engine = False
  _use_memcache = False

  documents = orm.SuperLocalStructuredProperty(SellerContentDocument, '1', repeated=True)

  @classmethod
  def prepare_key(cls, **kwargs):
    return cls.build_key('_content', parent=kwargs.get('parent'))

  def prepare(self, **kwargs):
    self.key = self.prepare_key(**kwargs)


class SellerPluginContainer(orm.BaseModel):

  _kind = 22

  _use_rule_engine = False
  _use_memcache = False

  plugins = orm.SuperPluginStorageProperty(('107', '113', '117', '126', '108', '109'), '1', required=True, default=[], compressed=False)

  @classmethod
  def prepare_key(cls, **kwargs):
    return cls.build_key('_plugin_group', parent=kwargs.get('parent'))

  def prepare(self, **kwargs):
    self.key = self.prepare_key(**kwargs)


class Seller(orm.BaseExpando):

  _kind = 23

  _use_memcache = False

  name = orm.SuperStringProperty('1', required=True)
  logo = orm.SuperImageLocalStructuredProperty(orm.Image, '2', required=True)

  _default_indexed = False

  _virtual_fields = {
      '_content': orm.SuperRemoteStructuredProperty(SellerContent),
      '_plugin_group': orm.SuperRemoteStructuredProperty(SellerPluginContainer),
      '_records': orm.SuperRecordProperty('23'),
      '_currency': orm.SuperReferenceProperty('17', autoload=True, callback=lambda self: self.get_currency_callback(),
                                              format_callback=lambda self, value: value)
  }

  def condition_not_guest_and_owner(action, account, entity, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key

  def condition_owner_active(action, account, entity, **kwargs):
    return entity._original.root_entity.state == "active"

  _permissions = [
      orm.ExecuteActionPermission(('create', 'update', 'prepare'), condition_not_guest_and_owner),
      orm.ExecuteActionPermission('read', condition_owner_active),
      orm.ReadFieldPermission(('_plugin_group'), condition_not_guest_and_owner),
      orm.ReadFieldPermission(('name', 'logo', 'updated', '_content', '_currency'), condition_owner_active),
      orm.WriteFieldPermission(('name', 'logo', '_content', '_plugin_group', '_records'), condition_not_guest_and_owner)
  ]

  _actions = [
      orm.Action(
          id='read',
          arguments={
              'account': orm.SuperKeyProperty(kind='11', required=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      GetCache(cfg={'group': lambda context: 'read_23_%s' % context.input['account']._id_str, 'cache': [lambda context: 'account' if context.account.key == context.input['account'] else None, 'all']}),
                      Read(),
                      RulePrepare(),
                      RuleExec(),
                      SellerSetupDefaults(),
                      Set(cfg={'d': {'output.entity': '_seller'}}),
                      CallbackExec()
                  ]
              )
          ]
      ),
      orm.Action(
          id='update',
          arguments={
              'account': orm.SuperKeyProperty(kind='11', required=True),
              'name': orm.SuperStringProperty(required=True),
              'logo': orm.SuperImageLocalStructuredProperty(orm.Image,
                                                            upload=True,
                                                            process_config={'measure': False,
                                                                            'transform': True,
                                                                            'width': 720,
                                                                            'height': 300,
                                                                            'crop_to_fit': True}),
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
                      DeleteCache(cfg={'group': lambda context: 'read_23_%s' % context.input['account']._id_str}),
                      Set(cfg={'d': {'output.entity': '_seller'}})
                  ]
              )
          ]
      )
  ]

  def get_currency_callback(self):
    currency = None
    if self.key:
      self._plugin_group.read()
      for plugin in self._plugin_group.value.plugins:
        if plugin.get_kind() == '117':
          currency = plugin.currency
      if currency is not None:
        currency = currency.get_async()
    return currency

  @classmethod
  def prepare_key(cls, input, **kwargs):
    return cls.build_key('seller', parent=input.get('account'))
