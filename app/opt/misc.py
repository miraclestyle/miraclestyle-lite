# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.srv import io, rule, log

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
                                                rule.ActionPermission('14', io.Action.build_key('14-0').urlsafe(), True, "context.auth.user.root_admin"),
                                               ])
  

    _actions = {
       'manage' : io.Action(id='14-0',
                              arguments={
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'title' : ndb.SuperStringProperty(required=True),
                                 'category' : ndb.SuperIntegerProperty(required=True),
                                 'body' : ndb.SuperTextProperty(required=True),
                                 'sequence' : ndb.SuperIntegerProperty(required=True),
                                 'active' : ndb.SuperBooleanProperty(default=False),
                                   
                                 'key' : ndb.SuperKeyProperty(kind='14'),
          
                              }
                             ),
 
    }  
    
    @classmethod
    def manage(cls, args):
        
        action = cls._actions.get('manage')
        context = action.process(args)
        
        if not context.has_error():
          
            @ndb.transactional(xg=True)
            def transaction():
              
                create = context.args.get('create')
                set_args = context.args.copy()
                
                if create:
                   entity = cls()
                else:
                   entity_key = context.args.get('key')
                   if not entity_key:
                      return context.required('key')
                    
                   entity = entity_key.get()
                   del set_args['key']
                   
                del set_args['create']
              
                context.rule.entity = entity
                rule.Engine.run(context, True)
                
                if not rule.executable(context):
                   return context.not_authorized()
                 
                entity.populate(**set_args)
                entity.put()
                  
                context.log.entities.append((entity,))
                log.Engine.run(context)
                   
                context.status(entity)
               
            try:
                transaction()
            except Exception as e:
                context.transaction_error(e)
            
        return context
 

# done!
class ProductCategory(ndb.BaseModel):
    
    _kind = 17
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/category.py#l8
    # https://support.google.com/merchants/answer/1705911
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L227
    # composite index: ancestor:no - status,name
    
    #  kind='app.core.misc.ProductCategory',
    parent_record = ndb.SuperKeyProperty('1', kind='17', indexed=False)
    name = ndb.SuperStringProperty('2', required=True)
    complete_name = ndb.SuperTextProperty('3')# da je ovo indexable bilo bi idealno za projection query
    state = ndb.SuperStringProperty('4', required=True) # @todo status => state ? better ? for convention ? or just active = boolean 

    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('17', io.Action.build_key('17-0').urlsafe(), True, "context.auth.user.root_admin"),
                                                rule.ActionPermission('17', io.Action.build_key('17-1').urlsafe(), True, "context.auth.user.root_admin"),
                                               ])
  

    _actions = {
       'manage' : io.Action(id='17-0',
                              arguments={
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'state' : ndb.SuperStringProperty(required=True),
                                 'parent_record' : ndb.SuperKeyProperty(kind='17'),
                                
                                 'key' : ndb.SuperKeyProperty(kind='17'),
          
                              }
                             ),
       'delete' : io.Action(id='17-1',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='17'),
                              }
                             ),
 
 
    }  
    
    @classmethod
    def manage(cls, args):
        
        action = cls._actions.get('manage')
        context = action.process(args)
        
        if not context.has_error():
          
            @ndb.transactional(xg=True)
            def transaction():
              
                create = context.args.get('create')
                set_args = context.args.copy()
                
                if create:
                   entity = cls()
                else:
                   entity_key = context.args.get('key')
                   if not entity_key:
                      return context.required('key')
                    
                   entity = entity_key.get()
                   del set_args['key']
                   
                del set_args['create']
              
                context.rule.entity = entity
                rule.Engine.run(context, True)
                
                if not rule.executable(context):
                   return context.not_authorized()
                 
                entity.populate(**set_args)
                entity.complete_name = ndb.make_complete_name(entity, 'name', 'parent_record')
                entity.put()
                  
                context.log.entities.append((entity,))
                log.Engine.run(context)
                   
                context.status(entity)
               
            try:
                transaction()
            except Exception as e:
                context.transaction_error(e)
            
        return context
  
    @classmethod
    def delete(cls, args):
        
        action = cls._actions.get('delete')
        context = action.process(args)

        if not context.has_error():
          
          @ndb.transactional(xg=True)
          def transaction():
                          
               entity_key = context.args.get('key')
               entity = entity_key.get()
               context.rule.entity = entity
               rule.Engine.run(context, True)
               
               if not rule.executable(context):
                  return context.not_authorized()
                
               entity.key.delete()
               context.log.entities.append((entity,))
               log.Engine.run(context)
        
               context.status(entity)
               
          try:
             transaction()
          except Exception as e:
             context.transaction_error(e)
           
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
                                                rule.ActionPermission('24', io.Action.build_key('24-0').urlsafe(), True, "not context.auth.user.is_guest"),
                                                rule.ActionPermission('24', io.Action.build_key('24-1').urlsafe(), True, "context.auth.user.root_admin and context.rule.entity.state in ['new', 'su_opened']"),
                                                rule.ActionPermission('24', io.Action.build_key('24-2').urlsafe(), True, "(context.rule.entity.key_parent == context.auth.user.key) and (context.rule.entity.state in ['su_opened', 'su_awaiting_closure'])"),
                                                rule.ActionPermission('24', io.Action.build_key('24-3').urlsafe(), True, "(context.rule.entity.state in ['new', 'su_opened', 'su_awaiting_closure']) and (context.auth.user.root_admin or context.rule.entity.key_parent == context.auth.user.key)"),

                                               ])
  

    _actions = {
       'create' : io.Action(id='24-0',
                              arguments={
                                 'reference' : ndb.SuperStringProperty(required=True),
                                 'message' : ndb.TextProperty(required=True),
                              }
                             ),
 
                
       'sudo' : io.Action(id='24-1',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='24'),
                                 'note' : ndb.TextProperty(required=True),
                                 'message' : ndb.TextProperty(required=True),
                                 'state' : ndb.SuperStringProperty(required=True)
                              }
                             ),
                
       'close' : io.Action(id='24-2',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='24'),
                                 'note' : ndb.TextProperty(required=False), # note should not be required i think
                                 'message' : ndb.TextProperty(required=True),
                              }
                             ),
                
       'log_message' : io.Action(id='24-3',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='24'),
                                 'note' : ndb.TextProperty(required=False), # note should not be required for log message
                                 'message' : ndb.TextProperty(required=True),
                              }
                             ), 
 
    }  
 
    def __todict__(self):
      
      d = super(SupportRequest, self).__todict__()
 
      d['messages'] = log.Record.query(ancestor=self.key).fetch()
      
      return d
    
    @classmethod
    def create(cls, args):
        
        action = cls._actions.get('create')
        context = action.process(args)
        
        if not context.has_error():
          
            @ndb.transactional(xg=True)
            def transaction():
              
                entity = cls(parent=context.auth.user.key, state='new')
              
                context.rule.entity = entity
                rule.Engine.run(context, True)
                
                if not rule.executable(context):
                   return context.not_authorized()
 
                entity.reference = context.args.get('reference')
                entity.put()
                  
                context.log.entities.append((entity,))
                log.Engine.run(context)
                   
                context.status(entity)
               
            try:
                transaction()
            except Exception as e:
                context.transaction_error(e)
            
        return context
    
    @classmethod
    def close(cls, args):
      
        action = cls._actions.get('close')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('key')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context, True)
               
               if not rule.executable(context):
                  return context.not_authorized()
               
               entity.state = 'closed'
               entity.put()
               
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
 
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
 
 
    @classmethod
    def sudo(cls, args):
      
        action = cls._actions.get('sudo')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('key')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context, True)
               
               if not rule.executable(context):
                  return context.not_authorized()
                
               if context.args.get('state') not in ('su_opened', 'su_awaiting_closure'):
                  return context.error('state', 'invalid_state')
               
               entity.state = context.args.get('state')
               entity.put()
               
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
     
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
    
    @classmethod
    def log_message(cls, args):
      
        action = cls._actions.get('log_message')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('key')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context, True)
               
               if not rule.executable(context):
                  return context.not_authorized()
                
               entity.put() # ref project-documentation.py #L-244
  
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
               
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
   