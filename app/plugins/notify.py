# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import mail, urlfetch

from app import ndb, util
from app.tools.manipulator import safe_eval


# @todo This will be updated once we resolve set operation issue.
class Set(ndb.BaseModel):
  
  def run(self, context):
    MailTemplate = context._models['58']
    HttpTemplate = context._models['63']
    input_templates = context._input.get('templates')
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
    context.entities['61'].name = context._input.get('name')
    context.entities['61'].action = context._input.get('action')
    context.entities['61'].condition = context._input.get('condition')
    context.entities['61'].active = context._input.get('active')
    context.entities['61'].templates = templates


# @todo We have to consider http://sendgrid.com/partner/google
class MailSend(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    message_sender = self.cfg.get('sender', None)
    if not message_sender:
      raise ndb.TerminateAction()
    message = mail.EmailMessage()
    message.sender = message_sender
    message.bcc = context._input['recipient']
    message.subject = context._input['subject']
    message.body = context._input['body']  # We can add html argument in addition to body if we want to send html version!
    message.check_initialized()
    message.send()


class HttpSend(ndb.BaseModel):
  
  def run(self, context):
    urlfetch.fetch(context._input.get('recipient'), json.dumps(context._input), method=urlfetch.POST)


class Initiate(ndb.BaseModel):
  
  def run(self, context):
    caller_user_key = context._input.get('caller_user')
    caller_action_key = context._input.get('caller_action')
    context.tmp['caller_user'] = caller_user_key.get()
    notifications = context._model.query(context._model.active == True,
                                         context._model.action == caller_action_key,
                                         namespace=context.tmp['caller_entity'].key_namespace).fetch()
    if notifications:
      for notification in notifications:
        values = {'entity': context.tmp['caller_entity'], 'user': context.tmp['caller_user']}
        if safe_eval(notification.condition, values):
          for template in notification.templates:
            template.run(context)
