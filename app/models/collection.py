# -*- coding: utf-8 -*-
'''
Created on May 18, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models import *
from app.plugins import *


class Collection(orm.BaseExpando):
  
  _kind = 18
  
  notify = orm.SuperBooleanProperty('1', required=True, default=False)
  accounts = orm.SuperKeyProperty('2', kind='11', repeated=True)  # @todo Or we can go straight to Seller model here, and use it's keys?
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('18'),
    '_sellers': orm.SuperReferenceStructuredProperty('11', autoload=False,
                                                     callback=lambda self: orm.get_multi_async([orm.Key(account_key._id_str, parent=account_key) for account_key in self.accounts]),
                                                     format_callback=lambda self, entities: orm.get_async_results(entities))
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('18', [orm.Action.build_key('18', 'update'),
                                  orm.Action.build_key('18', 'read')], True, 'entity._original.key_parent == account.key and not account._is_guest'),
      orm.FieldPermission('18', ['notify', 'accounts', '_records', '_sellers.name', '_sellers.logo'], True, True, 'entity._original.key_parent == account.key and not account._is_guest')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('18', 'update'),
      arguments={
        'account': orm.SuperKeyProperty(kind='11', required=True),
        'notify': orm.SuperBooleanProperty(default=True),
        'accounts': orm.SuperKeyProperty(kind='11', repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_collection.notify': 'input.notify', '_collection.accounts': 'input.accounts'}}),
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
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    account_key = input.get('account')
    return cls.build_key(account_key._id_str, parent=account_key)
