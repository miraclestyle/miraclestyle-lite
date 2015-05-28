# -*- coding: utf-8 -*-
'''
Created on Jun 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import re
import json
import os

from google.appengine.api import taskqueue
from google.appengine.ext import blobstore
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api import channel

from jinja2 import Environment, evalcontextfilter, Markup, escape, FileSystemLoader

import orm
from util import *


def rule_prepare(entities, strict, **kwargs):
  entities = normalize(entities)
  for entity in entities:
    if entity and isinstance(entity, orm.Model):
      permissions = []
      if hasattr(entity, '_global_role') and entity._global_role.get_kind() == '7':
        permissions.extend(entity._global_role.permissions)
      entity.rule_prepare(permissions, strict, **kwargs)


def rule_exec(entity, action):
  if entity and hasattr(entity, '_action_permissions'):
    if not entity._action_permissions[action.key_urlsafe]['executable']:
      raise orm.ActionDenied(action)
  else:
    raise orm.ActionDenied(action)


def callback_exec(url, callbacks):
  callbacks = normalize(callbacks)
  queues = {}
  if orm.in_transaction():
    callbacks = callbacks[:5]
  if len(callbacks):
    for callback in callbacks:
      if callback and isinstance(callback, (list, tuple)) and len(callback) == 2:
        queue_name, data = callback
        if data:
          if queue_name not in queues:
            queues[queue_name] = []
          queues[queue_name].append(taskqueue.Task(url=url, payload=json.dumps(data), target='backend'))
  if len(queues):
    for queue_name, tasks in queues.iteritems():
      queue = taskqueue.Queue(name=queue_name)
      queue.add(tasks, transactional=orm.in_transaction())


def blob_create_upload_url(upload_url, gs_bucket_name):
  return blobstore.create_upload_url(upload_url, gs_bucket_name=gs_bucket_name)

jinja_env = Environment(loader=FileSystemLoader([os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notifications', 'templates')]))

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n')
                          for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

jinja_env.filters['nl2br'] = nl2br


def render_template(template_as_string, values={}):
  from_string_template = jinja_env.from_string(template_as_string)
  return from_string_template.render(values)

def channel_create(token):
  return channel.create_channel(token)


# @todo We have to consider http://sendgrid.com/partner/google
def mail_send(**kwargs):
  message_sender = kwargs.get('sender', None)
  if not message_sender:
    raise ValueError('`sender` not found in kwargs')
  message = mail.EmailMessage()
  message.sender = message_sender
  message.bcc = kwargs['recipient']
  message.subject = render_template(kwargs['subject'], kwargs).strip()
  message.html = render_template(kwargs['body'], kwargs).strip()
  message.body = message.html
  message.check_initialized()
  message.send()


def http_send(**kwargs):
  kwargs['subject'] = render_template(kwargs['subject'], kwargs).strip()
  kwargs['body'] = render_template(kwargs['body'], kwargs).strip()
  urlfetch.fetch(kwargs['recipient'], json.dumps(kwargs), method=urlfetch.POST)


def channel_send(**kwargs):
  message = {'action_id': kwargs['action'].key_id_str, 'body': render_template(kwargs['body'], kwargs).strip(), 'subject': render_template(kwargs['subject'], kwargs).strip()}
  return channel.send_message(kwargs['recipient'], json.dumps(message))
