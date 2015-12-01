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

  reference = orm.SuperKeyProperty('1', kind='14', required=False, indexed=False)
  name = orm.SuperStringProperty('2', required=True, indexed=False)
  country = orm.SuperStringProperty('3', required=True, indexed=False)
  country_code = orm.SuperStringProperty('4', required=True, indexed=False)
  region = orm.SuperStringProperty('5', required=True, indexed=False)
  region_code = orm.SuperStringProperty('6', required=True, indexed=False)
  city = orm.SuperStringProperty('7', required=True, indexed=False)
  postal_code = orm.SuperStringProperty('8', required=True, indexed=False)
  street = orm.SuperStringProperty('9', required=True, indexed=False)

  _default_indexed = False


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
      '_country': orm.SuperReferenceProperty(autoload=True, target_field='country'),
      '_region': orm.SuperReferenceProperty(autoload=True, target_field='region')
  }

  def get_location(self):
    return BuyerLocation(reference=self.key,
                         name=self.name,
                         country=self._country.name,
                         country_code=self._country.code,
                         region=self._region.name,
                         region_code=self._region.code,
                         city=self.city,
                         postal_code=self.postal_code,
                         street=self.street)


class Buyer(orm.BaseExpando):

  _kind = 19

  _use_memcache = False

  '''
  read:
    buyer_<account.id>
  '''

  READ_CACHE_POLICY = {'key': 'buyer', 'cache': ['account']}

  addresses = orm.SuperLocalStructuredProperty(BuyerAddress, '1', repeated=True)

  _default_indexed = False

  _virtual_fields = {
      '_records': orm.SuperRecordProperty('19')
  }

  def condition_not_guest_and_owner(account, entity, **kwargs):
    return not account._is_guest and entity._original.key_root == account.key

  _permissions = [
      orm.ExecuteActionPermission(('update', 'read'), condition_not_guest_and_owner),
      orm.ReadFieldPermission(('addresses'), condition_not_guest_and_owner),
      orm.WriteFieldPermission(('addresses', '_records'), condition_not_guest_and_owner)
  ]

  _actions = [
      orm.Action(
          id='update',
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
                      DeleteCache(cfg=READ_CACHE_POLICY),
                      Set(cfg={'d': {'output.entity': '_buyer'}})
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
                      GetCache(cfg=READ_CACHE_POLICY),
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
    return cls.build_key('buyer', parent=input.get('account'))
