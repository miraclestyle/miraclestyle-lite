# -*- coding: utf-8 -*-
'''
Created on May 18, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import orm
import settings
from plugins.base import *
from models.location import *

__all__ = ['Buyer', 'BuyerAddress', 'BuyerLocation']


class BuyerLocation(orm.BaseExpando):
  
  _kind = 121
  
  reference = orm.SuperKeyProperty('1', kind='14', required=True, indexed=False)
  name = orm.SuperStringProperty('2', required=True, indexed=False)
  country = orm.SuperStringProperty('3', required=True, indexed=False)
  country_code = orm.SuperStringProperty('4', required=True, indexed=False)
  city = orm.SuperStringProperty('5', required=True, indexed=False)
  postal_code = orm.SuperStringProperty('6', required=True, indexed=False)
  street = orm.SuperStringProperty('7', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'region': orm.SuperStringProperty('8'),
    'region_code': orm.SuperStringProperty('9')
    }


class BuyerAddress(orm.BaseExpando):
  
  _kind = 14
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  country = orm.SuperKeyProperty('2', kind='12', required=True, indexed=False)
  region = orm.SuperKeyProperty('6', kind='13', required=True, indexed=False)
  city = orm.SuperStringProperty('3', required=True, indexed=False)
  postal_code = orm.SuperStringProperty('4', required=True, indexed=False)
  street = orm.SuperStringProperty('5', required=True, indexed=False)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_country': orm.SuperReferenceProperty(target_field='country'),
    '_region': orm.SuperReferenceProperty(target_field='region')
  }
  
  def get_location(self):
    location = self
    location_country = location.country.get()
    location_region = location.region.get()
    return BuyerLocation(reference=self.key,
                         name=location.name,
                         country=location_country.name,
                         country_code=location_country.code,
                         region=location_region.name,
                         region_code=location_region.code,
                         city=location.city,
                         postal_code=location.postal_code,
                         street=location.street)


class Buyer(orm.BaseExpando):
  
  _kind = 19
  
  addresses = orm.SuperLocalStructuredProperty(BuyerAddress, '1', repeated=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('19')
    }
  
  _global_role = orm.GlobalRole(
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
        'addresses': orm.SuperLocalStructuredProperty(BuyerAddress, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_buyer.addresses': 'input.addresses'}}),
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
