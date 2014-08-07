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
    '_country': orm.SuperStorageStructuredProperty('15', autoload=True, storage='reference',
                                                   storage_config={'target_field': 'country'},
                                                   updateable=False, deleteable=False),
    '_region': orm.SuperStorageStructuredProperty('16', autoload=True, storage='reference',
                                                  storage_config={'target_field': 'region'},
                                                  updateable=False, deleteable=False)
  }


class Addresses(orm.BaseModel):
  
  _kind = 77
  
  addresses = orm.SuperLocalStructuredProperty(Address, '1', repeated=True)
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('77')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('77', [orm.Action.build_key('77', 'update'),
                                  orm.Action.build_key('77', 'read')], True, 'entity._original.key_parent == user.key and not user._is_guest'),
      orm.FieldPermission('77', ['addresses', '_records'], True, True, 'entity._original.key_parent == user.key and not user._is_guest')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('77', 'update'),
      arguments={
        'user': orm.SuperKeyProperty(kind='0', required=True),
        'addresses': orm.SuperLocalStructuredProperty(Address, repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_addresses.addresses': 'input.addresses'}}),
            AddressesUpdateSet(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_addresses'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('77', 'read'),
      arguments={
        'user': orm.SuperKeyProperty(kind='0', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_addresses'}})
            ]
          )
        ]
      )
    ]
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    user_key = input.get('user')
    return cls.build_key(user_key._id_str, parent=user_key)


class Collection(orm.BaseModel):
  
  _kind = 10
  
  notify = orm.SuperBooleanProperty('1', required=True, default=False)
  domains = orm.SuperKeyProperty('2', kind='6', repeated=True)
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('10'),
    '_domains': orm.SuperStorageStructuredProperty('6', autoload=False, storage='reference',
                                                   repeated=True, updateable=False, deleteable=False,
                                                   storage_config={'callback': lambda self: orm.get_multi_async([domain_key for domain_key in self.domains]),
                                                                    # This format_callback is here, because inside entities, there can always be Nones.
                                                                    # It is possible that we will have to make this more convinient, because we use same functionality on many places.
                                                                   'format_callback': lambda self, entities: orm.get_async_results(entities)})
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('10', [orm.Action.build_key('10', 'update'),
                                  orm.Action.build_key('10', 'read')], True, 'entity._original.key_parent == user.key and not user._is_guest'),
      orm.FieldPermission('10', ['notify', 'domains', '_records', '_domains.name', '_domains.logo'], True, True, 'entity._original.key_parent == user.key and not user._is_guest')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('10', 'update'),
      arguments={
        'user': orm.SuperKeyProperty(kind='0', required=True),
        'notify': orm.SuperBooleanProperty(default=True),
        'domains': orm.SuperKeyProperty(kind='6', repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_collection.notify': 'input.notify', '_collection.domains': 'input.domains'}}),
            RulePrepare(cfg={'skip_user_roles': True}),
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
      key=orm.Action.build_key('10', 'read'),
      arguments={
        'user': orm.SuperKeyProperty(kind='0', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_collection'}})
            ]
          )
        ]
      )
    ]
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    user_key = input.get('user')
    return cls.build_key(user_key._id_str, parent=user_key)
