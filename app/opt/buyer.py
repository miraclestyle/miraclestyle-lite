# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.srv import rule, io, log

# buyer is not fully done, collections are at 50%
 
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
                                                rule.ActionPermission('9', io.Action.build_key('9-0').urlsafe(), True, "context.rule.entity.owner.key == context.auth.user.key and (not context.auth.user.is_guest)"),
                                                rule.ActionPermission('9', io.Action.build_key('9-1').urlsafe(), True, "context.rule.entity.owner.key == context.auth.user.key and (not context.auth.user.is_guest)"),
                                               ])
 
    _expando_fields = {
        'region' :  ndb.SuperKeyProperty('8', kind='16'),
        'email' : ndb.SuperStringProperty('10'),
        'telephone' : ndb.SuperStringProperty('11'),
    }

    _actions = {
       'manage' : io.Action(id='9-0',
                              arguments={
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'country' : ndb.SuperKeyProperty(kind='15', required=True),
                                 'city' : ndb.SuperStringProperty(required=True),
                                 'postal_code' : ndb.SuperStringProperty(required=True),
                                 'street' : ndb.SuperStringProperty(required=True),
                                 'default_shipping' : ndb.SuperBooleanProperty(default=True),
                                 'default_billing' : ndb.SuperBooleanProperty(default=True),
                                 
                                 'key' : ndb.SuperKeyProperty(kind='9'),
                                 
                                  # expando
                                 'region' :  ndb.SuperKeyProperty(kind='16'),
                                 'email' : ndb.SuperStringProperty(),
                                 'telephone' : ndb.SuperStringProperty(),
                              }
                             ),
                
       'delete' : io.Action(id='9-1',
                              arguments={
                                 'address' : ndb.SuperKeyProperty(kind='9', required=True),
                              }
                             ),
                
       'list' : io.Action(id='9-2',
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
                          
               entity_key = context.args.get('key')
               entity = entity_key.get()
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
                   entity_key = context.args.get('key')
                   if not entity_key:
                      return context.not_found()
                   entity = entity_key.get()
                   
                if 'key' in set_args:
                   del set_args['key']
              
                context.rule.entity = entity
                rule.Engine.run(context)
                
                if not rule.executable(context):
                   return context.not_authorized()
             
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
 

    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('10', io.Action.build_key('10-0').urlsafe(),
                                                                     True, "context.rule.entity.owner.key == context.auth.user.key and (not context.auth.user.is_guest)"),
                                                rule.ActionPermission('10', io.Action.build_key('10-1').urlsafe(),
                                                                     True, "context.rule.entity.owner.key == context.auth.user.key and (not context.auth.user.is_guest)"),
                                               ])
 

    _actions = {
       'manage' : io.Action(id='10-0',
                              arguments={
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'notify' : ndb.SuperBooleanProperty(default=False),
                                 'key' : ndb.SuperKeyProperty(kind='10'),
                              }
                             ),
                
       'delete' : io.Action(id='10-1',
                              arguments={
                                  'key' : ndb.SuperKeyProperty(kind='10', required=True),
                              }
                             ),
                
       'list' : io.Action(id='10-2',
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
              
           context.response['collections'] = cls.query(ancestor=user.key).fetch()
              
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
      
    @classmethod
    def manage(cls, args):
        
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
                   entity_key = context.args.get('key')
                   if not entity_key:
                      return context.not_found()
                   entity = entity_key.get()
                   
                if 'key' in set_args:
                   del set_args['key']
              
                context.rule.entity = entity
                rule.Engine.run(context)
                
                if not rule.executable(context):
                   return context.not_authorized()
                
                entity.primary_email = context.auth.user.primary_email
                entity.populate(**set_args)
                entity.put()
                 
                context.log.entities.append((entity, ))
                log.Engine.run(context)
                   
                context.status(entity)
               
            try:
                transaction()
            except Exception as e:
                context.transaction_error(e)
            
        return context
 

# done!
class CollectionCompany(ndb.BaseModel):
    
    _kind = 11
    # ancestor User
    company = ndb.SuperKeyProperty('1', kind='44', required=True)
    collections = ndb.SuperKeyProperty('2', kind='10', repeated=True)# soft limit 500x

 

    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('11', io.Action.build_key('11-0').urlsafe(),
                                                                     True, "context.rule.entity.owner.key == context.auth.user.key and (not context.auth.user.is_guest)"),
                                                rule.ActionPermission('11', io.Action.build_key('11-1').urlsafe(),
                                                                     True, "context.rule.entity.owner.key == context.auth.user.key and (not context.auth.user.is_guest)"),
                                               ])
 

    _actions = {
       'manage' : io.Action(id='11-0',
                              arguments={
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'key' : ndb.SuperKeyProperty(kind='11'),
                                 'company' : ndb.SuperKeyProperty(kind='44', required=True),
                                 'collections' : ndb.SuperKeyProperty(kind='10', repeated=True),
                              }
                             ),
                
       'delete' : io.Action(id='11-1',
                              arguments={
                                 'key' : ndb.SuperKeyProperty(kind='11', required=True),
                              }
                             ),
                
       'list' : io.Action(id='11-2',
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
              
           context.response['collection_companies'] = cls.query(ancestor=user.key).fetch()
              
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
      
    @classmethod
    def manage(cls, args):
        
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
                   entity_key = context.args.get('key')
                   if not entity_key:
                      return context.not_found()
                   entity = entity_key.get()
                   
                if 'key' in set_args:
                   del set_args['key']
              
                context.rule.entity = entity
                rule.Engine.run(context)
                
                if not rule.executable(context):
                   return context.not_authorized()
                
                company_key = context.args.get('company')
                company = company_key.get()
                
                if company.state != 'active': 
                   # how to solve this? possible solution might be ndb.SuperKeyProperty(kind=Company, expr="value.state == 'active'", required=True) - this would be placed in arguments={}
                   return context.error('company', 'not_active')
                
                collection_keys = context.args.get('collections')
                collections_now = []
                for collection_key in collection_keys:
                    if context.auth.user.key == collection_key.parent():
                       collections_now.append(collection_key)
                
                entity.company = company_key
                entity.collections = collections_now
                entity.put()
                 
                context.log.entities.append((entity, ))
                log.Engine.run(context)
                   
                context.status(entity)
               
            try:
                transaction()
            except Exception as e:
                context.transaction_error(e)
            
        return context
  
    
# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class AggregateCollectionCatalog(ndb.BaseModel):
    
    _kind = 12
    
    # ancestor User
    # not logged
    # task queue radi agregaciju prilikom nekih promena na store-u
    # mogao bi da se uvede index na collections radi filtera: AggregateBuyerCollectionCatalog.collections = 'collection', 
    # ovaj model bi se trebao ukinuti u korist MapReduce resenja, koje bi bilo superiornije od ovog
    # composite index: ancestor:yes - catalog_published_date:desc
    company = ndb.SuperKeyProperty('1', kind='44', required=True)
    collections = ndb.SuperKeyProperty('2', kind='10', repeated=True, indexed=False)# soft limit 500x
    catalog = ndb.SuperKeyProperty('3', kind='35', required=True, indexed=False)
    catalog_cover = ndb.SuperBlobKeyProperty('4', required=True, indexed=False)# blob ce se implementirati na GCS
    catalog_published_date = ndb.SuperDateTimeProperty('5', required=True)
