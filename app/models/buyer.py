# -*- coding: utf-8 -*-
'''
Created on May 18, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models import *
from app.plugins import *


class Buyer(orm.BaseExpando):
  
  _kind = 19
  
  addresses = orm.SuperLocalStructuredProperty('14', '1', repeated=True)  # @todo It used to be Address. Is this ok!?
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('19')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('19', [orm.Action.build_key('19', 'update'),
                                  orm.Action.build_key('19', 'read')], True, 'entity._original.key_parent == account.key and not account._is_guest'),
      orm.FieldPermission('19', ['addresses', '_records'], True, True, 'entity._original.key_parent == account.key and not account._is_guest')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('19', 'update'),
      arguments={
        'account': orm.SuperKeyProperty(kind='6', required=True),
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
        'account': orm.SuperKeyProperty(kind='6', required=True),
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
    return cls.build_key(account_key._id_str, parent=account_key)
