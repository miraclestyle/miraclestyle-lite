# -*- coding: utf-8 -*-
'''
Created on May 18, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from backend import orm, settings

from backend.models.base import *
from backend.plugins.base import *

from backend.models.location import *
from backend.plugins.buyer import *

__all__ = ['Buyer']


class Buyer(orm.BaseExpando):
  
  _kind = 19
  
  addresses = orm.SuperLocalStructuredProperty(Address, '1', repeated=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('19')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('19', [orm.Action.build_key('19', 'update'),
                                  orm.Action.build_key('19', 'read')], True,
                           'not account._is_guest and entity._original.key_root == account.key'),
      orm.FieldPermission('19', ['addresses', '_records'], True, True,
                          'not account._is_guest and entity._original.key_root == account.key')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('19', 'update'),
      arguments={
        'account': orm.SuperKeyProperty(kind='11', required=True),
        'addresses': orm.SuperLocalStructuredProperty(Address, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_buyer.addresses': 'input.addresses'}}),
            BuyerUpdateSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_buyer'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('19', 'read'),
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
            Set(cfg={'d': {'output.entity': '_buyer'}})
            ]
          )
        ]
      )
    ]
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    account_key = input.get('account')
    return cls.build_key('buyer', parent=account_key)
