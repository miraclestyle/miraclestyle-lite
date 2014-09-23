# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from backend import ndb
from backend.srv import event, rule, log

# done 80%

class Content(ndb.BaseModel):
    
    _kind = 14
    # root
    # composite index: ancestor:no - category,active,sequence
    updated = ndb.SuperDateTimeProperty('1', auto_now=True)
    title = ndb.SuperStringProperty('2', required=True)
    category = ndb.SuperIntegerProperty('3', required=True)
    body = ndb.SuperTextProperty('4', required=True)
    sequence = ndb.SuperIntegerProperty('5', required=True)
    active = ndb.SuperBooleanProperty('6', default=False)
    
    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('14', event.Action.build_key('14-0').urlsafe(), True, "context.auth.user._root_admin"),
                                                rule.ActionPermission('14', event.Action.build_key('14-1').urlsafe(), True, "context.auth.user._root_admin"),
                                               ])
  

    _actions = {
       'create' : event.Action(id='14-0',
                              arguments={
        
                                 'title' : ndb.SuperStringProperty(required=True),
                                 'category' : ndb.SuperIntegerProperty(required=True),
                                 'body' : ndb.SuperTextProperty(required=True),
                                 'sequence' : ndb.SuperIntegerProperty(required=True),
                                 'active' : ndb.SuperBooleanProperty(default=False),
                             
          
                              }
                             ),
                
       'update' : event.Action(id='14-1',
                              arguments={
                  
                                 'title' : ndb.SuperStringProperty(required=True),
                                 'category' : ndb.SuperIntegerProperty(required=True),
                                 'body' : ndb.SuperTextProperty(required=True),
                                 'sequence' : ndb.SuperIntegerProperty(required=True),
                                 'active' : ndb.SuperBooleanProperty(default=False),
                                   
                                 'key' : ndb.SuperKeyProperty(kind='14', required=True),
          
                              }
                             ),
 
    }  
    
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
          
        context.log.entities.append((entity,))
        log.Engine.run(context)
 
    @classmethod
    def create(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
 
            entity = cls()
          
            cls.complete_save(entity, context)
           
        transaction()
            
        return context
       
    
    @classmethod
    def update(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
  
            entity_key = context.input.get('key')
            entity = entity_key.get()
            
            cls.complete_save(entity, context)
            
           
        transaction()
            
        return context

# @todo
class Message(ndb.BaseModel):
    
    _kind = 21
    
    # root
    outlet = ndb.SuperIntegerProperty('1', required=True, indexed=False)
    group = ndb.SuperIntegerProperty('2', required=True, indexed=False)
    state = ndb.SuperIntegerProperty('3', required=True)
  

# done! - sudo kontrolisan model
class SupportRequest(ndb.BaseModel):
    
    _kind = 24
    
    # ancestor User
    # ako uopste bude vidljivo useru onda mozemo razmatrati indexing
    # ako hocemo da dozvolimo sva sortiranja, i dodatni filter po state-u uz sortiranje, onda nam trebaju slecedi indexi
    # composite index:
    # ancestor:yes - updated:desc; ancestor:yes - created:desc;
    # ancestor:yes - state,updated:desc; ancestor:yes - state,created:desc
    reference = ndb.SuperStringProperty('1', required=True, indexed=False)
    state = ndb.SuperStringProperty('2', required=True)
    updated = ndb.SuperDateTimeProperty('3', auto_now=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True)
    
    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('24', event.Action.build_key('24-0').urlsafe(), True, "not context.auth.user._is_guest"),
                                                rule.ActionPermission('24', event.Action.build_key('24-1').urlsafe(), True, "context.auth.user._root_admin and context.rule.entity.state in ['new', 'su_opened']"),
                                                rule.ActionPermission('24', event.Action.build_key('24-2').urlsafe(), True, "(context.rule.entity.key_parent == context.auth.user.key) and (context.rule.entity.state in ['su_opened', 'su_awaiting_closure'])"),
                                                rule.ActionPermission('24', event.Action.build_key('24-3').urlsafe(), True, "(context.rule.entity.state in ['new', 'su_opened', 'su_awaiting_closure']) and (context.auth.user._root_admin or context.rule.entity.key_parent == context.auth.user.key)"),

                                               ])
  

    _actions = {
       'create' : event.Action(id='24-0',
                              arguments={
                                 'reference' : ndb.SuperStringProperty(required=True),
                                 'message' : ndb.TextProperty(required=True),
                              }
                             ),
 
                
       'sudo' : event.Action(id='24-1',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='24', required=True),
                                 'note' : ndb.TextProperty(required=True),
                                 'message' : ndb.TextProperty(required=True),
                                 'state' : ndb.SuperStringProperty(required=True)
                              }
                             ),
                
       'close' : event.Action(id='24-2',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='24', required=True),
                                 'note' : ndb.TextProperty(required=False), # note should not be required i think
                                 'message' : ndb.TextProperty(required=True),
                              }
                             ),
                
       'log_message' : event.Action(id='24-3',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='24', required=True),
                                 'note' : ndb.TextProperty(required=False), # note should not be required for log message
                                 'message' : ndb.TextProperty(required=True),
                              }
                             ), 
 
    }  
 
    
    @classmethod
    def create(cls, context):
 
         @ndb.transactional(xg=True)
         def transaction():
           
             entity = cls(parent=context.auth.user.key, state='new')
           
             context.rule.entity = entity
             rule.Engine.run(context, True)
             
             if not rule.executable(context):
                raise rule.ActionDenied(context)
    
             entity.reference = context.input.get('reference')
             entity.put()
               
             context.log.entities.append((entity,))
             log.Engine.run(context)
 
         transaction()
            
         return context
    
    @classmethod
    def close(cls, context):
 
        @ndb.transactional(xg=True)
        def transaction():
          
            entity_key = context.input.get('key')
            entity = entity_key.get()
       
            context.rule.entity = entity
            rule.Engine.run(context, True)
            
            if not rule.executable(context):
               raise rule.ActionDenied(context)
            
            entity.state = 'closed'
            entity.put()
            
            context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
            log.Engine.run(context)
 
        transaction()
           
        return context
 
 
    @classmethod
    def sudo(cls, context):
 
       @ndb.transactional(xg=True)
       def transaction():
         
           entity_key = context.input.get('key')
           entity = entity_key.get()
      
           context.rule.entity = entity
           rule.Engine.run(context, True)
           
           if not rule.executable(context):
              raise rule.ActionDenied(context)
            
           if context.input.get('state') not in ('su_opened', 'su_awaiting_closure'):
             # raise custom exception!!!
              return context.error('state', 'invalid_state')
           
           entity.state = context.input.get('state')
           entity.put()
           
           context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
           log.Engine.run(context)
 
       transaction()
           
       return context
    
    @classmethod
    def log_message(cls, context):
  
         @ndb.transactional(xg=True)
         def transaction():
           
             entity_key = context.input.get('key')
             entity = entity_key.get()
        
             context.rule.entity = entity
             rule.Engine.run(context, True)
             
             if not rule.executable(context):
                raise rule.ActionDenied(context)
              
             entity.put() # ref project-documentation.py #L-244
  
             context.log.entities.append((entity, {'message' : context.input.get('message'), 'note' : context.input.get('note')}))
             log.Engine.run(context)
        
         transaction()
           
         return context
   