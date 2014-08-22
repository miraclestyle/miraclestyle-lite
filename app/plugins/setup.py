# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import time
import datetime
import collections
import math
from xml.etree import ElementTree

from app import orm, settings
from app.tools.base import callback_exec
from app.util import *


class ConfigurationInstall(orm.BaseModel):
  
  def run(self, context):
    config = context._configuration
    context.user = config.parent_entity
    SetupClass = get_system_setup(config.setup)
    setup = SetupClass(config, context)
    setup.run()


class ConfigurationCronInstall(orm.BaseModel):
  
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


__SYSTEM_SETUPS = {}


def get_system_setup(setup_name):
  global __SYSTEM_SETUPS
  return __SYSTEM_SETUPS.get(setup_name)


def register_system_setup(*setups):
  global __SYSTEM_SETUPS
  for setup in setups:
    __SYSTEM_SETUPS[setup[0]] = setup[1]


class Setup():
  
  skip_transactions = ['create_widgets', 'create_transaction_categories', 'create_order_journal']
  
  def __init__(self, config, context):
    self.config = config
    self.context = context
  
  def __get_next_operation(self):
    if not self.config.next_operation:
      return 'execute_init'
    function = 'execute_%s' % self.config.next_operation
    log('Running function %s' % function)
    return function
  
  def run(self):
    iterations = 100
    while self.config.state == 'active':
      iterations -= 1
      fn = self.__get_next_operation()
      runner = getattr(self, fn) # will throw error if next operation does not exist.
      if self.config.next_operation not in self.skip_transactions:
        orm.transaction(runner, xg=True)
      else:
        runner()
      time.sleep(1.5)  # Sleep between transactions.
      if iterations < 1: # To prevent forever loops this is for testing purposes
        log('Stopped iteration after 100')
        break


class DomainSetup(Setup):
  
  def execute_init(self):
    config_input = self.config.configuration_input
    self.config.next_operation = 'create_domain'
    self.config.next_operation_input = {'name': config_input.get('name'),
                                        'logo': config_input.get('logo')}
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
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    ActionPermission = self.context.models['79']
    FieldPermission = self.context.models['80']
    DomainRole = self.context.models['60']
    permissions = []
    objects = ['6', '60', '8', '62', '61', '35', '38', '39', '17', '15', '16', '19', '49', '47']
    for obj in objects:
      obj = self.context.models.get(obj)
      if obj is not None:  # This is because we do not have all models ported yet.
        # For production it should work self.context.models[obj]
        if hasattr(obj, '_actions'):
          actions = []
          for action_instance in obj._actions:
            actions.append(action_instance.key)
          permissions.append(ActionPermission(obj.get_kind(), actions, True, 'True'))
          props = obj.get_fields()
          prop_names = []
          for prop_name, prop in props.iteritems():
            prop_names.append(prop_name)
          permissions.append(FieldPermission(obj.get_kind(), prop_names, True, True, 'True'))
    entity = DomainRole(namespace=namespace, id='admin', name='Administrators', permissions=permissions)
    entity._use_rule_engine = False
    entity.write({'agent': self.context.user.key, 'action': self.context.action.key})
    self.config.next_operation = 'create_widgets'
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': entity.key}
    self.config.write()
  
  def execute_create_widgets(self):
    
    config_input = self.config.next_operation_input
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    role_key = config_input.get('role_key')
    
    Widget = self.context.models['62']
    Filter = self.context.models['65']
    
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
                                Filter(name='Users', model='8')]),
                Widget(id='system_user_interface',
                       namespace=namespace,
                       name='User Interface',
                       role=role_key,
                       search_form=False,
                       filters=[Filter(name='Menu Widgets', model='62')]),
                Widget(id='system_transaction',
                       namespace=namespace,
                       name='Transaction',
                       role=role_key,
                       search_form=False,
                       filters=[Filter(name='Journals', model='49'), Filter(name='Categories', model='47')]),
                Widget(id='system_notifications',
                       namespace=namespace,
                       name='Notifications',
                       role=role_key,
                       search_form=False,
                       filters=[Filter(name='Templates', model='61')])]
    for i, entity in enumerate(entities):
      entity._use_rule_engine = False
      entity.sequence = i
    orm.write_multi_transactions(entities, {'agent': self.context.user.key, 'action': self.context.action.key})
    self.config.next_operation = 'create_domain_user'
    self.config.next_operation_input = {'domain_key': domain_key,
                                        'role_key': role_key}
    self.config.write()
 
  def execute_create_domain_user(self):
    config_input = self.config.next_operation_input
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    DomainUser = self.context.models['8']
    user = self.config.parent_entity
    entity = DomainUser(namespace=namespace, id=user.key_id_str,
                        name='Administrator', state='accepted',
                        roles=[config_input.get('role_key')])
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
    self.config.next_operation = 'create_transaction_categories'
    self.config.next_operation_input = {'domain_key': domain_key}
    self.config.write()
  
  def execute_create_transaction_categories(self):
    config_input = self.config.next_operation_input
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    Category = self.context.models['47']
    
    def make_complete_name(info, infos):
      separator = unicode(' / ')
      parent_id = info.get('parent_id')
      names = [info.get('name')]
      if parent_id is not None:
        while True:
          find_end = infos.get(parent_id)
          if find_end is None:
            break
          names.append(find_end.get('name'))
          parent_id = find_end.get('parent_id')
          if parent_id is None:
            break
      names.reverse()
      return separator.join(names)
    
    with file(settings.TRANSACTION_CATEGORIES_DATA_FILE) as f:
      tree = ElementTree.fromstring(f.read())
      root = tree.findall('data')
      infos = collections.OrderedDict()
      for child in root[0]:
        new_category = {}
        the_id = child.attrib.get('id')
        new_category['id'] = the_id
        for child2 in child:
          name = child2.attrib.get('name')
          if name is not None:
            if name == 'parent_id':
              val = child2.get('ref')
            else:
              val = child2.text
            new_category[name] = val
        infos[the_id] = new_category
    to_put = []
    for the_id, info in infos.iteritems():
      parent_id = info.get('parent_id')
      data = {'name' : info.get('name'), 'complete_name' : make_complete_name(info, infos), 'namespace' : namespace, 'id' : info.get('code')}
      if parent_id is not None:
        parent = infos.get(parent_id)
        data['parent_record'] = Category.build_key(parent['code'], namespace=namespace) # will throw an error if parent was specified but not found
      new_category = Category(**data)
      new_category._use_rule_engine = False
      to_put.append(new_category)
    orm.write_multi_transactions(to_put, {'agent': self.context.user.key, 'action': self.context.action.key})
    self.config.next_operation = 'create_order_journal'
    self.config.next_operation_input = {'domain_key': domain_key}
    self.config.write()
  
  def execute_create_order_journal(self):
    config_input = self.config.next_operation_input
    domain_key = config_input.get('domain_key')
    namespace = domain_key.urlsafe()
    # @todo Insert creation logic here!
    self.config.next_operation = 'complete'
    self.config.next_operation_input = {'domain_key': domain_key}
    self.config.write()
  
  def execute_complete(self):
    config_input = self.config.next_operation_input
    domain_key = config_input.get('domain_key')
    entity = domain_key.get()
    
    def message_recievers(entity, user):
      primary_contact = entity.primary_contact.get()
      user = orm.Key('0', int(primary_contact.key_id_str)).get()
      return [user._primary_email]
    
    CustomTemplate = self.context.models['59']
    custom_notify = CustomTemplate(outlet='send_mail',
                                   message_subject='Your Application "{{entity.name}}" has been sucessfully created.',
                                   message_body='Your application has been created. Check your apps page (this message can be changed). Thanks.',
                                   message_recievers=message_recievers)
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
