# -*- coding: utf-8 -*-
'''
Created on Jun 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import re
import json
import os

from google.appengine.ext import blobstore
from google.appengine.api import taskqueue, mail, urlfetch, channel
from jinja2 import Environment, evalcontextfilter, Markup, escape, FileSystemLoader
from webapp2_extras import securecookie

import orm
import settings
from .util import normalize

__all__ = ['rule_prepare', 'rule_exec', 'callback_exec', 'blob_create_upload_url', 'render_template',
           'channel_create', 'mail_send', 'http_send', 'channel_send', 'secure_cookie']


def rule_prepare(entities, **kwargs):
  entities = normalize(entities)
  for entity in entities:
    if entity and isinstance(entity, orm.Model):
      entity.rule_prepare(getattr(entity, '_permissions', []), **kwargs)


def rule_exec(entity, action):
  if entity and hasattr(entity, '_action_permissions'):
    if not entity._action_permissions[action.key_id_str]['executable']:
      raise orm.ActionDenied(action)
  else:
    raise orm.ActionDenied(action)


def callback_exec(url, callbacks):
  callbacks = normalize(callbacks)
  queues = {}
  if orm.in_transaction() and len(callbacks) > 5:
    raise ValueError('When in transaction, only up to 5 callbacks are allowed. You provided %s.' % len(callbacks))
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


def render_template(string_template, values={}):
  template = jinja_env.from_string(string_template)
  return template.render(values)


def channel_create(token):
  return channel.create_channel(token)


# @note We have to consider http://sendgrid.com/partner/google
def mail_send(data):
  message_sender = data.get('sender', None)
  if not message_sender:
    raise ValueError('`sender` not found in data')
  message = mail.EmailMessage()
  message.sender = message_sender
  message.bcc = data['recipient']
  message.subject = render_template(data['subject'], data).strip()
  message.html = render_template(data['body'], data).strip()
  message.body = message.html
  message.check_initialized()
  message.send()


def http_send(data):
  data['subject'] = render_template(data['subject'], data).strip()
  data['body'] = render_template(data['body'], data).strip()
  urlfetch.fetch(data['recipient'], json.dumps(data), method=urlfetch.POST)


def channel_send(data):
  message = {'action_id': data['action'].key_id_str, 'body': render_template(data['body'], data).strip()}
  return channel.send_message(data['recipient'], json.dumps(message))

secure_cookie = securecookie.SecureCookieSerializer(settings.COOKIE_SECRET)
