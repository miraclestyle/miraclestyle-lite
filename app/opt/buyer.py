# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.srv import rule, event, log
 
class Address(ndb.BaseExpando):
    
    _kind = 9
    # ancestor User
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    country = ndb.SuperKeyProperty('2', kind='15', required=True, indexed=False)
    city = ndb.SuperStringProperty('3', required=True, indexed=False)
    postal_code = ndb.SuperStringProperty('4', required=True, indexed=False)
    street = ndb.SuperStringProperty('5', required=True, indexed=False)
    default_shipping = ndb.SuperBooleanProperty('6', default=True, indexed=False)
    default_billing = ndb.SuperBooleanProperty('7', default=True, indexed=False)
  
    _default_indexed = False
    
    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('9', event.Action.build_key('9-0').urlsafe(), True, "context.rule.entity.key_parent == context.auth.user.key and (not context.auth.user.is_guest)"),
                                                rule.ActionPermission('9', event.Action.build_key('9-3').urlsafe(), True, "context.rule.entity.key_parent == context.auth.user.key and (not context.auth.user.is_guest)"),
                                                rule.ActionPermission('9', event.Action.build_key('9-1').urlsafe(), True, "context.rule.entity.key_parent == context.auth.user.key and (not context.auth.user.is_guest)"),
                                               ])
 
    _expando_fields = {
        'region' :  ndb.SuperKeyProperty('8', kind='16'),
        'email' : ndb.SuperStringProperty('10'),
        'telephone' : ndb.SuperStringProperty('11'),
    }

    _actions = {
       'update' : event.Action(id='9-0',
                              arguments={
              
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'country' : ndb.SuperKeyProperty(kind='15', required=True),
                                 'city' : ndb.SuperStringProperty(required=True),
                                 'postal_code' : ndb.SuperStringProperty(required=True),
                                 'street' : ndb.SuperStringProperty(required=True),
                                 'default_shipping' : ndb.SuperBooleanProperty(default=True),
                                 'default_billing' : ndb.SuperBooleanProperty(default=True),
                                 
                                 'key' : ndb.SuperKeyProperty(kind='9', required=True),
                                 
                                  # expando
                                 'region' :  ndb.SuperKeyProperty(kind='16'),
                                 'email' : ndb.SuperStringProperty(),
                                 'telephone' : ndb.SuperStringProperty(),
                              }
                             ),
                
       'create' : event.Action(id='9-3',
                              arguments={
              
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'country' : ndb.SuperKeyProperty(kind='15', required=True),
                                 'city' : ndb.SuperStringProperty(required=True),
                                 'postal_code' : ndb.SuperStringProperty(required=True),
                                 'street' : ndb.SuperStringProperty(required=True),
                                 'default_shipping' : ndb.SuperBooleanProperty(default=True),
                                 'default_billing' : ndb.SuperBooleanProperty(default=True),
                                
                                  # expando
                                 'region' :  ndb.SuperKeyProperty(kind='16'),
                                 'email' : ndb.SuperStringProperty(),
                                 'telephone' : ndb.SuperStringProperty(),
                              }
                             ),
                
       'delete' : event.Action(id='9-1',
                              arguments={
                                 'address' : ndb.SuperKeyProperty(kind='9', required=True),
                              }
                             ),
                
       'list' : event.Action(id='9-2'),
    }  
 
      
    @classmethod
    def list(cls, context):
      
        user = context.auth.user
              
        context.output['addresses'] = cls.query(ancestor=user.key).fetch()
              
        return context
     
    @classmethod
    def delete(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
                        
             entity_key = context.input.get('key')
             entity = entity_key.get()
             context.rule.entity = entity
             rule.Engine.run(context, True)
             if not rule.executable(context):
                raise rule.ActionDenied(context)
              
             entity.key.delete()
             context.log.entities.append((entity,))
             log.Engine.run(context)
             
             context.output['deleted'] = True
     
        transaction()
             
        return context
      
    @classmethod
    def complete_save(cls, entity, context):
      
        set_args = {}
        
        for field_key in cls.get_fields():
             if field_key in context.input:
                set_args[field_key] = context.input.get(field_key)
      
        context.rule.entity = entity
        rule.Engine.run(context, True)
            
        if not rule.executable(context):
           raise rule.ActionDenied(context)
         
        entity.populate(**set_args)
        entity.put()
            
        if (entity.default_shipping or entity.default_billing):
          all_addresses = cls.query(ancestor=context.auth.user.key).fetch()
          
          for address in all_addresses:
            log = False
            if address.key != entity.key:
              if entity.default_shipping:
                 address.default_shipping = False
                 log = True
              if entity.default_billing:
                 address.default_billing = False
                 log = True
              #if (log):
                #context.log.entities.append((address, ))
                 
          ndb.put_multi(all_addresses) # no need to log default_billing and default_shipping, doesnt make sense
  
        context.log.entities.append((entity, ))
        log.Engine.run(context)
 
              
    @classmethod
    def update(cls, context): # im not sure if we are going to perform updates on multiple address instances - this is a UI thing
 
        @ndb.transactional(xg=True)
        def transaction():
            
            entity_key = context.input.get('key')
            entity = entity_key.get()
   
            cls.complete_save(entity, context)
             
        transaction()
            
        return context
            
    @classmethod
    def create(cls, context): # im not sure if we are going to perform updates on multiple address instances - this is a UI thing
 
       @ndb.transactional(xg=True)
       def transaction():
 
           entity = cls(parent=context.auth.user.key)
           
           cls.complete_save(entity, context)
          
       transaction()
            
       return context
    
            
# done!
class Collection(ndb.BaseModel):
    
    _kind = 10
    
    # ancestor User
    # mozda bude trebao index na primary_email radi mogucnosti update-a kada user promeni primarnu email adresu na svom profilu
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    notify = ndb.SuperBooleanProperty('2', required=True, default=False)
    companies = ndb.SuperKeyProperty('3', kind='44', repeated=True)
    
    primary_email = ndb.SuperStringProperty('4', required=True, indexed=False)
 

    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('10', event.Action.build_key('10-0').urlsafe(),
                                                                     True, "context.rule.entity.key_parent == context.auth.user.key and (not context.auth.user.is_guest)"),
                                                rule.ActionPermission('10', event.Action.build_key('10-3').urlsafe(),
                                                                     True, "context.rule.entity.key_parent == context.auth.user.key and (not context.auth.user.is_guest)"),
                                                rule.ActionPermission('10', event.Action.build_key('10-1').urlsafe(),
                                                                     True, "context.rule.entity.key_parent == context.auth.user.key and (not context.auth.user.is_guest)"),
                                               ])
 

    _actions = {
       'update' : event.Action(id='10-0',
                              arguments={
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'notify' : ndb.SuperBooleanProperty(default=False),
                                 'key' : ndb.SuperKeyProperty(kind='10', required=True),
                                 'companies' : ndb.SuperKeyProperty(kind='44', repeated=True),
                              }
                             ),
                
       'create' : event.Action(id='10-3',
                              arguments={
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'notify' : ndb.SuperBooleanProperty(default=False),
                                 'companies' : ndb.SuperKeyProperty(kind='44'),
                              }
                             ),
                
       'delete' : event.Action(id='10-1',
                              arguments={
                                  'key' : ndb.SuperKeyProperty(kind='10', required=True),
                              }
                             ),
                
       'list' : event.Action(id='10-2'),
    }  
 
    @classmethod
    def list(cls, context):
 
        user = context.auth.user
              
        context.output['collections'] = cls.query(ancestor=user.key).fetch()
              
        return context
         
    @classmethod
    def delete(cls, context):
 
       @ndb.transactional(xg=True)
       def transaction():
                       
            entity_key = context.input.get('key')
            entity = entity_key.get()
            context.rule.entity = entity
            rule.Engine.run(context, True)
            
            if not rule.executable(context):
               raise rule.ActionDenied(context)
             
            entity.key.delete()
            context.log.entities.append((entity,))
            log.Engine.run(context)
 
       transaction()
           
       return context
     
     
    @classmethod
    def complete_save(cls, entity, context):
      
        set_args = {}
        
        for field_key in cls.get_fields():
             if field_key in context.input:
                set_args[field_key] = context.input.get(field_key)
      
        context.rule.entity = entity
        rule.Engine.run(context, True)
        
        if not rule.executable(context):
           raise rule.ActionDenied(context)
        
        entity.primary_email = context.auth.user.primary_email
        
        company_keys = set_args.get('companies', [])
        
        if company_keys:
            companies = ndb.get_multi(company_keys)
            company_keys = []
            for company in companies:
                if not company.state == 'open':
                   company_keys.remove(company.key)
                    
        entity.populate(**set_args)
        entity.put()
         
        context.log.entities.append((entity, ))
        log.Engine.run(context)
    
     
    @classmethod
    def update(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
   
            entity_key = context.input.get('key')
            entity = entity_key.get()
          
            cls.complete_save(entity, context)
           
        transaction()
            
        return context
      
    @classmethod
    def create(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
    
            entity = cls(parent=context.auth.user.key)
 
            cls.complete_save(entity, context)
           
        transaction()
            
        return context
