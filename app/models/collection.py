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


class Collection(orm.BaseModel):
  
  _kind = 10
  
  notify = orm.SuperBooleanProperty('1', required=True, default=False)
  accounts = orm.SuperKeyProperty('2', kind='6', repeated=True)
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('10'),
    '_domains': orm.SuperReferenceStructuredProperty('6', autoload=False,
                                                     callback=lambda self: orm.get_multi_async([domain_key for domain_key in self.domains]),
                                                     format_callback=lambda self, entities: orm.get_async_results(entities))
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('10', [orm.Action.build_key('10', 'update'),
                                  orm.Action.build_key('10', 'read')], True, 'entity._original.key_parent == account.key and not account._is_guest'),
      orm.FieldPermission('10', ['notify', 'domains', '_records', '_domains.name', '_domains.logo'], True, True, 'entity._original.key_parent == account.key and not account._is_guest')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('10', 'update'),
      arguments={
        'account': orm.SuperKeyProperty(kind='6', required=True),
        'notify': orm.SuperBooleanProperty(default=True),
        'accounts': orm.SuperKeyProperty(kind='6', repeated=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_collection.notify': 'input.notify', '_collection.domains': 'input.domains'}}),
            RulePrepare(cfg={'skip_account_roles': True}),
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
        'account': orm.SuperKeyProperty(kind='6', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_account_roles': True}),
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
