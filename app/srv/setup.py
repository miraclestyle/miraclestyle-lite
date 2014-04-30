# -*- coding: utf-8 -*-
'''
Created on Feb 17, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import time
import datetime

from app import ndb, util, settings
from app.srv import event, log, nav, rule, callback
from app.plugins import common
from app.plugins import rule as plugin_rule
from app.plugins import log as plugin_log
from app.plugins import callback as plugin_callback
from app.plugins import setup


class Configuration(ndb.BaseExpando):
  
  _kind = 57
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  configuration_input = ndb.SuperPickleProperty('3', required=True, compressed=False)
  setup = ndb.SuperStringProperty('4', required=True, indexed=False)
  state = ndb.SuperStringProperty('5', required=True, indexed=False)
  next_operation = ndb.SuperStringProperty('6', indexed=False)
  next_operation_input = ndb.SuperPickleProperty('7', indexed=False)
  
  _global_role = rule.GlobalRole(
    permissions=[
      rule.ActionPermission('57', event.Action.build_key('57-0').urlsafe(), True, "context.user._is_taskqueue"),
      rule.ActionPermission('57', event.Action.build_key('57-1').urlsafe(), True, "context.user._is_taskqueue")
      ]
    )
  
  _actions = {
    'install': event.Action(
      id='57-0',
      arguments={
        'key': ndb.SuperKeyProperty(required=True, kind='57')
        }
      ),
    'cron_install': event.Action(
      id='57-1',
      arguments={}
      )
    }
  
  _plugins = [
    common.Context(
      subscriptions=[
        event.Action.build_key('57-0'),
        event.Action.build_key('57-1')
        ]
      ),
    common.Prepare(
      subscriptions=[
        event.Action.build_key('57-1')
        ],
      domain_model=False
      ),
    common.Read(
      subscriptions=[
        event.Action.build_key('57-0')
        ]
      ),
    plugin_rule.Prepare(
      subscriptions=[
        event.Action.build_key('57-0'),
        event.Action.build_key('57-1')
        ],
      skip_user_roles=True,
      strict=False
      ),
    plugin_rule.Exec(
      subscriptions=[
        event.Action.build_key('57-0'),
        event.Action.build_key('57-1')
        ]
      ),
    setup.Install(
      subscriptions=[
        event.Action.build_key('57-0')
        ]
      ),
    setup.CronInstall(
      subscriptions=[
        event.Action.build_key('57-1')
        ]
      )
    ]
  
  
  """@classmethod
  def get_active_configurations(cls):
    time_difference = datetime.datetime.now()-datetime.timedelta(minutes=15)
    configurations = cls.query(cls.state == 'active', cls.updated < time_difference).fetch(50)
    return configurations
  
  
  @classmethod
  def cron_install(cls, context):
    
    context.rule.entity = cls()
    context.rule.skip_user_roles = True
    rule.Engine.run(context)
    
    if not rule.executable(context):
       raise rule.ActionDenied(context)
 
    configurations = Configuration.get_active_configurations()
    for configuration in configurations:
      context.auth.user = configuration.parent_entity
      configuration.run(context)
      
    return context

  
  @classmethod
  def install(cls, context):
    
    entity_key = context.input.get('key')
    entity = entity_key.get()
    
    context.rule.entity = entity
    context.rule.skip_user_roles = True
    rule.Engine.run(context)
    
    if not rule.executable(context):
       raise rule.ActionDenied(context)
    
    util.logger('Start configuration.run(context)')
    
    context.auth.user = entity.parent_entity
    
    entity.run(context)
    
    util.logger('End configuration.run(context)')
    
    return context
  
  def run(self, context):
    
    SetupClass = get_system_setup(self.setup)
    setup = SetupClass(self, context)
    
    iterations = 100
    while self.state == 'active':
       iterations -= 1
       setup.run() # keep runing until state is completed - upon failure, the task will be re-sent until its 100% submitted trough transaction
       time.sleep(1.5) # throughput demands one entity per sec, we will put 1.5
       
       # do not do infinite loops, this is just for tests now.
       if iterations < 1:
          util.logger('Stopped iteration at %s' % iterations)
          break"""
