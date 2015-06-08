# -*- coding: utf-8 -*-
'''
Created on May 18, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import orm
import settings
import notifications

from models.base import *
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
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('18', [orm.Action.build_key('18', 'update'),
                                  orm.Action.build_key('18', 'read')], True,
                           'not account._is_guest and entity._original.key_root == account.key'),
      orm.ActionPermission('18', [orm.Action.build_key('18', 'cron_notify')], True, 'account._is_taskqueue or account._is_cron or account._root_admin'),
      orm.FieldPermission('18', ['_sellers'], None, True, 'not account._is_guest'),
      orm.FieldPermission('18', ['notify', 'sellers', '_records', '_sellers.name', '_sellers.logo'], True, True,
                          'not account._is_guest and entity._original.key_root == account.key'),

      ]
    )

  _actions = [
    orm.Action(
      key=orm.Action.build_key('18', 'update'),
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
      key=orm.Action.build_key('18', 'cron_notify'),
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
            CollectionCronNotify(cfg={})
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Notify(cfg={'s': {'subject': notifications.COLLECTION_NOTIFY_SUBJECT,
                              'body': notifications.COLLECTION_NOTIFY_BODY,
                              'sender': settings.NOTIFY_EMAIL},
                        'd': {'recipient': '_recipient._primary_email',
                              'condition': '_recipient.state == "active"',
                              'discontinued_catalogs': '_all_discontinued_catalogs',
                              'published_catalogs': '_all_published_catalogs'}}),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('18', 'read'),
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
    account_key = input.get('account')
    return cls.build_key('collection', parent=account_key)
