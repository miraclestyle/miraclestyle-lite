# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import mail, urlfetch

from app import ndb, memcache, util
from app.lib.safe_eval import safe_eval
from app.lib.attribute_manipulator import set_attr, get_attr


class Set(ndb.BaseModel):
  
  def run(self, context):
    MailTemplate = context.models['58']
    HttpTemplate = context.models['63']
    input_templates = context.input.get('templates')
    templates = []
    for template in input_templates:
      template.pop('class_', None)
      model = MailTemplate
      if template.get('kind') == '63':
        model = HttpTemplate
      fields = model.get_fields()
      for key, value in template.items():
        if key in fields:
          field = fields.get(key)
          if hasattr(field, 'format'):
            template[key] = field.format(value)  # Call format functions on simpleton json values.
        else:
          del template[key]
      templates.append(model(**template))
    context.values['61'].name = context.input.get('name')
    context.values['61'].action = context.input.get('action')
    context.values['61'].condition = context.input.get('condition')
    context.values['61'].active = context.input.get('active')
    context.values['61'].templates = templates


# @todo We have to consider http://sendgrid.com/partner/google
class MailSend(ndb.BaseModel):
  
  message_sender = ndb.SuperStringProperty('1', required=True, indexed=False)
  
  def run(self, context):
    # @todo We have to somehow hide recipients of the message from each other. Perhaps like this?
    message = mail.EmailMessage()
    message.sender = self.message_sender
    message.to = self.message_sender
    message.subject = context.input['subject']
    message.body = context.input['body']  # We can add html argument in addition to body if we want to send html version!
    message.bcc = context.input['recipient']
    message.check_initialized()
    message.send()


class HttpSend(ndb.BaseModel):
  
  def run(self, context):
    urlfetch.fetch(context.input.get('recipient'), json.dumps(context.input), method=urlfetch.POST)


class Initiate(ndb.BaseModel):
  
  def run(self, context):
    caller_user_key = context.input.get('caller_user')
    caller_action_key = context.input.get('caller_action')
    context.tmp['caller_user'] = caller_user_key.get()
    notifications = context.model.query(context.model.active == True,
                                        context.model.action == caller_action_key,
                                        namespace=context.tmp['caller_entity'].key_namespace).fetch()
    if notifications:
      for notification in notifications:
        values = {'entity': context.tmp['caller_entity'], 'user': context.tmp['caller_user']}
        if safe_eval(notification.condition, values):
          for template in notification.templates:
            template.run(context)
