# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import time
import hashlib

from app import ndb, util
from app.srv import log as ndb_log
from app.srv.event import Action
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.plugins import common, rule, log, callback, buyer
 
class Address(ndb.BaseExpando):
    
    _kind = 9
    # ancestor User
    # composite index: ancestor:yes - name
    internal_id = ndb.SuperStringProperty('1', required=True) # md5 hash => <timestamp>-<random_str>-<name>-<city>-<postal code>-<street>-<default_shipping>-<default_billing>
    name = ndb.SuperStringProperty('2', required=True)
    country = ndb.SuperKeyProperty('3', kind='15', required=True, indexed=False)
    city = ndb.SuperStringProperty('4', required=True, indexed=False)
    postal_code = ndb.SuperStringProperty('5', required=True, indexed=False)
    street = ndb.SuperStringProperty('6', required=True, indexed=False)
    default_shipping = ndb.SuperBooleanProperty('7', default=True, indexed=False)
    default_billing = ndb.SuperBooleanProperty('8', default=True, indexed=False)
    
    _country = None # prevent from expando saving
    _region = None # prevent from expando saving
  
    _default_indexed = False
    
    _expando_fields = {
        'region' :  ndb.SuperKeyProperty('9', kind='16'),
        'email' : ndb.SuperStringProperty('10'),
        'telephone' : ndb.SuperStringProperty('11'),
    }
    
    def get_output(self):
     dic = super(Address, self).get_output()
     dic['_country'] = getattr(self, '_country', None)
     dic['_region'] = getattr(self, '_region', None)
     return dic
    
    def generate_internal_id(self):
      internal_id = '%s-%s-%s-%s-%s-%s-%s-%s' %  (str(time.time()), util.random_chars(10), self.name,
       self.city, self.postal_code, self.street, self.default_shipping, self.default_billing)
      self.internal_id = hashlib.md5(internal_id).hexdigest()
    

class Addresses(ndb.BaseModel):
  
  _kind = 77
  
  addresses = ndb.SuperLocalStructuredProperty(Address, repeated=True)
  
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('10', repeated=True)
  }
  
  _global_role = GlobalRole(permissions=[
                   ActionPermission('77', Action.build_key('77', 'update').urlsafe(), True, "context.entity.key_parent == context.user.key and (not context.user._is_guest)"),
                   ActionPermission('77', Action.build_key('77', 'read').urlsafe(), True, "context.entity.key_parent == context.user.key and (not context.user._is_guest)"),
                   ActionPermission('77', Action.build_key('77', 'read_records').urlsafe(), True, "context.entity.key_parent == context.user.key and (not context.user._is_guest)"),
                   FieldPermission('77', ['addresses', '_records'], True, True, 'True'),
                 ])
 
  
  _actions = [
      Action(key=Action.build_key('77', 'update'),
            arguments={
                 'user': ndb.SuperKeyProperty(kind='0', required=True),
                 'addresses' : ndb.SuperLocalStructuredProperty(Address, repeated=True),
            },
            _plugins=[
              common.Context(),
              buyer.AddressRead(),
              buyer.AddressUpdate(),
              rule.Prepare(skip_user_roles=True, strict=False),
              rule.Exec(),
              rule.Write(transactional=True),
              common.Write(transactional=True),
              log.Entity(transactional=True),
              log.Write(transactional=True),
              rule.Read(transactional=True),
              common.Set(transactional=True, dynamic_values={'output.entity': 'entities.77'}),
              callback.Payload(transactional=True, queue = 'notify',
                               static_data = {'action_id': 'initiate', 'action_model': '77'},
                               dynamic_data = {'caller_entity': 'entities.77.key_urlsafe'}),
              callback.Exec(transactional=True, dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
              ]             
     ),       
    Action(
      key=Action.build_key('77', 'read'),
      arguments={
        'user': ndb.SuperKeyProperty(kind='0', required=True) # here we user key to retrieve "by user" addresses
        },
      _plugins=[
        common.Context(),
        buyer.AddressRead(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.77'})
        ]
      ),
      Action(
      key=Action.build_key('77', 'read_records'),
      arguments={
        'user': ndb.SuperKeyProperty(kind='0', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        buyer.AddressRead(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        log.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.77', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),       
  ]
  
  # this entire segment could be placed in plugins but at the moment this is the fastest method
  # because on every entity that gets trough output this function get_async_information() must be called to fetch the data async
  
  def get_output(self):
    self.get_async_information()
    return super(Addresses, self).get_output()
  
  def get_async_information(self):
    if self.addresses:
      
      @ndb.tasklet
      def async(addr):
        if addr.country:
          addr._country = yield addr.country.get_async() # discover convention name of these two or put them in virtual fields?
        if addr.region:
         addr._region = yield addr.region.get_async()
         raise ndb.Return(addr)
        
      @ndb.tasklet
      def helper(addresses):
        addresses = yield map(async, addresses)
        raise ndb.Return(addresses)
      
      self.addresses = helper(self.addresses).get_result()
     
            
# done!
class Collection(ndb.BaseModel):
    
  _kind = 10
  
  # ancestor User
  # mozda bude trebao index na primary_email radi mogucnosti update-a kada user promeni primarnu email adresu na svom profilu
  # composite index: ancestor:yes - name
  
  notify = ndb.SuperBooleanProperty('1', required=True, default=False)
  domains = ndb.SuperKeyProperty('2', kind='6', repeated=True, indexed=False)
 
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('10', repeated=True),
    '_domains' : ndb.SuperLocalStructuredProperty('6', repeated=True), # we need virtual domain prop so we can control what user can see in the domain results e.g. show only name, key, and logo
  }
    
  _global_role = GlobalRole(permissions=[
                 ActionPermission('10', Action.build_key('10', 'update').urlsafe(), True, "context.entity.key_parent == context.user.key and (not context.user._is_guest)"),
                 ActionPermission('10', Action.build_key('10', 'read').urlsafe(), True, "context.entity.key_parent == context.user.key and (not context.user._is_guest)"),
                 ActionPermission('77', Action.build_key('10', 'read_records').urlsafe(), True, "context.entity.key_parent == context.user.key and (not context.user._is_guest)"),
                 FieldPermission('10', ['notify', 'domains', '_records', '_domains'], True, True, 'True')
               ])
  
  _actions = [
      Action(key=Action.build_key('10', 'update'),
            arguments={
                 'user': ndb.SuperKeyProperty(kind='0', required=True),
                 'notify' : ndb.SuperBooleanProperty(default=True),
                 'domains' : ndb.SuperKeyProperty(kind='6', repeated=True),
            },
      _plugins=[
              common.Context(),
              buyer.CollectionRead(),
              common.Set(dynamic_values={'values.10.notify': 'input.notify', 'values.10.domains': 'input.domains'}),
              rule.Prepare(skip_user_roles=True, strict=False),
              rule.Exec(),
              rule.Write(transactional=True),
              common.Write(transactional=True),
              log.Entity(transactional=True),
              log.Write(transactional=True),
              rule.Read(transactional=True),
              common.Set(transactional=True, dynamic_values={'output.entity': 'entities.10'}),
              callback.Payload(transactional=True, queue = 'notify',
                               static_data = {'action_id': 'initiate', 'action_model': '10'},
                               dynamic_data = {'caller_entity': 'entities.10.key_urlsafe'}),
              callback.Exec(transactional=True, dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
              ]             
     ),
    Action(
      key=Action.build_key('10', 'read'),
      arguments={
         'user': ndb.SuperKeyProperty(kind='0', required=True) # here we use the user key instead of actual collection key to retrieve "by user" collection
        },
      _plugins=[
        common.Context(),
        buyer.CollectionRead(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.10'})
        ]
      ),
      Action(
      key=Action.build_key('10', 'read_records'),
      arguments={
        'user': ndb.SuperKeyProperty(kind='0', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        buyer.CollectionRead(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        log.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.10', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),    
   ]
  
  def get_output(self):
    self._domains = ndb.get_multi(self.domains)
    return super(Collection, self).get_output()
    
