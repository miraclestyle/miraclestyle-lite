# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import time
import datetime

from app import ndb, util
from app.srv import event, log, nav, rule  # @todo We need event import for event.Action.build_key. Is there a workaround?
from app.plugins import log as plugin_log
from app.plugins import callback as plugin_callback


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
    self.context.tmp['log_write'] = plugin_log.Write(static_arguments={}, dynamic_arguments={})  # We use log plugin for logging. @todo Decide if this this is optimal solution!
    self.context.tmp['callback_exec'] = plugin_callback.Exec(static_data={}, dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})  # We use callback plugin for triggering notifications. @todo Decide if this this is optimal solution!
    while self.config.state == 'active':
      iterations -= 1
      runner = getattr(self, self.__get_next_operation())
      if runner:
        ndb.transaction(runner, xg=True)
      time.sleep(1.5)
      if iterations < 1:
        util.logger('Stopped iteration at %s' % iterations)  # @todo Probably to be removed?!
        break


class DomainSetup(Setup):
  
  @classmethod
  def create_domain_notify_message_recievers(cls, entity, user):
    primary_contact = entity.primary_contact.get()
    user = ndb.Key('0', int(primary_contact.key_id_str)).get()
    return [user._primary_email]
  
  def execute_init(self):
    config_input = self.config.configuration_input
    self.config.next_operation = 'create_domain'
    self.config.next_operation_input = {'name': config_input.get('domain_name'),
                                        'logo': config_input.get('domain_logo')}
    self.config.put()
  
  def execute_create_domain(self):
    config_input = self.config.next_operation_input
    Domain = self.context.models['6']
    entity = Domain(name=config_input.get('name'),
                    state='active',
                    logo=config_input.get('logo'))
    entity.put()
    # We use log plugin for logging. @todo Decide if this this is optimal solution!
    self.context.log_entities.append((entity, ))
    self.context.tmp['log_write'].run(self.context)
    self.config.next_operation = 'create_domain_role'
    self.config.next_operation_input = {'domain_key': entity.key}
    self.config.put()
  
  def execute_create_domain_role(self):
    config_input = self.config.next_operation_input
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
        permissions.append(rule.ActionPermission(kind=obj.get_kind(),
                                                 actions=actions,
                                                 executable=True,
                                                 condition='True'))
      props = obj.get_fields()
      prop_names = []
      for prop_name, prop in props.items():
        prop_names.append(prop_name)
      permissions.append(rule.FieldPermission(obj.get_kind(), prop_names, True, True, 'True'))
    entity = rule.DomainRole(namespace=namespace, id='admin', name='Administrators', permissions=permissions)
    entity.put()
    # We use log plugin for logging. @todo Decide if this this is optimal solution!
    self.context.log_entities.append((entity, ))
    self.context.tmp['log_write'].run(self.context)
    self.config.next_operation = 'create_widget_step_1'
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': entity.key}
    self.config.put()
  
  def execute_create_widget_step_1(self):
    config_input = self.config.next_operation_input
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    role_key = config_input.get('role_key')
    entities = [nav.Widget(id='system_search',
                           namespace=namespace,
                           name='Search',
                           role=role_key,
                           search_form=True,
                           filters=[]),
                nav.Widget(id='system_marketing',
                           namespace=namespace,
                           name='Marketing',
                           role=role_key,
                           search_form=False,
                           filters=[nav.Filter(name='Catalogs', kind='35')]),
                nav.Widget(id='system_security',
                           namespace=namespace,
                           name='Security',
                           role=role_key,
                           search_form=False,
                           filters=[nav.Filter(name='Roles', kind='60'),
                                    nav.Filter(name='Users', kind='8')])]
    for i, entity in enumerate(entities):
      entity.sequence = i
    ndb.put_multi(entities)
    # We use log plugin for logging. @todo Decide if this this is optimal solution!
    for entity in entities:
      self.context.log_entities.append((entity, ))
    self.context.tmp['log_write'].run(self.context)
    self.config.next_operation = 'create_widget_step_2'
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': role_key,
                                        'sequence': i}
    self.config.put()
  
  def execute_create_widget_step_2(self):
    config_input = self.config.next_operation_input
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    role_key = config_input.get('role_key')
    sequence = config_input.get('sequence')
    entities = [nav.Widget(id='system_user_interface',
                           namespace=namespace,
                           name='User Interface',
                           role=role_key,
                           search_form=False,
                           filters=[nav.Filter(name='Menu Widgets', kind='62')]),
                nav.Widget(id='system_notifications',
                           namespace=namespace,
                           name='Notifications',
                           role=role_key,
                           search_form=False,
                           filters=[nav.Filter(name='Templates', kind='61')])]
    for i, entity in enumerate(entities):
      entity.sequence = (i+1) + sequence
    ndb.put_multi(entities)
    # We use log plugin for logging. @todo Decide if this this is optimal solution!
    for entity in entities:
      self.context.log_entities.append((entity, ))
    self.context.tmp['log_write'].run(self.context)
    self.config.next_operation = 'create_domain_user'
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': role_key}
    self.config.put()
  
  def execute_create_domain_user(self):
    config_input = self.config.next_operation_input
    user = self.config.parent_entity
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    entity = rule.DomainUser(namespace=namespace, id=user.key_id_str,
                             name='Administrator', state='accepted',
                             roles=[config_input.get('role_key')])  # Previous name property value was: user._primary_email
    entity.put()
    user.domains.append(domain_key)
    user.put()
    # We use log plugin for logging. @todo Decide if this this is optimal solution!
    self.context.log_entities.extend([(entity, ), (user, )])
    self.context.tmp['log_write'].run(self.context)
    self.config.next_operation = 'add_domain_primary_contact'
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'user_key': entity.key}
    self.config.put()
  
  def execute_add_domain_primary_contact(self):
    config_input = self.config.next_operation_input
    domain_key = config_input.get('domain_key')
    entity = domain_key.get()
    entity.primary_contact = config_input.get('user_key')
    entity.put()
    # We use log plugin for logging. @todo Decide if this this is optimal solution!
    self.context.log_entities.append((entity, ))
    self.context.tmp['log_write'].run(self.context)
    CustomTemplate = self.context.models['59']
    custom_notify = CustomTemplate(outlet='send_mail',
                                   message_subject='Your Application "{{entity.name}}" has been sucessfully created.',
                                   message_body='Your application has been created. Check your apps page (this message can be changed) app.srv.notify.py #L-232. Thanks.',
                                   message_recievers=self.create_domain_notify_message_recievers)
    self.context.tmp['caller_entity'] = entity
    self.context.tmp['caller_user'] = self.context.user
    custom_notify.run(self.context)
    # We use callback plugin for triggering notifications. @todo Decide if this this is optimal solution!
    self.context.tmp['callback_exec'].run(self.context)
    self.config.state = 'completed'
    self.config.put()


register_system_setup(('setup_domain', DomainSetup))


class Install(ndb.BaseModel):
  
  def run(self, context):
    config = context.entities['57']
    context.user = config.parent_entity
    SetupClass = get_system_setup(config.setup)
    setup = SetupClass(config, context)
    setup.run()


class CronInstall(ndb.BaseModel):
  
  def run(self, context):
    time_difference = datetime.datetime.now()-datetime.timedelta(minutes=15)
    configurations = context.model.query(context.model.state == 'active', context.model.updated < time_difference).fetch(50)
    for config in configurations:
      context.user = config.parent_entity
      SetupClass = get_system_setup(config.setup)
      setup = SetupClass(config, context)
      setup.run()
