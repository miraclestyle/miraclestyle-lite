# -*- coding: utf-8 -*-
'''
Created on Feb 17, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import time
import datetime

from app import ndb, util, settings
from app.srv import event, log, nav, rule, callback
 
__SYSTEM_SETUPS = {}

# example: get_system_setup('domain_setup')
def get_system_setup(setup_name):
  global __SYSTEM_SETUPS
  return __SYSTEM_SETUPS.get(setup_name)

# example: register_system_setup(('domain_setup', DomainSetup), ('name', Class))
def register_system_setup(*setups):
  global __SYSTEM_SETUPS
  for setup in setups:
    __SYSTEM_SETUPS[setup[0]] = setup[1]
    

class Context():
  
  def __init__(self):
      self.input = {}
      self.name = None
      self.transactional = None
 

# this will be configuration for domain setup
class Setup():

 def __init__(self, configuration, context):
   
    # upon init, we setup context and configuration instance for use in the methods below
    self.config = configuration
    self.context = context
     
     
 def __get_next_operation(self):
    # protected method of pointing out which operation will be called next
    if not self.config.next_operation:
       return 'execute_init'
     
    funct = 'execute_%s' % self.config.next_operation
    
    util.logger('Running function %s' % funct)
    
    return funct
    
    
 def run(self):
   # this is called in while loop. it wont stop calling functions until the configuration state equals something else then "active"
   runner = getattr(self, self.__get_next_operation())
   
   if runner:
      return ndb.transaction(runner, xg=True) # each function is called in seperate transaction
   
   
class DomainSetup(Setup):
  
  @classmethod
  def create_domain_notify_message_recievers(cls, entity, user):
          primary_contact = entity.primary_contact.get()
          return [primary_contact._primary_email]
 
  def execute_init(self):
    
    config_input = self.config.configuration_input
    
    self.config.next_operation_input = {'name' : config_input.get('domain_name'), 
                                        'primary_contact' : config_input.get('domain_primary_contact')
                                       }
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
 
     objects = [auth.Domain, rule.DomainRole, rule.DomainUser, nav.Widget, notify.Template, notify.MailNotify, notify.HttpNotify,
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
 
     self.config.next_operation_input = {'domain_key' : domain_key, 
                                         'role_key' : role.key,
                                        }
     self.config.next_operation = 'create_widget_step_1'
     self.config.put()
     
  def execute_create_widget_step_1(self):
    
      input = self.config.next_operation_input
      domain_key = input.get('domain_key')
      namespace = domain_key.urlsafe()
      role_key = input.get('role_key')
 
      to_put = [nav.Widget(id='admin_marketing', 
                           namespace=namespace,
                           name='Marketing',
                           role=role_key,
                           filters=[nav.Filter(name='Catalog', kind='35')]),
                 nav.Widget(id='admin_business',
                            namespace=namespace, 
                            name='Business', 
                            role=role_key,
                            filters=[nav.Filter(name='Companies', kind='44')]),
                 nav.Widget(id='admin_security', 
                            namespace=namespace,
                            name='Security',
                            role=role_key,
                            filters=[nav.Filter(name='Roles', kind='60'),
                                     nav.Filter(name='Filter Groups', kind='62')]),

 
                    ]
      
      for i,to in enumerate(to_put):
          to.sequence = i
      
      ndb.put_multi(to_put)
      
      for to in to_put:
          self.context.log.entities.append((to,))
           
      log.Engine.run(self.context)
       
      self.config.next_operation_input = {'domain_key' : domain_key, 
                                          'role_key' : role_key,
                                          'sequence' : i,
                                        }
      self.config.next_operation = 'create_widget_step_2'
      self.config.put()
      
      
  def execute_create_widget_step_2(self):
    
      input = self.config.next_operation_input
      domain_key = input.get('domain_key')
      namespace = domain_key.urlsafe()
      role_key = input.get('role_key')
      sequence = input.get('sequence')
 
      to_put = [nav.Widget(id='admin_app_users',
                            namespace=namespace,
                            name='App Users',
                            role=role_key,
                            filters=[nav.Filter(name='Users', kind='8')]),
               nav.Widget(id='admin_notifications', 
                            namespace=namespace,
                            name='Notifications',
                            role=role_key,
                            filters=[nav.Filter(name='Templates', kind='61')]),
                ]
 
      for i,to in enumerate(to_put):
          to.sequence = (i+1)+sequence
      
      ndb.put_multi(to_put) 

      for to in to_put:
          self.context.log.entities.append((to,))
           
      log.Engine.run(self.context)
      
      self.config.next_operation_input = {'domain_key' : domain_key, 
                                          'role_key' : role_key,
                                        }
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
     self.config.next_operation_input = {'domain_key' : domain_key}
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
       
       custom_notify.run(self.context, self.context.auth.user, domain)
       
       callback.Engine.run(self.context)
       
       self.config.state = 'completed'
       self.config.put()
 

register_system_setup(('setup_domain', DomainSetup))
  

class Configuration(ndb.BaseExpando):
  
  _kind = 57
  
  # ancestor User
 
  configuration_input = ndb.SuperPickleProperty('1', required=True, compressed=False) # original user supplied input
  setup = ndb.SuperStringProperty('2', required=True) 
  next_operation = ndb.SuperStringProperty('3')
  next_operation_input = ndb.SuperPickleProperty('4') # recorded by setup engine
  state = ndb.SuperStringProperty('5', required=True) # working, error, completed....
  created = ndb.SuperDateTimeProperty('6', auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('7', auto_now=True)
  
  _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('57', event.Action.build_key('57-0').urlsafe(), True, "context.auth.user._is_taskqueue"),
                                            rule.ActionPermission('57', event.Action.build_key('57-1').urlsafe(), True, "context.auth.user._is_taskqueue"),
                              
                                            ])  
  
  _actions = {
              'install' : event.Action(id='57-0',
                                          arguments={
                                            'key' : ndb.SuperKeyProperty(required=True, kind='57')
                                        }),
              'cron_install' : event.Action(id='57-1')
            }
  
  
  @classmethod
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
          break
      