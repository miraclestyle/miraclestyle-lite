# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import orm
import settings
import mem

from models.base import *
from plugins.base import *

from models.location import *
from plugins.seller import *


__all__ = ['SellerContentDocument', 'SellerContent',
           'SellerFeedbackStats', 'SellerFeedback',
           'SellerPluginContainer', 'Seller']


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
  def prepare_key(cls, **kwargs):
    seller_key = kwargs.get('parent')
    return cls.build_key('_content', parent=seller_key)

  def prepare(self, **kwargs):
    self.key = self.prepare_key(**kwargs)


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
  def prepare_key(cls, **kwargs):
    seller_key = kwargs.get('parent')
    return cls.build_key('_feedback', parent=seller_key)

  def prepare(self, **kwargs):
    self.key = self.prepare_key(**kwargs)


class SellerPluginContainer(orm.BaseModel):
  
  _kind = 22
  
  _use_rule_engine = False
  
  plugins = orm.SuperPluginStorageProperty(('107', '113', '117', '126', '108', '109'), '1', required=True, default=[], compressed=False)
  
  @classmethod
  def prepare_key(cls, **kwargs):
    seller_key = kwargs.get('parent')
    return cls.build_key('_plugin_group', parent=seller_key)

  def prepare(self, **kwargs):
    self.key = self.prepare_key(**kwargs)


class Seller(orm.BaseExpando):
  
  _kind = 23
  
  _use_memcache = True
  
  name = orm.SuperStringProperty('1', required=True)
  logo = SuperImageLocalStructuredProperty(Image, '2', required=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_content': orm.SuperRemoteStructuredProperty(SellerContent),
    '_feedback': orm.SuperRemoteStructuredProperty(SellerFeedback),
    '_plugin_group': orm.SuperRemoteStructuredProperty(SellerPluginContainer),
    '_records': orm.SuperRecordProperty('23'),
    '_follower_count': orm.SuperComputedProperty(lambda self: self.get_followers_count_callback()),
    '_notified_followers_count': orm.SuperComputedProperty(lambda self: self.get_notified_followers_count_callback()),
    '_currency': orm.SuperReferenceProperty('17', callback=lambda self: self.get_currency_callback(),
                                                  format_callback=lambda self, value: value)
    }
  
  _global_role = GlobalRole(
    permissions=[
      # @todo We will se if read permission is required by the public audience!
      orm.ActionPermission('23', [orm.Action.build_key('23', 'create'),
                                  orm.Action.build_key('23', 'update'),
                                  orm.Action.build_key('23', 'prepare')], True,
                           'action.key_id_str not in ["cron_generate_feedback_stats"] and not account._is_guest and entity._original.key_root == account.key'),
      orm.ActionPermission('23', [orm.Action.build_key('23', 'read')], True,
                           'action.key_id_str not in ["cron", "cron_generate_feedback_stats"] and not account._is_guest and entity._original.root_entity._original.state == "active"'),
      orm.ActionPermission('23', [orm.Action.build_key('23', 'cron_generate_feedback_stats')], True, 'account._is_taskqueue or account._is_cron or account._root_admin'),
      orm.FieldPermission('23', ['_feedback'], True, True, 'account._is_taskqueue or account._is_cron or account._root_admin'),
      orm.FieldPermission('23', ['name', 'logo', '_content', '_plugin_group', '_records'], True, True,
                          'action.key_id_str not in ["cron", "cron_generate_feedback_stats"] and not account._is_guest and entity._original.key_root == account.key'),
      orm.FieldPermission('23', ['_feedback'], True, True, 'account._is_taskqueue and action.key_id_str == "cron"'),
      orm.FieldPermission('23', ['name', 'logo', '_currency', '_feedback'], False, True,
                          'action.key_id_str not in ["cron", "cron_generate_feedback_stats"] and not account._is_guest and entity._original.root_entity._original.state == "active"'),
      orm.FieldPermission('23', ['_plugin_group'], False, False,
                          'action.key_id_str not in ["cron", "cron_generate_feedback_stats"] and not account._is_guest and (entity._original.key_root == account.key or entity._original.root_entity._original.state != "active")')
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
            Set(cfg={'d': {'output.entity': '_seller'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('23', 'cron_generate_feedback_stats'),
      arguments={
        'cursor': orm.SuperStringProperty(),
      },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            SellerCronGenerateFeedbackStats(cfg={})
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            CallbackExec(),
            Set(cfg={'d': {'output.entity': '_seller'}})
            ]
          )
        ]
      )
    ]

  def get_notified_followers_count_callback(self):
    Collection = orm.Model._lookup_model('18') # @todo import or this
    key = 'get_notified_followers_count_%s' % self.key.urlsafe()
    already = mem.get(key)
    if already is None:
      already = Collection.query(Collection.sellers == self.key, Collection.notify == True).count()
      mem.set(key, already, settings.CACHE_TIME_NOTIFIED_FOLLOWERS_COUNT)
    return already

  def get_followers_count_callback(self):
    Collection = orm.Model._lookup_model('18') # @todo import or this
    key = 'get_followers_count_%s' % self.key.urlsafe()
    already = mem.get(key)
    if already is None:
      already = Collection.query(Collection.sellers == self.key).count()
      mem.set(key, already, settings.CACHE_TIME_FOLLOWERS_COUNT)
    return already

 
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
    account_key = input.get('account')
    return cls.build_key('seller', parent=account_key)
