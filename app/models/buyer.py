# -*- coding: utf-8 -*-
'''
Created on May 18, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.models import auth
from app.models.base import *
from app.plugins.base import *
from app.plugins import buyer


class Address(ndb.BaseExpando):
  
  _kind = 9
  
  internal_id = ndb.SuperStringProperty('1', required=True, indexed=False)  # md5 hash => <timestamp>-<random_str>-<name>-<city>-<postal code>-<street>-<default_shipping>-<default_billing>
  name = ndb.SuperStringProperty('2', required=True, indexed=False)
  country = ndb.SuperKeyProperty('3', kind='15', required=True, indexed=False)
  city = ndb.SuperStringProperty('4', required=True, indexed=False)
  postal_code = ndb.SuperStringProperty('5', required=True, indexed=False)
  street = ndb.SuperStringProperty('6', required=True, indexed=False)
  default_shipping = ndb.SuperBooleanProperty('7', required=True, default=True, indexed=False)
  default_billing = ndb.SuperBooleanProperty('8', required=True, default=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'region': ndb.SuperKeyProperty('9', kind='16'),
    'email': ndb.SuperStringProperty('10'),
    'telephone': ndb.SuperStringProperty('11')
    }
  
  _virtual_fields = {
    '_country': ndb.SuperStringProperty(),
    '_region': ndb.SuperStringProperty()
    }


class Addresses(ndb.BaseModel):
  
  _kind = 77
  
  addresses = ndb.SuperLocalStructuredProperty(Address, '1', repeated=True)
  
  _virtual_fields = {
    '_records': SuperLocalStructuredRecordProperty('10', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('77', [Action.build_key('77', 'update'),
                              Action.build_key('77', 'read'),
                              Action.build_key('77', 'read_records')], True, 'context.entity.key_parent == context.user.key and not context.user._is_guest'),
      FieldPermission('77', ['addresses', '_records'], True, True, 'context.entity.key_parent == context.user.key and not context.user._is_guest')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('77', 'update'),
      arguments={
        'user': ndb.SuperKeyProperty(kind='0', required=True),
        'addresses': ndb.SuperLocalStructuredProperty(Address, repeated=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            buyer.AddressRead(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Set(cfg={'d': {'entities.77.addresses': 'input.addresses'}}),
            buyer.AddressSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RecordWrite(cfg={'paths': ['entities.77']}),
            Set(cfg={'d': {'output.entity': 'entities.77'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('77', 'read'),
      arguments={
        'user': ndb.SuperKeyProperty(kind='0', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            buyer.AddressRead(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Set(cfg={'d': {'output.entity': 'entities.77'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('77', 'read_records'),
      arguments={
        'user': ndb.SuperKeyProperty(kind='0', required=True),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            buyer.AddressRead(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            RecordRead(cfg={'page': settings.RECORDS_PAGE}),
            Set(cfg={'d': {'output.entity': 'entities.77',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}})
            ]
          )
        ]
      )
    ]


class Collection(ndb.BaseModel):
  
  _kind = 10
  
  notify = ndb.SuperBooleanProperty('1', required=True, default=False)
  domains = ndb.SuperKeyProperty('2', kind='6', repeated=True)
  
  _virtual_fields = {
    '_records': SuperLocalStructuredRecordProperty('10', repeated=True),
    '_domains': ndb.SuperLocalStructuredProperty(auth.Domain, repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('10', [Action.build_key('10', 'update'),
                              Action.build_key('10', 'read'),
                              Action.build_key('10', 'read_records')], True, 'context.entity.key_parent == context.user.key and not context.user._is_guest'),
      FieldPermission('10', ['notify', 'domains', '_records', '_domains'], True, True, 'context.entity.key_parent == context.user.key and not context.user._is_guest')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('10', 'update'),
      arguments={
        'user': ndb.SuperKeyProperty(kind='0', required=True),
        'notify': ndb.SuperBooleanProperty(default=True),
        'domains': ndb.SuperKeyProperty(kind='6', repeated=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            buyer.CollectionRead(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Set(cfg={'d': {'entities.10.notify': 'input.notify', 'entities.10.domains': 'input.domains'}})
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RecordWrite(cfg={'paths': ['entities.10']}),
            Set(cfg={'d': {'output.entity': 'entities.10'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('10', 'read'),
      arguments={
        'user': ndb.SuperKeyProperty(kind='0', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            buyer.CollectionRead(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Set(cfg={'d': {'output.entity': 'entities.10'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('10', 'read_records'),
      arguments={
        'user': ndb.SuperKeyProperty(kind='0', required=True),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            buyer.CollectionRead(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            RecordRead(cfg={'page': settings.RECORDS_PAGE}),
            Set(cfg={'d': {'output.entity': 'entities.10',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}})
            ]
          )
        ]
      )
    ]
