# -*- coding: utf-8 -*-
'''
Created on Feb 17, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import time
import datetime

from app import ndb, util, settings

from app.srv import event, log, notify
 
__SERVICE = 'setup'
__DEFAULT_ARGUMENTS = {
  'configuration_key' : ndb.SuperKeyProperty(kind='57', required=True)
}

# for every setup, there must be a unique action, because other services that depend on actions (like notify)
# wont know how to react
event.register_system_action(event.Action(id='setup_domain',
                                          service=__SERVICE,
                                          arguments=__DEFAULT_ARGUMENTS
                                          ))

# this method should perhaps be incorporated in DomainSetup class ?

# it could, however this code then must be below DomainSetup class
def create_domain_notify_message_recievers(entity, user):
    primary_contact = entity.primary_contact.get()
    return [primary_contact.primary_email]

# this registration call should perhaps be incorporated in DomainSetup constructor ?

# if we do that this function will be called every time the DomainSetup.__init__() is called, and that is alot 
# because this should be called only once upon module import
notify.register_system_templates(notify.GlobalTemplate(name='Send domain link after domain is completed',
                                         action=event.Action.build_key('setup_domain'), # reference to setup domain action implementation
                                         message_subject='Your Application "{{entity.name}}" has been sucessfully created.',
                                         message_sender=settings.NOTIFY_EMAIL,
                                         message_body='Your application has been created. Check your apps page (this message can be changed) app.srv.notify.py #L-232. Thanks.',
                                         message_recievers=create_domain_notify_message_recievers))

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
     entity.name = input.get('domain_name')
     entity.primary_contact = primary_contact
     entity.put()
     
     self.context.log.entities.append((entity,))
     
     log.Engine.run(self.context)
     
     namespace = entity.key.urlsafe()
 
     self.config.next_operation_input = {'namespace' : namespace}
     self.config.next_operation = 'create_domain_role'
     self.config.put()
      
     
  def execute_create_domain_role(self):
     
     input = self.config.next_operation_input
     namespace = input.get('namespace')
     permissions = []
     
     # from all objects specified here, the ActionPermission will be built. So the role we are creating
     # will have all action permissions - taken `_actions` per model
     from app.srv import auth, rule
     from app.domain import business, marketing, product

     objects = [auth.Domain, rule.DomainRole, rule.DomainUser, business.Company, business.CompanyContent,
                marketing.Catalog, marketing.CatalogImage, marketing.CatalogPricetag,
                       product.Content, product.Instance, product.Template, product.Variant]
     
     for obj in objects:
         if hasattr(obj, '_actions'):
           for friendly_action_key, action_instance in obj._actions.items():
               permissions.append(rule.ActionPermission(kind=obj.get_kind(), 
                                                        action=action_instance.key.urlsafe(),
                                                        executable=True,
                                                        condition='True'))
     
     role = rule.DomainRole(namespace=namespace, name='Administrators', permissions=permissions)
     role.put()
     
     # context.log.entities.append((role, ))
     
     config_input = self.config.configuration_input
     self.config.next_operation_input = {'namespace' : namespace, 
                                         'role_key' : role.key,
                                        }
     self.config.next_operation = 'create_domain_user'
     self.config.put()
     
  def execute_create_domain_user(self):
    
     from app.srv import rule
     
     input = self.config.next_operation_input
     user = self.config.parent_entity
     namespace = input.get('namespace')
    
     domain_user = rule.DomainUser(namespace=namespace, id=user.key_id_str,
                               name=user.primary_email, state='accepted',
                               roles=[input.get('role_key')])
     
     domain_user.put()
     # context.log.entities.append((domain_user, ))

     
     config_input = self.config.configuration_input
     self.config.next_operation_input = {'namespace' : namespace}
     other_info = ('name',
                   'logo',
                   'state',                                         
                   'country',
                   'region',
                   'city',
                   'postal_code',
                   'street',
                   'email',
                   'telephone',
                   'currency',
                   'paypal_email',
                   'tracking_id',
                   'feedbacks',
                   'location_exclusion')
     
     for info in other_info:
         self.config.next_operation_input[info] = config_input.get('company_%s' % info)
         
     self.config.next_operation = 'create_company'
     self.config.put()
 
 
  def execute_create_company(self):
    
      from app.domain import business
      
      input = self.config.next_operation_input
      
      namespace = input.pop('namespace')
      
      entity = business.Company(namespace=namespace)
      entity.populate(**input)
      entity.state = 'open'
      ndb.make_complete_name(entity, 'name', 'parent_record')
      entity.put()
      
      self.context.log.entities.append((entity,))
      
      log.Engine.run(self.context)
       
      self.config.next_operation = 'add_user_domain'
      self.config.next_operation_input = {'namespace' : namespace}
      self.config.put()
      
      
  def execute_add_user_domain(self):
      
     input = self.config.next_operation_input
     user = self.config.parent_entity
     
     namespace = input.get('namespace')
     
     domain_key = ndb.Key(urlsafe=namespace)
     domain = domain_key.get()
     
     user.domains.append(domain_key)
     user.put()
     
     self.context.log.entities.append((user,))
     
     log.Engine.run(self.context)
     
     self.context.notify.entity = domain
     
     notify.Engine.run(self.context)
     
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
  
  @classmethod
  def get_active_configurations(cls):
    time_difference = datetime.datetime.now()-datetime.timedelta(minutes=15)
    configurations = cls.query(cls.state == 'active', cls.updated < time_difference).fetch(50)
    return configurations
  
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
    
class Engine:
  
  @classmethod
  def crun_run(cls, context):
    configurations = Configuration.get_active_configurations()
    for configuration in configurations:
      context.auth.user = configuration.parent_entity
      configuration.run(context)
  
  @classmethod
  def run(cls, context):
    # runs in transaction
    configuration_key = context.input.get('configuration_key')
    configuration = configuration_key.get()
    
    util.logger('Start configuration.run(context)')
    
    context.auth.user = configuration.parent_entity
    
    configuration.run(context)
    
    util.logger('End configuration.run(context)')
      