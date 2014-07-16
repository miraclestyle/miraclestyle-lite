# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import mail, urlfetch

from app import orm, util
from app.tools.manipulator import safe_eval


class NotifySet(orm.BaseModel):
  
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
          if hasattr(field, 'argument_format'):
            template[key] = field.argument_format(value)  # Call format functions on simpleton json values.
        else:
          del template[key]
      templates.append(model(**template))
    context._notification.name = context.input.get('name')
    context._notification.action = context.input.get('action')
    context._notification.condition = context.input.get('condition')
    context._notification.active = context.input.get('active')
    context._notification.templates = templates


# @todo We have to consider http://sendgrid.com/partner/google
class NotifyMailSend(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    message_sender = self.cfg.get('sender', None)
    if not message_sender:
      raise orm.TerminateAction()
    message = mail.EmailMessage()
    message.sender = message_sender
    message.bcc = context.input['recipient']
    message.subject = context.input['subject']
    message.body = context.input['body']  # We can add html argument in addition to body if we want to send html version!
    message.check_initialized()
    message.send()


class NotifyHttpSend(orm.BaseModel):
  
  def run(self, context):
    urlfetch.fetch(context.input.get('recipient'), json.dumps(context.input), method=urlfetch.POST)


class NotifyInitiate(orm.BaseModel):
  
  def run(self, context):
    caller_user_key = context.input.get('caller_user')
    caller_action_key = context.input.get('caller_action')
    context._caller_user = caller_user_key.get()
    notifications = context.model.query(context.model.active == True,
                                        context.model.action == caller_action_key,
                                        namespace=context._caller_entity.key_namespace).fetch()
    if notifications:
      for notification in notifications:
        values = {'entity': context._caller_entity, 'user': context._caller_user}
        if safe_eval(notification.condition, values):
          for template in notification.templates:
            callbacks = template.run({'caller_entity': context._caller_entity,
                                      'caller_user': context._caller_user,
                                      'models': context.models})
            context._callbacks.extend(callbacks)
