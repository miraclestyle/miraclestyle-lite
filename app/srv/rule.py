# -*- coding: utf-8 -*-
'''
Created on Dec 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.lib.safe_eval import safe_eval
from app.srv import io, log

def _check_field(context, name, key):
    if context.entity:
      # this is like this because we can use it like writable(context, ('field1', 'field2'))
      if not isinstance(key, (tuple, list)):
         key = (key, )
      checks = []
      for k in key:
          checks.append(context.entity._field_permissions[name][k])
      return all(checks)
    else:
      return False

def writable(context, name):
  return _check_field(context, name, 'writable')

def visible(context, name):
  return _check_field(context, name, 'visible')

def required(context, name):
  return _check_field(context, name, 'required')

def executable(context):
  if context.rule.entity:
     return context.rule.entity._action_permissions[context.action.key.urlsafe()]['executable']
  else:
     return False
  


class Context():
  
  def __init__(self):
    self.entity = None
    
    
class Permission():
  pass


class ActionPermission(Permission):
  
  
  def __init__(self, kind, action, executable=None, condition=None):
    
    self.kind = kind # entity kind identifier (entity._kind)
    self.action = action # action id (action.key.id()), or action key (action.key) ?
    self.executable = executable
    self.condition = condition
    
  def run(self, role, context):
     
    if (self.kind == context.rule.entity.get_kind()) and (self.action in context.rule.entity.get_actions()) and (safe_eval(self.condition, {'context' : context})) and (self.executable != None):
       context.rule.entity._action_permissions[self.action]['executable'].append(self.executable)


class FieldPermission(Permission):
  
  
  def __init__(self, kind, field, writable=None, visible=None, required=None, condition=None):
    
    self.kind = kind # entity kind identifier (entity._kind)
    self.field = field # this must be a field code name from ndb property (field._code_name)
    self.writable = writable
    self.visible = visible
    self.required = required
    self.condition = condition
    
  def run(self, context):
 
    if (self.kind == context.rule.entity.get_kind()) and (self.field in context.rule.entity.get_fields()) and (safe_eval(self.condition, {'context' : context})):
      if (self.writable != None):
        context.rule.entity._field_permissions[self.field]['writable'].append(self.writable)
      if (self.visible != None):
        context.rule.entity._field_permissions[self.field]['visible'].append(self.visible)
      if (self.required != None):
        context.rule.entity._field_permissions[self.field]['required'].append(self.required)
    

class Role(ndb.BaseExpando):
    
    # root (namespace Domain)
    # ovaj model ili LocalRole se jedino mogu koristiti u runtime i cuvati u datastore, dok se GlobalRole moze samo programski iskoristiti
    # ovo bi bilo tlacno za resurse ali je jedini preostao feature sa kojim 
    # bi ovaj rule engine koncept prevazisao sve ostale security modele
    # parent_record = ndb.SuperKeyProperty('1', kind='44', indexed=False) 
    # complete_name = ndb.SuperTextProperty('3')
    name = ndb.SuperStringProperty('1', required=True)
    active = ndb.SuperBooleanProperty('2', default=True)
    permissions = ndb.SuperPickleProperty('3', required=True, compressed=False) # [permission1, permission2,...]
    
    ### za ovo smo rekli da svakako treba da se radi validacija pri inputu 
    # treba da postoji validator da proverava prilikom put()-a da li su u permissions listi instance Permission klase
    # napr:
    #def _pre_put_hook(self):
    #for perm in self.permissions:
        #if not isinstance(perm, Permission):
           #raise ValueError('Expected instance of Permission, got %r' % perm)
    
    def run(self, context):
        for permission in self.permissions:
            permission.run(self, context)
 


class Engine:
  
  @classmethod
  def prepare(cls, context):
    
    context.rule.entity._field_permissions = {} 
    context.rule.entity._action_permissions = {} 
 
    fields = context.rule.entity.get_fields()
 
    for field_key in fields:
       context.rule.entity._field_permissions[field_key] = {'writable' : [], 'visible' : [], 'required' : []}
    
    actions = context.rule.entity.get_actions()
       
    for action_key in actions:
       context.rule.entity._action_permissions[action_key] = {'executable' : []}
 
  @classmethod
  def decide(cls, data, strict):
    calc = {}
    for element, properties in data.items():
          for prop, value in properties.items():
            
            if element not in calc:
               calc[element] = {}
            
            if len(value):
              if (strict):
                if all(value):
                   calc[element][prop] = True
                else:
                   calc[element][prop] = False
              elif any(value):
                calc[element][prop] = True
              else:
                calc[element][prop] = False
            else:
              calc[element][prop] = None
              
    return calc
  
  @classmethod
  def compile(cls, local_data, global_data, strict=False):
    
    global_data_calc = cls.decide(global_data, strict)
    
    # if any local data, process them
    if local_data:
       local_data_calc = cls.decide(local_data, strict)
       
       # iterate over local data, and override them with the global data, if any
       for element, properties in local_data_calc.items():
          for prop, value in properties.items():
              if element in global_data_calc:
                 if prop in global_data_calc[element]:
                    gc = global_data_calc[element][prop]
                    if gc is not None and gc != value:
                          local_data_calc[element][prop] = gc
                  
              if local_data_calc[element][prop] is None:
                 local_data_calc[element][prop] = False
                 
       # make sure that global data are always present
       for element, properties in global_data_calc.items():
          if element not in local_data_calc:
            for prop, value in properties.items():
              if prop not in local_data_calc[element]:
                 local_data_calc[element][prop] = value
            
       finals = local_data_calc
    
    # otherwise just use global data    
    else:
       for element, properties in global_data_calc.items():
          for prop, value in properties.items():
            if value is None:
               value = False
            global_data_calc[element][prop] = value
            
       finals = global_data_calc
       
    return finals
  
  @classmethod
  def run(cls, context, skip_user_roles=False, strict=False):
    
    # datastore system
    
    if context.rule.entity:
 
      # call prepare first, populates required dicts into the entity instance
      cls.prepare(context)
      local_action_permissions = {}
      local_field_permissions = {}
      
      if not skip_user_roles:
        user_role_key = UserRole.build_key(str(context.auth.user.key.id()), namespace=context.rule.entity.key.namespace())
        user_role = user_role_key.get()
        roles = ndb.get_multi(user_role.roles)
        for role in roles:
          if role.active:
             role.run(context)
          
        # copy 
        local_action_permissions = context.rule.entity._action_permissions.copy()
        local_field_permissions = context.rule.entity._field_permissions.copy()
      
        # empty
        cls.prepare(context)
   
      entity = context.rule.entity
      if hasattr(entity, '_global_role') and isinstance(entity._global_role, GlobalRole):
         entity._global_role.run(context)
      
      # copy   
      global_action_permissions = context.rule.entity._action_permissions.copy()
      global_field_permissions = context.rule.entity._field_permissions.copy()
      
      # empty
      cls.prepare(context)
     
      context.rule.entity._action_permissions = cls.compile(local_action_permissions, global_action_permissions, strict)
      context.rule.entity._field_permissions = cls.compile(local_field_permissions, global_field_permissions, strict)
   

class GlobalRole(Role):
      pass

class LocalRole(Role):
  
    _kind = 56
  
    _global_role = GlobalRole(permissions=[
                                            ActionPermission('56', io.Action.build_key('56-0').urlsafe(), False, "context.rule.entity.domain.state != 'active'"),
                                            ActionPermission('56', io.Action.build_key('56-1').urlsafe(), False, "context.rule.entity.domain.state != 'active'"),
                                          ])
    # unique action naming, possible usage is '_kind_id-manage'
    _actions = {
       'manage' : io.Action(id='56-0',
                              arguments={
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'domain' : ndb.SuperKeyProperty(kind='app.domain.acl.Domain'),
                                 'id' : ndb.SuperKeyProperty(kind='56'),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'permissions' : ndb.SuperJsonProperty(required=True),
                                 'active' : ndb.SuperBooleanProperty(),
                              }
                             ),
                
       'delete' : io.Action(id='56-1',
                              arguments={
                                 'id' : ndb.SuperKeyProperty(kind='56'),
                              }
                             ),
    }
    
    @property
    def domain(self):
       return ndb.Key(urlsafe=self.key.namespace()).get()
  
    @classmethod
    def delete(cls, args):
        
        action = cls._actions.get('delete')
        context = action.process(args)
        
        if not context.has_error():
          
          @ndb.transactional(xg=True)
          def transaction():
                         
             entity_key = context.args.get('id')
             entity = entity_key.get()
            
             if entity and entity.loaded():
               
                context.rule.entity = entity
                Engine.run(context, True)
               
                if not executable(context):
                   return context.not_authorized()
                 
                domain_users = entity.domain.get_users(entity_key) 
                user_keys = []
                
                for domain_user in domain_users:
                    
                    domain_user.roles.remove(entity_key)
                    domain_user.put()
                    context.log.entities.append((domain_user,))
                    user_keys.append(domain_user.user)
                    
                users = ndb.get_multi(user_keys)
                
                for user in users:
                   user.roles.remove(entity_key)
                   user.put()
                   context.log.entities.append((user,))
                
                context.log.entities.append((entity, ))
                entity.key.delete()
                log.Engine.run(context)
                 
                context.status(entity)
                context.response['deleted'] = True
             else:
                context.not_found()      
              
          try:
             transaction()
          except Exception as e:
             context.transaction_error(e)
           
        return context
    
    @classmethod
    def manage(cls, args):
        
        action = cls._actions.get('manage')
        context = action.process(args)
        
        if not context.has_error():
          
            @ndb.transactional(xg=True)
            def transaction():
              
                create = context.args.get('create')
                
                if create:
                   domain_key = context.args.get('domain')
                   domain = domain_key.get()
                   entity = cls(namespace=domain.key.namespace())
                else:
                   entity_key = context.args.get('id')
                   entity = entity_key.get()
              
                context.rule.entity = entity
                Engine.run(context)
                
                if not executable(context):
                   return context.not_authorized()
                 
                entity.name = context.args.get('name')
                entity.active = context.args.get('active')
                
                permissions = context.args.get('permissions')
                set_permissions = []
                for permission in permissions:
                  
                    if 'action' not in permission:
                       set_permissions.append(FieldPermission(permission.get('kind'),
                                                               permission.get('field'),
                                                               permission.get('writable'),
                                                               permission.get('visible'), 
                                                               permission.get('required'),
                                                               permission.get('condition')))
                       
                    else:
                      set_permissions.append(ActionPermission(permission.get('kind'),
                                                              permission.get('action'),
                                                              permission.get('executable'),
                                                              permission.get('condition')))
                entity.permissions = set_permissions      
                entity.put()
                
                context.log.entities.append((entity,))
                log.Engine.run(context)
                   
                context.status(entity)
               
            try:
                transaction()
            except Exception as e:
                context.transaction_error(e)
            
        return context
 
class UserRole(ndb.BaseModel):
    
    _kind = 8
    
    # root (namespace Domain) - id = str(user_key.id())
    # mozda bude trebalo jos indexa u zavistnosti od potreba u UIUX
    # composite index: ancestor:no - name
    name = ndb.SuperStringProperty('1', required=True)# ovo je deskriptiv koji administratoru sluzi kako bi lakse spoznao usera
    roles = ndb.SuperKeyProperty('3', kind=LocalRole, repeated=True)# vazno je osigurati da se u ovoj listi ne nadju duplikati rola, jer to onda predstavlja security issue!!
    state = ndb.SuperStringProperty('4', required=True)# invited/accepted
    
    _default_indexed = False
    
    _global_role = GlobalRole(permissions=[
                                            ActionPermission('8', io.Action.build_key('8-0').urlsafe(), False, "context.rule.entity.domain.state != 'active'"),
                                            ActionPermission('8', io.Action.build_key('8-1').urlsafe(), False, "context.rule.entity.domain.state != 'active'"),
                                            ActionPermission('8', io.Action.build_key('8-2').urlsafe(), False, "context.rule.entity.domain.state != 'active'"),
                                            ActionPermission('8', io.Action.build_key('8-3').urlsafe(), False, "context.rule.entity.domain.state != 'active'"),
                                          ])
    # unique action naming, possible usage is '_kind_id-manage'
    _actions = {
       'invite' : io.Action(id='8-0',
                              arguments={
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'domain' : ndb.SuperKeyProperty(kind='app.srv.auth.Domain'),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'roles' : ndb.SuperKeyProperty(kind='56', required=True, repeated=True),
                              }
                             ),
                
       'remove' : io.Action(id='8-1',
                              arguments={
                                 'id' : ndb.SuperKeyProperty(kind='8', required=True),
                              }
                             ),
                
       'accept' : io.Action(id='8-2',
                              arguments={
                                 'id' : ndb.SuperKeyProperty(kind='8', required=True),
                              }
                             ),
                
       'update' : io.Action(id='8-3',
                              arguments={
                                 'id' : ndb.SuperKeyProperty(kind='8', required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'roles' : ndb.SuperKeyProperty(kind='56', required=True, repeated=True),
                              }
                             ),
    }
    
    @property
    def domain(self): # maybe replaced by context.auth.domain
       return ndb.Key(urlsafe=self.key.namespace()).get()
  
    # Poziva novog usera u domenu, al čime da ga poziva? po mailu?
    @classmethod
    def invite(cls, args):
        pass
          
    # Uklanja postojeceg usera iz domene
    @classmethod
    def remove(cls, args):
        pass
 
    # Prihvata poziv novog usera u domenu
    @classmethod
    def accept(cls, args):
        pass
    
    # Azurira postojeceg usera u domeni
    @classmethod
    def update(cls, args):
        pass