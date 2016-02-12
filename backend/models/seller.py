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


__all__ = ['SellerPluginContainer', 'Seller']


class SellerPluginContainer(orm.BaseModel):

  _kind = 22

  _use_rule_engine = False

  plugins = orm.SuperPluginStorageProperty(('107', '113', '117', '126', '109', '114'), '1', required=True, default=[], compressed=False)

  @classmethod
  def prepare_key(cls, **kwargs):
    return cls.build_key('_plugin_group', parent=kwargs.get('parent'))

  def prepare(self, **kwargs):
    self.key = self.prepare_key(**kwargs)


class Seller(orm.BaseExpando):

  _kind = 23

  _use_record_engine = True

  name = orm.SuperStringProperty('1', required=True)
  logo = orm.SuperImageLocalStructuredProperty(orm.Image, '2', required=True)

  _default_indexed = False

  _virtual_fields = {
      '_plugin_group': orm.SuperRemoteStructuredProperty(SellerPluginContainer),
      '_records': orm.SuperRecordProperty('23'),
      '_stripe_publishable_key': orm.SuperComputedProperty(lambda self: self.get_stripe_publishable_key()),
      '_currency': orm.SuperReferenceProperty('17', autoload=True, callback=lambda self: self.get_currency_callback(),
                                              format_callback=lambda self, value: value)
  }

  def condition_not_guest_and_owner(action, account, entity, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key

  def condition_owner_active(action, account, entity, **kwargs):
    return entity._original.root_entity.state == "active"

  def condition_taskqueue(account, **kwargs):
    return account._is_taskqueue

  _permissions = [
      orm.ExecuteActionPermission(('create', 'read', 'update', 'prepare'), condition_not_guest_and_owner),
      orm.ExecuteActionPermission('far_cache_groups_flush', condition_owner_active),
      orm.ReadFieldPermission(('name', 'logo', '_plugin_group', '_currency', '_stripe_publishable_key'), condition_not_guest_and_owner),
      orm.WriteFieldPermission(('name', 'logo', '_plugin_group', '_records'), condition_not_guest_and_owner)
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
          id='far_cache_groups_flush',
          arguments={
              'key': orm.SuperKeyProperty(kind='23', required=True)
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      RulePrepare(),
                      RuleExec(),
                      SellerDeleteFarCacheGroups(),
                      Set(cfg={'d': {'output.entity': '_seller'}}),
                      DeleteCache()
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
                                     '_seller._plugin_group': 'input._plugin_group'}}),
                      SellerInterceptEncryptedValue(),
                      SellerSetupDefaults(),
                      SellerMaybeDeleteFarCacheGroups(),
                      RulePrepare(),
                      RuleExec()
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      Write(),
                      DeleteCache(cfg={'group': lambda context: 'read_23_%s' % context.input['account']._id_str}),
                      Set(cfg={'d': {'output.entity': '_seller'}}),
                      CallbackExec()
                  ]
              )
          ]
      )
  ]

  def get_stripe_publishable_key(self):
    stripe_publishable_key = None
    if self.key:
      self._plugin_group.read()
      for plugin in self._plugin_group.value.plugins:
        if plugin.get_kind() == '114':
          stripe_publishable_key = plugin.publishable_key
    return stripe_publishable_key    

  def get_currency_callback(self):
    currency = None
    if self.key:
      self._plugin_group.read()
      for plugin in self._plugin_group.value.plugins:
        if ((plugin.get_kind() == '117') and (plugin.active)):
          currency = plugin.currency
      if currency is not None:
        currency = currency.get_async()
    return currency

  @classmethod
  def prepare_key(cls, input, **kwargs):
    return cls.build_key('seller', parent=input.get('account'))
