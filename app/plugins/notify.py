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
  
  def run(self, context):
    '''
     the first 4 arguments that are specified must be named correctly, otherwise the mail_send will throw an error
     if function explicitly asks for arguments
     def func(arg1, arg2, arg3, **kwds):
       pass
       
     then you must call the function like this func(arg1='foo', arg2='bar', arg3='baaz', # if you dont call these it will throw an error other=1, kwd=2, arguments=3) etc..
    '''
    mail.send_mail(sender=context.input['sender'],
              to=context.input['recipient'],
              subject=context.input['subject'],
              body=context.input['body'])  # 'html' can be replaced with 'body' argument if we decide to implement plain text.
    # as for html ones
    # html keyword can be used, along with the body one
    # http://stackoverflow.com/questions/2860614/send-html-e-mail-in-app-engine-python


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
