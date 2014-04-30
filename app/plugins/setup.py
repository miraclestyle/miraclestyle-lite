# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import time
import datetime

from app import ndb, settings
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


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
        ndb.transaction(runner, xg=True)
      time.sleep(1.5)
      if iterations < 1:
        util.logger('Stopped iteration at %s' % iterations)  # @todo Probably to be removed?!
        break


class DomainSetup(Setup):
  
  @classmethod
  def create_domain_notify_message_recievers(cls, entity, user):
    primary_contact = entity.primary_contact.get()
    return [primary_contact._primary_email]
  
  def execute_init(self):
    config_input = self.config.configuration_input
    self.config.next_operation_input = {'name': config_input.get('domain_name'), 
                                        'primary_contact': config_input.get('domain_primary_contact')}
    self.config.next_operation = 'create_domain'
    self.config.put()
  
  def execute_create_domain(self):
    input = self.config.configuration_input
    primary_contact = input.get('domain_primary_contact')
    from app.srv import auth
    entity = auth.Domain(state='active')
    # rule engine is not needed here because user cannot reach this if he cannot call Domain.create()
    entity.name = input.get('domain_name')
    entity.logo = input.get('domain_logo')
    entity.primary_contact = primary_contact
    entity.put()
    self.context.log.entities.append((entity,))
    log.Engine.run(self.context)
    self.config.next_operation_input = {'domain_key' : entity.key}
    self.config.next_operation = 'create_domain_role'
    self.config.put()
  
  def execute_create_domain_role(self):
    input = self.config.next_operation_input
    domain_key = input.get('domain_key')
    namespace = domain_key.urlsafe()
    permissions = []
    # from all objects specified here, the ActionPermission will be built. So the role we are creating
    # will have all action permissions - taken `_actions` per model
    from app.srv import auth, nav, notify, business, marketing, product
    objects = [auth.Domain, rule.DomainRole, rule.DomainUser, nav.Widget,
               notify.Template, notify.MailNotify, notify.HttpNotify,
               marketing.Catalog, marketing.CatalogImage, marketing.CatalogPricetag,
               product.Content, product.Instance, product.Template, product.Variant]
    for obj in objects:
      if hasattr(obj, '_actions'):
        actions = []
        for friendly_action_key, action_instance in obj._actions.items():
          actions.append(action_instance.key.urlsafe())
          permissions.append(rule.ActionPermission(kind=obj.get_kind(),
                                                   actions=actions,
                                                   executable=True,
                                                   condition='True'))
      props = obj.get_fields() # for every object, all fields get FieldPermission writable, visible, and - required which is based on prop._required
      prop_names = []
      for prop_name, prop in props.items():
        prop_names.append(prop_name)
        permissions.append(rule.FieldPermission(obj.get_kind(), prop_names, True, True, 'True'))
    role = rule.DomainRole(namespace=namespace, id='admin', name='Administrators', permissions=permissions)
    role.put()
    # context.log.entities.append((role, ))
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': role.key}
    self.config.next_operation = 'create_widget_step_1'
    self.config.put()
  
  def execute_create_widget_step_1(self):
    input = self.config.next_operation_input
    domain_key = input.get('domain_key')
    namespace = domain_key.urlsafe()
    role_key = input.get('role_key')
    to_put = [nav.Widget(id='system_marketing',
                         namespace=namespace,
                         name='Marketing',
                         role=role_key,
                         filters=[nav.Filter(name='Catalog', kind='35')]),
              nav.Widget(id='system_business',
                         namespace=namespace,
                         name='Business',
                         role=role_key,
                         filters=[nav.Filter(name='Companies', kind='44')]),
              nav.Widget(id='system_security',
                         namespace=namespace,
                         name='Security',
                         role=role_key,
                         filters=[nav.Filter(name='Roles', kind='60'),
                                  nav.Filter(name='Filter Groups', kind='62')])]
    for i, to in enumerate(to_put):
      to.sequence = i
    ndb.put_multi(to_put)
    for to in to_put:
      self.context.log.entities.append((to, ))
    log.Engine.run(self.context)
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': role_key,
                                        'sequence': i}
    self.config.next_operation = 'create_widget_step_2'
    self.config.put()
  
  def execute_create_widget_step_2(self):
    input = self.config.next_operation_input
    domain_key = input.get('domain_key')
    namespace = domain_key.urlsafe()
    role_key = input.get('role_key')
    sequence = input.get('sequence')
    to_put = [nav.Widget(id='system_app_users',
                         namespace=namespace,
                         name='App Users',
                         role=role_key,
                         filters=[nav.Filter(name='Users', kind='8')]),
              nav.Widget(id='system_notifications',
                         namespace=namespace,
                         name='Notifications',
                         role=role_key,
                         filters=[nav.Filter(name='Templates', kind='61')])]
    for i, to in enumerate(to_put):
      to.sequence = (i + 1) + sequence
    ndb.put_multi(to_put)
    for to in to_put:
      self.context.log.entities.append((to, ))
    log.Engine.run(self.context)
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': role_key}
    self.config.next_operation = 'create_domain_user'
    self.config.put()
  
  def execute_create_domain_user(self):
    input = self.config.next_operation_input
    user = self.config.parent_entity
    domain_key = input.get('domain_key')
    namespace = domain_key.urlsafe()
    domain_user = rule.DomainUser(namespace=namespace, id=user.key_id_str,
                                  name=user._primary_email, state='accepted',
                                  roles=[input.get('role_key')])
    domain_user.put()
    # context.log.entities.append((domain_user, ))
    self.config.next_operation = 'add_user_domain'
    self.config.next_operation_input = {'domain_key': domain_key}
    self.config.put()
  
  def execute_add_user_domain(self):
    input = self.config.next_operation_input
    user = self.config.parent_entity
    domain_key = input.get('domain_key')
    domain = domain_key.get()
    user.domains.append(domain_key)
    user.put()
    self.context.log.entities.append((user,))
    log.Engine.run(self.context)
    from app.srv import notify
    custom_notify = notify.CustomNotify(name='Send domain link after domain is completed',
                                        action=event.Action.build_key('57-0'),
                                        message_subject='Your Application "{{entity.name}}" has been sucessfully created.',
                                        message_sender=settings.NOTIFY_EMAIL,
                                        message_body='Your application has been created. Check your apps page (this message can be changed) app.srv.notify.py #L-232. Thanks.',
                                        message_recievers=self.create_domain_notify_message_recievers)
    context.caller_entity = domain
    context.caller_user = self.context.auth.user
    custom_notify.run(self.context)
    callback.Engine.run(self.context)
    self.config.state = 'completed'
    self.config.put()


class Install(event.Plugin):
  
  def run(self, context):
    config = context.entities['57']
    context.auth.user = config.parent_entity
    context.user = config.parent_entity
    SetupClass = get_system_setup(config.setup)
    setup = SetupClass(config, context)
    setup.run()


class CronInstall(event.Plugin):
  
  def run(self, context):
    time_difference = datetime.datetime.now()-datetime.timedelta(minutes=15)
    configurations = context.model.query(context.model.state == 'active', context.model.updated < time_difference).fetch(50)
    for config in configurations:
      context.auth.user = config.parent_entity
      context.user = config.parent_entity
      SetupClass = get_system_setup(config.setup)
      setup = SetupClass(config, context)
      setup.run()
