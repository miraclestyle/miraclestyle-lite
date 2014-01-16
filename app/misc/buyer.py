# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.srv import rule, event, log

# buyer is not fully done, collections are at 50%
 
class Address(ndb.BaseExpando):
    
    _kind = 9
    # ancestor User
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    country = ndb.SuperKeyProperty('2', kind='app.srv.location.Country', required=True, indexed=False)
    city = ndb.SuperStringProperty('3', required=True, indexed=False)
    postal_code = ndb.SuperStringProperty('4', required=True, indexed=False)
    street_address = ndb.SuperStringProperty('5', required=True, indexed=False)
    default_shipping = ndb.SuperBooleanProperty('6', default=True, indexed=False)
    default_billing = ndb.SuperBooleanProperty('7', default=True, indexed=False)
  
    _default_indexed = False
    
    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('9', event.Action.build_key('9-0').urlsafe(), True, "context.rule.entity.owner.key == context.auth.user.key and (not context.auth.user.is_guest)"),
                                                rule.ActionPermission('9', event.Action.build_key('9-1').urlsafe(), True, "context.rule.entity.owner.key == context.auth.user.key and (not context.auth.user.is_guest)"),
                                               ])
 
    _expando_fields = {
        'region' :  ndb.SuperKeyProperty('8', kind='app.srv.location.CountrySubdivision'),
        'street_address2' : ndb.SuperStringProperty('9'),
        'email' : ndb.SuperStringProperty('10'),
        'telephone' : ndb.SuperStringProperty('11'),
    }

    _actions = {
       'manage' : event.Action(id='9-0',
                              arguments={
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'country' : ndb.SuperKeyProperty(kind='app.srv.location.Country', required=True),
                                 'city' : ndb.SuperStringProperty(required=True),
                                 'postal_code' : ndb.SuperStringProperty(required=True),
                                 'street_address' : ndb.SuperStringProperty(required=True),
                                 'default_shipping' : ndb.SuperBooleanProperty(default=True),
                                 'default_billing' : ndb.SuperBooleanProperty(default=True),
                                 
                                 'address' : ndb.SuperKeyProperty(kind='9'),
                                 
                                  # expando
                                 'region' :  ndb.SuperKeyProperty(kind='app.srv.location.CountrySubdivision'),
                                 'street_address2' : ndb.SuperStringProperty(),
                                 'email' : ndb.SuperStringProperty(),
                                 'telephone' : ndb.SuperStringProperty(),
                              }
                             ),
                
       'delete' : event.Action(id='9-1',
                              arguments={
                                 'address' : ndb.SuperKeyProperty(kind='9', required=True),
                              }
                             ),
                
       'list' : event.Action(id='9-3',
                              arguments={}
                             ),
    }  
    
    @property
    def owner(self):
        return self.key.parent().get()
      
    @classmethod
    def list(cls, args):
      
        action = cls._actions.get('list')
        context = action.process(args)
        
        if not context.has_error():
          
           user = context.auth.user
              
           context.response['addresses'] = cls.query(ancestor=user.key).fetch()
              
           return context
     
    @classmethod
    def delete(cls, args):
        
        action = cls._actions.get('delete')
        context = action.process(args)

        if not context.has_error():
          
          @ndb.transactional(xg=True)
          def transaction():
                          
               entity = context.args.get('address')
               context.rule.entity = entity
               rule.Engine.run(context, True)
               if not rule.executable(context):
                  return context.not_authorized()
                
               entity.key.delete()
               context.log.entities.append((entity,))
               log.Engine.run(context)
               
               context.response['deleted'] = True
               context.status(entity)
               
        try:
           transaction()
        except Exception as e:
           context.transaction_error(e)
           
        return context
      
    @classmethod
    def manage(cls, args): # im not sure if we are going to perform updates on multiple address instances - this is a UI thing
        
        action = cls._actions.get('manage')
        context = action.process(args)
  
        if not context.has_error():
          
            @ndb.transactional(xg=True)
            def transaction():
              
                create = context.args.get('create')
                set_args = context.args.copy()
                del set_args['create']
               
                if create:
                   entity = cls(parent=context.auth.user.key)
                else:
                   entity_key = context.args.get('address')
                   if not entity_key:
                      return context.not_found()
                   entity = entity_key.get()
                   
                if 'address' in set_args:
                   del set_args['address']
              
                context.rule.entity = entity
                rule.Engine.run(context)
                
                if not rule.executable(context):
                   return context.not_authorized()
             
                entity.populate(**set_args)
                entity.put()
                
                     
                all_addresses = cls.query(ancestor=context.auth.user.key).fetch()
                
                for address in all_addresses:
                    if address.key != entity.key:
                      if set_args.get('default_shipping'):
                         address.default_shipping = False
                      if set_args.get('default_billing'):
                         address.default_billing = False
                         
                ndb.put_multi(all_addresses) # no need to log default_billing and default_shipping, doesnt make sense
                
                context.log.entities.append((entity, ))
                log.Engine.run(context)
                   
                context.status(entity)
               
            try:
                transaction()
            except Exception as e:
                context.transaction_error(e)
            
        return context
    
            
# done!
class Collection(ndb.BaseModel):
    
    _kind = 10
    
    # ancestor User
    # mozda bude trebao index na primary_email radi mogucnosti update-a kada user promeni primarnu email adresu na svom profilu
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    notify = ndb.SuperBooleanProperty('2', required=True, default=False)
    primary_email = ndb.SuperStringProperty('3', required=True, indexed=False)
 
    @classmethod
    def list(cls, values):
        response = ndb.Response()
        
        response['items'] = cls.query(ancestor=ndb.get_current_user().key).fetch()
        
        return response
 
    @classmethod
    def manage(cls, create, values, **kwds):
   
        response = ndb.Response()
        
        @ndb.transactional(xg=True)
        def transaction():
            
            current = ndb.get_current_user()
            
            if current.is_guest:
               return response.not_logged_in()
            
            response.process_input(values, cls, skip=('primary_email',))
             
            if not response.has_error():
 
                entity = cls.prepare(create, values, parent=current.key)
                
                # we internally set primary_email, not from user input    
                entity.primary_email = current.primary_email
                
                if entity is None:
                    return response.not_found()
        
                if not create:
    
                   if entity.key.parent() == current.key:
                       entity.put()
                       entity.new_action('update')
                       entity.record_action()
                       
                       response.status(entity)
                   else:
                       return response.not_authorized()
                   
                else:
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
                   
                   response.status(entity)
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response
    
    @classmethod
    def delete(cls, values, **kwds):
 
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
 

# done!
class CollectionCompany(ndb.BaseModel):
    
    _kind = 11
    # ancestor User
    company = ndb.SuperKeyProperty('1', kind='app.domain.business.Company', required=True)
    collections = ndb.SuperKeyProperty('2', kind='app.core.buyer.Collection', repeated=True)# soft limit 500x
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @classmethod
    def delete(cls, values, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  if entity.key.parent() == current.key:
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
        
        @ndb.transactional
        def transaction():
            
            current = ndb.get_current_user()
            
            if current.is_guest:
               return response.not_logged_in()
           
            response.process_input(values, cls)
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
            
            collection_keys = values.get('collections')
            company_key = values.get('company')
  
            if entity is None:
               return response.not_found()
           
            entity.collections = []
                  
            for c in collection_keys:
                if c.parent() == current.key:
                     entity.collections.append(c)
            
            if not create:
               if entity.key.parent() == current.key:
                  entity.put()
                  entity.new_action('update')
                  entity.record_action()
               else:
                  return response.not_authorized()
            else:
                entity = cls(parent=current.key, collections=collection_keys, company=company_key)
                entity.put()
                entity.new_action('create')
                entity.record_action()
                
            # @todo izaziva se update AggregateBuyerCollectionCatalog preko task queue 
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response
  
    
# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class AggregateCollectionCatalog(ndb.BaseModel):
    
    _kind = 12
    
    # ancestor User
    # not logged
    # task queue radi agregaciju prilikom nekih promena na store-u
    # mogao bi da se uvede index na collections radi filtera: AggregateBuyerCollectionCatalog.collections = 'collection', 
    # ovaj model bi se trebao ukinuti u korist MapReduce resenja, koje bi bilo superiornije od ovog
    # composite index: ancestor:yes - catalog_published_date:desc
    company = ndb.SuperKeyProperty('1', kind='app.domain.business.Company', required=True)
    collections = ndb.SuperKeyProperty('2', kind='app.core.buyer.Collection', repeated=True, indexed=False)# soft limit 500x
    catalog = ndb.SuperKeyProperty('3', kind='app.domain.marketing.Catalog', required=True, indexed=False)
    catalog_cover = ndb.SuperBlobKeyProperty('4', required=True, indexed=False)# blob ce se implementirati na GCS
    catalog_published_date = ndb.SuperDateTimeProperty('5', required=True)
