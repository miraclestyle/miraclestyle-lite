# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import time
import datetime

from app import orm, util
from app.tools.base import callback_exec


__SYSTEM_SETUPS = {}

def get_system_setup(setup_name):
  global __SYSTEM_SETUPS
  return __SYSTEM_SETUPS.get(setup_name)

def register_system_setup(*setups):
  global __SYSTEM_SETUPS
  for setup in setups:
    __SYSTEM_SETUPS[setup[0]] = setup[1]


class Setup():
  
  def __init__(self, config, context):
    self.config = config
    self.context = context
  
  def __get_next_operation(self):
    if not self.config.next_operation:
      return 'execute_init'
    function = 'execute_%s' % self.config.next_operation
    util.logger('Running function %s' % function)  # @todo Probably to be removed?!
    return function
  
  def run(self):
    iterations = 100
    while self.config.state == 'active':
      iterations -= 1
      runner = getattr(self, self.__get_next_operation())
      if runner:
        orm.transaction(runner, xg=True)
      time.sleep(1.5)
      if iterations < 1:
        util.logger('Stopped iteration at %s' % iterations)  # @todo Probably to be removed?!
        break


class DomainSetup(Setup):
  
  @classmethod
  def create_domain_notify_message_recievers(cls, entity, user):
    primary_contact = entity.primary_contact.get()
    user = orm.Key('0', int(primary_contact.key_id_str)).get()
    return [user._primary_email]
  
  def execute_init(self):
    config_input = self.config.configuration_input
    self.config.next_operation = 'create_domain'
    self.config.next_operation_input = {'name': config_input.get('domain_name'),
                                        'logo': config_input.get('domain_logo')}
    self.config.write()
  
  def execute_create_domain(self):
    config_input = self.config.next_operation_input
    Domain = self.context.models['6']
    entity = Domain(name=config_input.get('name'),
                    state='active',
                    logo=config_input.get('logo'))
    entity._use_rule_engine = False
    entity.write({'agent': self.context.user.key, 'action': self.context.action.key})
    self.config.next_operation = 'create_domain_role'
    self.config.next_operation_input = {'domain_key': entity.key}
    self.config.write()
  
  def execute_create_domain_role(self):
    config_input = self.config.next_operation_input
    ActionPermission = self.context.models['79']
    FieldPermission = self.context.models['80']
    DomainRole = self.context.models['60']
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    permissions = []
    objects = [self.context.models['6'], self.context.models['60'], self.context.models['8'],
               self.context.models['62'], self.context.models['61'], self.context.models['35'],
               self.context.models['38'], self.context.models['39'], self.context.models['17'],
               self.context.models['15'], self.context.models['16'], self.context.models['19']]
    for obj in objects:
      if hasattr(obj, '_actions'):
        actions = []
        for action_instance in obj._actions:
          actions.append(action_instance.key)
        permissions.append(ActionPermission(model=obj.get_kind(),
                                            actions=actions,
                                            executable=True,
                                            condition='True'))
      props = obj.get_fields()
      prop_names = []
      for prop_name, prop in props.items():
        prop_names.append(prop_name)
      permissions.append(FieldPermission(obj.get_kind(), prop_names, True, True, 'True'))
    entity = DomainRole(namespace=namespace, id='admin', name='Administrators', permissions=permissions)
    entity._use_rule_engine = False
    entity.write({'agent': self.context.user.key, 'action': self.context.action.key})
    self.config.next_operation = 'create_widget_step_1'
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': entity.key}
    self.config.write()
  
  def execute_create_widget_step_1(self):
    config_input = self.config.next_operation_input
    Widget = self.context.models['62']
    Filter = self.context.models['65']
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    role_key = config_input.get('role_key')
    entities = [Widget(id='system_search',
                       namespace=namespace,
                       name='Search',
                       role=role_key,
                       search_form=True,
                       filters=[]),
                Widget(id='system_marketing',
                       namespace=namespace,
                       name='Marketing',
                       role=role_key,
                       search_form=False,
                       filters=[Filter(name='Catalogs', model='35')]),
                Widget(id='system_security',
                       namespace=namespace,
                       name='Security',
                       role=role_key,
                       search_form=False,
                       filters=[Filter(name='Roles', model='60'),
                                Filter(name='Users', model='8')])]
    for i, entity in enumerate(entities):
      entity._use_rule_engine = False
      entity.sequence = i
      entity._record_arguments = {'agent': self.context.user.key, 'action': self.context.action.key}
    orm.put_multi(entities)
    self.config.next_operation = 'create_widget_step_2'
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': role_key,
                                        'sequence': i}
    self.config.write()
  
  def execute_create_widget_step_2(self):
    config_input = self.config.next_operation_input
    Widget = self.context.models['62']
    Filter = self.context.models['65']
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    role_key = config_input.get('role_key')
    sequence = config_input.get('sequence')
    entities = [Widget(id='system_user_interface',
                       namespace=namespace,
                       name='User Interface',
                       role=role_key,
                       search_form=False,
                       filters=[Filter(name='Menu Widgets', model='62')]),
                Widget(id='system_notifications',
                       namespace=namespace,
                       name='Notifications',
                       role=role_key,
                       search_form=False,
                       filters=[Filter(name='Templates', model='61')])]
    for i, entity in enumerate(entities):
      entity._use_rule_engine = False
      entity.sequence = (i+1) + sequence
      entity._record_arguments = {'agent': self.context.user.key, 'action': self.context.action.key}
    orm.put_multi(entities)
    self.config.next_operation = 'create_domain_user'
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': role_key}
    self.config.write()
  
  def execute_create_domain_user(self):
    config_input = self.config.next_operation_input
    DomainUser = self.context.models['8']
    user = self.config.parent_entity
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    entity = DomainUser(namespace=namespace, id=user.key_id_str,
                        name='Administrator', state='accepted',
                        roles=[config_input.get('role_key')])  # Previous name property value was: user._primary_email
    entity._use_rule_engine = False
    entity.write({'agent': self.context.user.key, 'action': self.context.action.key})
    user.domains.append(domain_key)
    user._use_rule_engine = False
    user.write({'agent': self.context.user.key, 'action': self.context.action.key})
    self.config.next_operation = 'add_domain_primary_contact'
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'user_key': entity.key}
    self.config.write()
  
  def execute_add_domain_primary_contact(self):
    config_input = self.config.next_operation_input
    domain_key = config_input.get('domain_key')
    entity = domain_key.get()
    entity.primary_contact = config_input.get('user_key')
    entity._use_rule_engine = False
    entity.write({'agent': self.context.user.key, 'action': self.context.action.key})
    CustomTemplate = self.context.models['59']
    custom_notify = CustomTemplate(outlet='send_mail',
                                   message_subject='Your Application "{{entity.name}}" has been sucessfully created.',
                                   message_body='Your application has been created. Check your apps page (this message can be changed). Thanks.',
                                   message_recievers=self.create_domain_notify_message_recievers)
    kwargs = {}
    kwargs['caller_entity'] = entity
    kwargs['caller_user'] = self.context.user
    callbacks = custom_notify.run(**kwargs)
    for callback in callbacks:
      callback[1]['caller_user'] = self.context.user.key_urlsafe
      callback[1]['caller_action'] = self.context.action.key_urlsafe
    callback_exec('/task/io_engine_run', callbacks)
    self.config.state = 'completed'
    self.config.write()


register_system_setup(('setup_domain', DomainSetup))


class Install(orm.BaseModel):
  
  def run(self, context):
    config = context._configuration
    context.user = config.parent_entity
    SetupClass = get_system_setup(config.setup)
    setup = SetupClass(config, context)
    setup.run()


class CronInstall(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    elapsed_time = self.cfg.get('time', 10)
    limit = self.cfg.get('page', 50)
    time_difference = datetime.datetime.now()-datetime.timedelta(minutes=elapsed_time)
    configurations = context.model.query(context.model.state == 'active', context.model.updated < time_difference).fetch(limit=limit)
    for config in configurations:
      context.user = config.parent_entity
      SetupClass = get_system_setup(config.setup)
      setup = SetupClass(config, context)
      setup.run()
