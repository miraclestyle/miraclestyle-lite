# -*- coding: utf-8 -*-
'''
Created on May 18, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, settings

from app.models.base import *
from app.plugins.base import *


__all__ = ['Collection']


class Collection(orm.BaseExpando):
  
  _kind = 18
  
  notify = orm.SuperBooleanProperty('1', required=True, default=False)
  sellers = orm.SuperKeyProperty('2', kind='23', repeated=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('18'),
    '_sellers': orm.SuperReferenceStructuredProperty('11', autoload=False,
                                                     callback=lambda self: orm.get_multi_async(self.sellers),
                                                     format_callback=lambda self, entities: orm.get_async_results(entities))
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('18', [orm.Action.build_key('18', 'update'),
                                  orm.Action.build_key('18', 'read')], True,
                           'not account._is_guest and entity._original.key_root == account.key'),
      orm.FieldPermission('18', ['notify', 'sellers', '_records', '_sellers.name', '_sellers.logo'], True, True,
                          'not account._is_guest and entity._original.key_root == account.key')
      ]
    )
  
  # @todo beside update, we need to add action that allows you to append to "sellers" key-list
  # that must be a custom plugin probably because "Set" accomplish it
  # however with .read and then update combo it is possible without custom action
  # e.g. read => returns full object
  # then client can append to sellers the wanted key
  # and then send update.
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
    return cls.build_key('collection', parent=account_key)
