# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.api import blobstore

from app import ndb, settings
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


class Read(event.Plugin):
  
  def run(self, context):
    # @todo Async operations effectively require two separate plugins
    # that will be separated by intermediate plugins, in order to prove to be useful!
    # This separation for async ops has to be decided yet!
    # Right now async is eliminated!
    #primary_contact = context.entities['6'].primary_contact.get_async()
    #primary_contact = primary_contact.get_result()
    primary_contact = context.entities['6'].primary_contact.get()
    context.entities['6']._primary_contact_email = primary_contact._primary_email


class Prepare(event.Plugin):
  
  def run(self, context):
    context.output['upload_url'] = blobstore.create_upload_url(context.input.get('upload_url'), gs_bucket_name=settings.COMPANY_LOGO_BUCKET)


class Search(event.Plugin):
  
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
