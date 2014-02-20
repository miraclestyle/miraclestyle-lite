# -*- coding: utf-8 -*-
'''
Created on Feb 17, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import time

from app import ndb, util

from google.appengine.api import taskqueue

from app.srv import io

# should implement it's own Context() probably, and be integrated in io.py Context.setup...

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

 def __init__(self, configuration):
    self.config = configuration
     
     
 def __get_next_operation(self):
    # protected method of chooising the  next operation
    if not self.config.next_operation:
       return 'execute_init'
     
    funct = 'execute_%s' % self.config.next_operation
    
    util.logger('Running function %s' % funct)
    
    return funct
    
    
 def run(self):
   runner = getattr(self, self.__get_next_operation())
   
   if runner:
      return ndb.transaction(runner, xg=True)
   
   
class DomainSetup(Setup):
 
  def execute_init(self):
    
    config_input = self.config.configuration_input
    self.config.next_operation_input = {'name' : config_input.get('domain_name'), 
                                        'primary_contact' : config_input.get('domain_primary_contact')
                                       }
    self.config.next_operation = 'create_domain'
    self.config.put()
     
    
  def execute_create_domain(self):
     # this creates new domain
     input = self.config.configuration_input
     primary_contact = input.get('domain_primary_contact')
     
     from app.srv import auth
     
     entity = auth.Domain(state='active')
     entity.name = input.get('domain_name')
     entity.primary_contact = primary_contact
     entity.put()
     
     namespace = entity.key.urlsafe()
 
     self.config.next_operation_input = {'namespace' : namespace}
     self.config.next_operation = 'create_domain_role'
     self.config.put()

     # build a role - possible usage of app.etc
     
     # from app.domain import business, marketing, product
     
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
    
     domain_user = rule.DomainUser(namespace=namespace, user=user.key, id=user.key_id_str,
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
       
      self.config.next_operation = 'add_user_domain'
      self.config.next_operation_input = {'namespace' : namespace}
      self.config.put()
      
      
  def execute_add_user_domain(self):
      
     input = self.config.next_operation_input
     user = self.config.parent_entity
     
     namespace = input.get('namespace')
     
     user.domains.append(ndb.Key(urlsafe=namespace))
     user.put()      
     
     self.config.state = 'completed'
     self.config.put()
     
     io.Engine.run({'action_key' : 'create_complete', 'key' : namespace, 'action_model' : 'srv.auth.Domain'})
     
     

register_system_setup(('create_domain', DomainSetup))
  

class Configuration(ndb.BaseExpando):
  
  _kind = 57
  
  # ancestor User
  # key.id() = prefix_<user supplied value>
  
  configuration_input = ndb.SuperPickleProperty('1', required=True, compressed=False) # original user supplied input
  setup = ndb.SuperStringProperty('2', required=True) 
  next_operation = ndb.SuperStringProperty('3')
  next_operation_input = ndb.SuperPickleProperty('4') # recorded by setup engine
  state = ndb.SuperStringProperty('5', required=True) # working, error, completed....
  created = ndb.SuperDateTimeProperty('6', auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('7', auto_now=True)
  
  @classmethod
  def get_active_configurations(cls):
    configurations = cls.query(cls.state == 'active').fetch(50)
    return configurations
  
  def run(self):
    SetupClass = get_system_setup(self.setup)
    setup = SetupClass(self)
    
    iterations = 100
    while self.state == 'active':
       iterations -= 1
       setup.run()
       time.sleep(1.5) # throughput demands one entity per sec, we will put 1.5
       
       # dont do infinite loop, this is just for tests now.
       if iterations < 1:
          util.logger('Stopped iteration at %s' % iterations)
          break
    
class Engine:
  
  @classmethod
  def run_configuration(cls, context):
    configurations = Configuration.get_active_configurations()
    for configuration in configurations:
      configuration.run()
  
  @classmethod
  def run(cls, context):
    # runs in transaction
    setup = context.setup.name
    
    if setup and get_system_setup(setup):
      if context.setup.transactional is None:
        context.setup.transactional = ndb.in_transaction()
      
      entity = Configuration(parent=context.auth.user.key, configuration_input=context.setup.input, setup=setup, state='active')
      entity.put()
      
      new_task = taskqueue.add(queue_name='setup', url='/task/run_configuration', transactional=context.setup.transactional, params={'configuration_key' : entity.key.urlsafe()})
      
      return [entity, new_task]
      