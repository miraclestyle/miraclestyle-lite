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
                   entity = entity_key.get()
                   del set_args['key']
                   
                del set_args['create']
              
                context.rule.entity = entity
                rule.Engine.run(context)
                
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
                   entity = entity_key.get()
                   del set_args['key']
                   
                del set_args['create']
              
                context.rule.entity = entity
                rule.Engine.run(context)
                
                if not rule.executable(context):
                   return context.not_authorized()
                
                entity.complete_name = ndb.make_complete_name(entity, 'name', 'parent_record')
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
    state = ndb.SuperIntegerProperty('2', required=True)
    updated = ndb.SuperDateTimeProperty('3', auto_now=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True)
  
    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls, only=('reference',))
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values, parent=current.key)
            
            if entity is None:
               return response.not_found()
      
            if not entity or not entity.loaded():
               if not current.is_guest:
                   entity.set_state(cls.OBJECT_DEFAULT_STATE)
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response 
  
    @classmethod
    def sudo(cls, values, **kwds):
        
        response = ndb.Response()
        
        @ndb.transactional(xg=True) 
        def transaction(): 
            
            convert = [
                ndb.SuperStringProperty('message', required=True),
                ndb.SuperStringProperty('note', required=True)
            ]
            
            response.process_input(values, cls, only=False, convert=convert)
            if response.has_error():
               return response
            
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
               # check if user can do this
 
               action = values.get('action')
               
               if not action.startswith('su_'):
                  return response.not_authorized()
               
               current = ndb.get_current_user()
               if current.has_permission(action, entity):
                      state = values.get('state')
                      action = entity.new_action(action, state=state, message=values.get('message'), note=values.get('note'))
                      entity.put()
                      entity.record_action()
                      response.status([entity, action])
               else:
                   return response.not_authorized()
            else:
                response.not_found()
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)   
               
        return response
    
    @classmethod
    def log_message(cls, values, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)  
        def transaction(): 
            
            convert = [
                ndb.SuperStringProperty('message', required=True),
                ndb.SuperStringProperty('note', required=True)
            ]
            
            response.process_input(values, cls, only=False, convert=convert)
            if response.has_error():
               return response
            
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
               # check if user can do this
               current = ndb.get_current_user()
              
               if entity.get_state not in ('new', 'su_opened'):
                  return response.not_authorized()
              
               if current.has_permission('log_message', entity):
                      action = entity.new_action('log_message', message=values.get('message'), note=values.get('note'))
                      entity.record_action()
                      response.status([entity, action])
               else:
                   return response.not_authorized()
            else:
                response.not_found()
                
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
               
        return response
    
    @classmethod
    def close(cls, values, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)
        def transaction(): 
            
            convert = [
                ndb.SuperStringProperty('message', required=True),
                ndb.SuperStringProperty('note', required=True)
            ]
            
            response.process_input(values, cls, only=False, convert=convert)
            if response.has_error():
               return response
            
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
               # check if user can do this
               current = ndb.get_current_user()
               """
               su_opened
               su_awaiting_closure
               """
               if entity.get_state not in ('su_opened', 'su_awaiting_closure'):
                  return response.not_authorized()
               
               if current.has_permission('close', entity) or current.key == entity.key.parent():
                      action = entity.new_action('close', state='closed', message=values.get('message'), note=values.get('note'))
                      entity.put()
                      entity.record_action()
                      response.status([entity, action])
               else:
                   return response.not_authorized()
            else:
                response.not_found()
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)   
                       
        return response
   