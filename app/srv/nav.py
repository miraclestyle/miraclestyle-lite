# -*- coding: utf-8 -*-
'''
Created on Feb 24, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.srv import rule


class Filter(ndb.BaseExpando):
 
  # Local structured property
  
  name = ndb.SuperStringProperty('1', required=True) # name that is visible on the link
  kind = ndb.SuperStringProperty('3', required=True) # which model (entity kind) this filter affects
  query = ndb.SuperJsonProperty('4', required=True) # query parameters that are passed to search function of the model


class Widget(ndb.BaseExpando):
  
  _kind = 61
  
  # root (namespace Domain)
  
  name = ndb.SuperStringProperty('1', required=True) # name of the fieldset
  sequence = ndb.SuperIntegerProperty('2', required=True) # global sequence for ordering purposes
  active = ndb.SuperBooleanProperty('3', default=True) # whether this item is active or not
  role = ndb.SuperKeyProperty('4', kind='60', required=True) # to which role this group is attached
  search_form = ndb.SuperBooleanProperty('5', default=True) # whether this group is search form or set of filter buttons/links
  filters = ndb.SuperLocalStructuredProperty(Filter, '6', repeated=True)
  
  @classmethod
  def get_local_widgets(cls, domain, role):
    return cls.query(cls.active == True,
                     cls.role == role,
                     namespace=domain.key_namespace).order(cls.sequence).fetch()
   
   
class Engine:
  
  @classmethod
  def run(cls, context):
    domain_key = context.input.get('domain')
    domain = domain_key.get()
    domain_user_key = rule.DomainUser.build_key(context.auth.user.key_id_str, namespace=domain.key.urlsafe())
    domain_user = domain_user_key.get()
    if domain_user:
       context.output['menu'] = Widget.get_local_widgets(domain, domain_user.roles)