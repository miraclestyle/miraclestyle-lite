# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import mail, urlfetch

from app import ndb, settings
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr


class Prepare(event.Plugin):
  
  def run(self, context):
    caller_entity_key = context.input.get('caller_entity')
    context.entities['caller_entity'] = caller_entity_key.get()  # @todo If user is taskqueue (as is expected to be) how do we handle it in rule?
    context.entities[context.model.get_kind()] = context.model(namespace=context.entities['caller_entity'].key_namespace)
    context.values[context.model.get_kind()] = context.model(namespace=context.entities['caller_entity'].key_namespace)



class MailSend(event.Plugin):
  
  def run(self, context):
    mail.send_mail(context.input['sender'], context.input['recipient'],
                   context.input['subject'], context.input['body'])


class HttpSend(event.Plugin):
  
  def run(self, context):
    urlfetch.fetch(context.input.get('recipient'), json.dumps(context.input), method=urlfetch.POST)


class Initiate(event.Plugin):
  
  def run(self, context):
    caller_user_key = context.input.get('caller_user')
    caller_action_key = context.input.get('caller_action')
    context.entities['caller_user'] = caller_user_key.get()
    templates = context.model.query(context.model.active == True,
                                    context.model.action == caller_action_key,
                                    namespace=context.entities['caller_user'].key_namespace).fetch()
    if templates:
      for template in templates:
        template.run(context)

      
      
class RolesAndUsers(event.Plugin):
  
  def run(self, context):
    from app.srv.rule import DomainUser, DomainRole
    context.output['users'] = DomainUser.query(namespace=context.output['entity'].key_namespace).fetch()
    context.output['roles'] = DomainRole.query(namespace=context.output['entity'].key_namespace).fetch()