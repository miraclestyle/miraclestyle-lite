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

  documents = orm.SuperLocalStructuredProperty(SellerContentDocument, '1', repeated=True)

  @classmethod
  def prepare_key(cls, **kwargs):
    return cls.build_key('_content', parent=kwargs.get('parent'))

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
    return cls.build_key('_feedback', parent=kwargs.get('parent'))

  def prepare(self, **kwargs):
    self.key = self.prepare_key(**kwargs)


class SellerPluginContainer(orm.BaseModel):

  _kind = 22

  _use_rule_engine = False

  plugins = orm.SuperPluginStorageProperty(('107', '113', '117', '126', '108', '109'), '1', required=True, default=[], compressed=False)

  @classmethod
  def prepare_key(cls, **kwargs):
    return cls.build_key('_plugin_group', parent=kwargs.get('parent'))

  def prepare(self, **kwargs):
    self.key = self.prepare_key(**kwargs)


class Seller(orm.BaseExpando):

  _kind = 23

  _use_memcache = True

  name = orm.SuperStringProperty('1', required=True)
  logo = orm.SuperImageLocalStructuredProperty(orm.Image, '2', required=True)

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

  def condition_not_guest_and_owner(action, account, entity, **kwargs):
    return action.key_id_str not in ("cron_generate_feedback_stats",) and not account._is_guest and entity._original.key_root == account.key

  def condition_not_guest_and_owner_active(action, account, entity, **kwargs):
    return action.key_id_str not in ("cron_generate_feedback_stats",) and not account._is_guest and entity._original.root_entity._original.state == "active"

  def condition_taskqueue_or_cron_or_root(account, **kwargs):
    return account._is_taskqueue or account._is_cron or account._root_admin

  _permissions = [
      orm.ExecuteActionPermission(('create', 'update', 'prepare'), condition_not_guest_and_owner),
      orm.ExecuteActionPermission('read', condition_not_guest_and_owner_active),
      orm.ExecuteActionPermission('cron_generate_feedback_stats', condition_taskqueue_or_cron_or_root),
      orm.ReadFieldPermission(('_plugin_group'), condition_not_guest_and_owner),
      orm.ReadFieldPermission(('name', 'logo', '_content', '_currency', '_feedback', '_follower_count', '_notified_followers_count'), condition_not_guest_and_owner_active),
      orm.WriteFieldPermission('_feedback', condition_taskqueue_or_cron_or_root),
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
          id='update',
          arguments={
              'account': orm.SuperKeyProperty(kind='11', required=True),
              'name': orm.SuperStringProperty(required=True),
              'logo': orm.SuperImageLocalStructuredProperty(orm.Image,
                                                            upload=True,
                                                            process_config={'measure': False,
                                                                            'transform': True,
                                                                            'width': 240,
                                                                            'height': 100,
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
          id='cron_generate_feedback_stats',
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
                      SellerCronGenerateFeedbackStats()
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
    Collection = orm.Model._lookup_model('18')
    key = 'get_notified_followers_count_%s' % self.key.urlsafe()
    count = tools.mem_get(key)
    if count is None:
      count = Collection.query(Collection.sellers == self.key, Collection.notify == True).count()
      tools.mem_set(key, count, settings.CACHE_TIME_NOTIFIED_FOLLOWERS_COUNT)
    return count

  def get_followers_count_callback(self):
    Collection = orm.Model._lookup_model('18')
    key = 'get_followers_count_%s' % self.key.urlsafe()
    count = tools.mem_get(key)
    if count is None:
      count = Collection.query(Collection.sellers == self.key).count()
      tools.mem_set(key, count, settings.CACHE_TIME_FOLLOWERS_COUNT)
    return count

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
