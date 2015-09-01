# -*- coding: utf-8 -*-
'''
Created on May 18, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import orm
import settings
import notifications
from plugins.base import *
from plugins.collection import *

__all__ = ['Collection']


class Collection(orm.BaseExpando):

  _kind = 18

  notify = orm.SuperBooleanProperty('1', required=True, default=False)
  sellers = orm.SuperKeyProperty('2', kind='23', repeated=True)

  _default_indexed = False

  _virtual_fields = {
      '_records': orm.SuperRecordProperty('18'),
      '_sellers': orm.SuperReferenceStructuredProperty('23', autoload=False, repeated=True,
                                                       callback=lambda self: orm.get_multi_async(self.sellers),
                                                       format_callback=lambda self, entities: self.get_asynced_sellers(entities))
  }

  def condition_not_guest_and_owner(account, entity, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key

  def condition_taskqueue_or_cron_or_root(account, **kwargs):
    return account._is_taskqueue or account._is_cron or account._root_admin

  def condition_not_guest(account, **kwargs):
    return not account._is_guest

  _permissions = [
      orm.ExecuteActionPermission(('update', 'read'), condition_not_guest_and_owner),
      orm.ExecuteActionPermission('cron_notify', condition_taskqueue_or_cron_or_root),
      orm.ReadFieldPermission('_sellers', condition_not_guest),
      orm.ReadFieldPermission(('notify', 'sellers', '_sellers.name', '_sellers.logo'), condition_not_guest_and_owner),
      orm.WriteFieldPermission(('notify', 'sellers', '_records', '_sellers.name', '_sellers.logo'), condition_not_guest_and_owner)
  ]

  _actions = [
      orm.Action(
          id='update',
          arguments={
              'account': orm.SuperKeyProperty(kind='11', required=True),
              'notify': orm.SuperBooleanProperty(default=True),
              'sellers': orm.SuperKeyProperty(kind='23', repeated=True),
              'read_arguments': orm.SuperJsonProperty()
          },
          _plugin_groups=[
              orm.PluginGroup(
                  plugins=[
                      Context(),
                      Read(),
                      Set(cfg={'d': {'_collection.notify': 'input.notify', '_collection.sellers': 'input.sellers'}}),
                      RulePrepare(),
                      RuleExec()
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      Write(),
                      Set(cfg={'d': {'output.entity': '_collection'}})
                  ]
              )
          ]
      ),
      orm.Action(
          id='cron_notify',
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
                      CollectionCronNotify(cfg={'age': settings.COLLECTION_CATALOG_AGE})
                  ]
              ),
              orm.PluginGroup(
                  transactional=True,
                  plugins=[
                      Notify(cfg={'condition': lambda recipient_account, **kwargs: recipient_account.state == "active",
                                  's': {'subject': notifications.COLLECTION_CATALOG_PUBLISH_SUBJECT,
                                        'body': notifications.COLLECTION_CATALOG_PUBLISH_BODY,
                                        'sender': settings.NOTIFY_EMAIL},
                                  'd': {'recipient': '_recipient._primary_email',
                                        'recipient_account': '_recipient',
                                        'discontinued_catalogs': '_discontinued_catalogs',
                                        'published_catalogs': '_published_catalogs'}}),
                      CallbackExec()
                  ]
              )
          ]
      ),
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
                      Set(cfg={'d': {'output.entity': '_collection'}})
                  ]
              )
          ]
      )
  ]

  def get_asynced_sellers(self, entities):
    orm.get_async_results(entities)
    return entities

  @classmethod
  def prepare_key(cls, input, **kwargs):
    return cls.build_key('collection', parent=input.get('account'))
