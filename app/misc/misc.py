# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

# done 80%

class Content(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 14
    # root
    # composite index: ancestor:no - category,active,sequence
    updated = ndb.SuperDateTimeProperty('1', auto_now=True)
    title = ndb.SuperStringProperty('2', required=True)
    category = ndb.SuperIntegerProperty('3', required=True)
    body = ndb.SuperTextProperty('4', required=True)
    sequence = ndb.SuperIntegerProperty('5', required=True)
    active = ndb.SuperBooleanProperty('6', default=False)
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @property
    def is_usable(self):
        return self.active
    
    # def delete inherits from BaseModel see `ndb.BaseModel.delete()`
    
    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls)
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
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
 

# done!
class Image(ndb.BaseModel):
    
    # base class/structured class
    image = ndb.SuperImageKeyProperty('1', required=True, indexed=False)# blob ce se implementirati na GCS
    content_type = ndb.SuperStringProperty('2', required=True, indexed=False)
    size = ndb.SuperFloatProperty('3', required=True, indexed=False)
    width = ndb.SuperIntegerProperty('4', required=True, indexed=False)
    height = ndb.SuperIntegerProperty('5', required=True, indexed=False)
    sequence = ndb.SuperIntegerProperty('6', required=True)
    

# done!
class ProductCategory(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 17
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/category.py#l8
    # https://support.google.com/merchants/answer/1705911
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L227
    # composite index: ancestor:no - status,name
    
    #  kind='app.core.misc.ProductCategory',
    parent_record = ndb.SuperKeyProperty('1', kind='17', indexed=False)
    name = ndb.SuperStringProperty('2', required=True)
    complete_name = ndb.SuperTextProperty('3')# da je ovo indexable bilo bi idealno za projection query
    status = ndb.SuperIntegerProperty('4', required=True)
  
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @property
    def is_usable(self):
        return self.status
    
    @classmethod
    def delete(cls, values):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
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
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls)
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.complete_name = ndb.make_complete_name(entity, 'name', parent='parent_record')
                   # add task que to update all children
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.complete_name = ndb.make_complete_name(entity, 'name', parent='parent_record')
                   # add task que to update all children
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

 

# @todo
class Message(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 21
    
    # root
    outlet = ndb.SuperIntegerProperty('1', required=True, indexed=False)
    group = ndb.SuperIntegerProperty('2', required=True, indexed=False)
    state = ndb.SuperIntegerProperty('3', required=True)
 
    OBJECT_DEFAULT_STATE = 'composing'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'composing' : (1, ),
        'processing' : (2, ),
        'completed' : (3, ),
        'canceled' : (4, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'send' : 3,
       'complete' : 4,
       'cancel' : 5,
    }
    
    OBJECT_TRANSITIONS = {
        'send' : {
            'from' : ('composing',),
            'to' : ('processing',),
         },
        'complete' : {
           'from' : ('processing',),
           'to'   : ('completed',),
        },
        'cancel' : {
           'from' : ('composing',),
           'to'   : ('canceled',),
        },
    }
    
# @todo
class BillingCreditAdjustment(ndb.BaseModel):
    
    KIND_ID = 22
    
    # root (namespace Domain)
    # not logged
    adjusted = ndb.SuperDateTimeProperty('2', auto_now_add=True, indexed=False)
    agent = ndb.SuperKeyProperty('3', kind='app.core.acl.User', required=True, indexed=False)
    amount = ndb.SuperDecimalProperty('4', required=True, indexed=False)
    message = ndb.SuperTextProperty('5')# soft limit 64kb - to determine char count
    note = ndb.SuperTextProperty('6')# soft limit 64kb - to determine char count
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
    }    
     
     
class FeedbackRequest(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 23
    
    # ancestor User
    # ako hocemo da dozvolimo sva sortiranja, i dodatni filter po state-u uz sortiranje, onda nam trebaju slecedi indexi
    # composite index:
    # ancestor:yes - updated:desc; ancestor:yes - created:desc;
    # ancestor:yes - state,updated:desc; ancestor:yes - state,created:desc
    reference = ndb.SuperStringProperty('1', required=True, indexed=False)
    state = ndb.SuperIntegerProperty('2', required=True)
    updated = ndb.SuperDateTimeProperty('3', auto_now=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True)
 
    
    OBJECT_DEFAULT_STATE = 'new'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za state none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'new' : (1, ),
        'su_reviewing' : (2, ),
        'su_duplicate' : (3, ),
        'su_accepted' : (4, ),
        'su_dismissed' : (5, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'log_message' : 2,
       'sudo' : 3,
    }
    
    OBJECT_TRANSITIONS = {
        'su_review' : {
            'from' : ('new',),
            'to' : ('su_reviewing',),
         },
        'su_close' : {
           'from' : ('su_reviewing', ),
           'to'   : ('su_duplicate', 'su_accepted', 'su_dismissed',),
        },
    }

    @classmethod
    def manage(cls, create, values, **kwdss):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls, only=('reference',))
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
      
            if create:
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

# done! - sudo kontrolisan model
class SupportRequest(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 24
    
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
 
    
    OBJECT_DEFAULT_STATE = 'new'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za state none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'new' : (1, ),
        'su_opened' : (2, ),
        'su_awaiting_closure' : (3, ),
        'closed' : (4, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'log_message' : 2,
       'sudo' : 3,
       'close' : 4,
    }
    
    OBJECT_TRANSITIONS = {
        'su_open' : {
            'from' : ('new',),
            'to' : ('su_opened',),
         },
        'su_propose_close' : {
           'from' : ('su_opened', ),
           'to'   : ('su_awaiting_closure',),
        },
        'close' : {
           'from' : ('su_opened', 'su_awaiting_closure',),
           'to'   : ('closed',),
        },
    }
    
    @classmethod
    def list(cls, **kwds):
        response = ndb.Response()
        
        response['items'] = cls.query().order(-cls.created).fetch()
        
        return response
  
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
   