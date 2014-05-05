# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import os

from google.appengine.api import blobstore

from app import ndb, settings
from app.srv import event
from app.srv.setup import Configuration
from app.srv.rule import DomainUser
from app.lib.attribute_manipulator import set_attr, get_attr
from app.plugins import rule as plugin_rule


class UserLoginPrepare(event.Plugin):
  
  def run(self, context):
    

class UserIPAddress(event.Plugin):
  
  def run(self, context):
    context.ip_address = os.environ['REMOTE_ADDR']


class UserLogoutOutput(event.Plugin):
  
  def run(self, context):
    context.entities['0'].set_current_user(None, None)
    context.output['entity'] = context.entities['0'].current_user()


class UserReadDomains(event.Plugin):
  
  def run(self, context):
    entities = []
    if context.user.domains:
      
      @ndb.tasklet
      def async(domain):
        if domain:
          # Rule engine cannot run in tasklets because the context.rule.entity gets in wrong places for some reason... which
          # also causes rule engine to not work properly with _action_permissions, this i could not debug because it is impossible to determine what is going on in iterator
          domain_user_key = DomainUser.build_key(context.user.key_id_str, namespace=domain.key_namespace)
          domain_user = yield domain_user_key.get_async()
        raise ndb.Return(domain_user)
      
      @ndb.tasklet
      def helper(domains):
        domain_users = yield map(async, domains)
        raise ndb.Return(domain_users)
      
      context.domains = ndb.get_multi(context.user.domains)
      context.domain_users = helper(context.domains).get_result()


class UserUpdate(event.Plugin):
  
  def run(self, context):
    primary_email = context.input.get('primary_email')
    disassociate = context.input.get('disassociate')
    for identity in context.values['0'].identities:
      if disassociate:
        if identity.identity in disassociate:
          identity.associated = False
      if primary_email:
        identity.primary = False
        if identity.email == primary_email:
          identity.primary = True
          identity.associated = True


class UserSudo(event.Plugin):
  
  def run(self, context):
    if context.entities['0']._field_permissions['state']['writable'] and context.values['0'].state == 'suspended':
      context.values['0'].sessions = []


class DomainCreate(event.Plugin):
  
  def run(self, context):
    config_input = context.input.copy()
    domain_logo = config_input.get('domain_logo')
    blob.Manager.used_blobs(domain_logo.image)
    config_input['domain_primary_contact'] = context.user.key
    config = Configuration(parent=context.user.key, configuration_input=config_input, setup='setup_domain', state='active')
    config.put()
    context.entities[config.get_kind()] = config
    
class DomainRead(event.Plugin):
  
  def run(self, context):
    # @todo Async operations effectively require two separate plugins
    # that will be separated by intermediate plugins, in order to prove to be useful!
    # This separation for async ops has to be decided yet!
    # Right now async is eliminated!
    #primary_contact = context.entities['6'].primary_contact.get_async()
    #primary_contact = primary_contact.get_result()
    primary_contact = context.entities['6'].primary_contact.get()
    context.entities['6']._primary_contact_email = primary_contact._primary_email


class DomainPrepare(event.Plugin):
  
  def run(self, context):
    context.output['upload_url'] = blobstore.create_upload_url(context.input.get('upload_url'), gs_bucket_name=settings.COMPANY_LOGO_BUCKET)


class DomainSearch(event.Plugin):
  
  def run(self, context):
    @ndb.tasklet
    def async(entity):
      user = yield entity.primary_contact.get_async()
      entity._primary_contact_email = user._primary_email
      raise ndb.Return(entity)
    
    @ndb.tasklet
    def mapper(entities):
      entities = yield map(async, entities)
      raise ndb.Return(entities)
    
    context.entities = mapper(context.entities).get_result()
