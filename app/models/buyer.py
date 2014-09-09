# -*- coding: utf-8 -*-
'''
Created on May 18, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings
from app.models import auth
from app.models.base import *
from app.plugins.base import *
from app.plugins.buyer import *


class Address(orm.BaseExpando):
  
  _kind = 9
  
  _use_rule_engine = False
  
  internal_id = orm.SuperStringProperty('1', required=True, indexed=False)  # md5 hash => <timestamp>-<random_str>-<name>-<city>-<postal code>-<street>-<default_shipping>-<default_billing>
  name = orm.SuperStringProperty('2', required=True, indexed=False)
  country = orm.SuperKeyProperty('3', kind='15', required=True, indexed=False)
  city = orm.SuperStringProperty('4', required=True, indexed=False)
  postal_code = orm.SuperStringProperty('5', required=True, indexed=False)
  street = orm.SuperStringProperty('6', required=True, indexed=False)
  default_shipping = orm.SuperBooleanProperty('7', required=True, default=True, indexed=False)
  default_billing = orm.SuperBooleanProperty('8', required=True, default=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'region': orm.SuperKeyProperty('9', kind='16'),
    'email': orm.SuperStringProperty('10'),
    'telephone': orm.SuperStringProperty('11')
    }
  
  _virtual_fields = {
    '_country': orm.SuperReferenceStructuredProperty('15', autoload=True, target_field='country'),
    '_region': orm.SuperReferenceStructuredProperty('16', autoload=True, target_field='region')
  }


class Buyer(orm.BaseModel):
  
  _kind = 77
  
  addresses = orm.SuperLocalStructuredProperty(Address, '1', repeated=True)
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('77')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('77', [orm.Action.build_key('77', 'update'),
                                  orm.Action.build_key('77', 'read')], True, 'entity._original.key_parent == account.key and not account._is_guest'),
      orm.FieldPermission('77', ['addresses', '_records'], True, True, 'entity._original.key_parent == account.key and not account._is_guest')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('77', 'update'),
      arguments={
        'account': orm.SuperKeyProperty(kind='0', required=True),
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
            RulePrepare(cfg={'skip_account_roles': True}),
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
      key=orm.Action.build_key('77', 'read'),
      arguments={
        'account': orm.SuperKeyProperty(kind='0', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_account_roles': True}),
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
