# -*- coding: utf-8 -*-
'''
Created on Jun 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json

from google.appengine.api import taskqueue
from google.appengine.ext import blobstore
from google.appengine.api import mail
from google.appengine.api import urlfetch

from jinja2.sandbox import SandboxedEnvironment

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


sandboxed_jinja = SandboxedEnvironment()


def render_template(template_as_string, values={}):
  from_string_template = sandboxed_jinja.from_string(template_as_string)
  return from_string_template.render(values)


# @todo We have to consider http://sendgrid.com/partner/google
def mail_send(**kwargs):
  message_sender = kwargs.get('sender', None)
  if not message_sender:
    raise orm.TerminateAction()
  message = mail.EmailMessage()
  message.sender = message_sender
  message.bcc = kwargs['recipient']
  message.subject = render_template(kwargs['subject'], kwargs)
  message.body = render_template(kwargs['body'], kwargs) # We can add html argument in addition to body if we want to send html version!
  message.check_initialized()
  message.send()


def http_send(**kwargs):
  urlfetch.fetch(kwargs['recipient'], json.dumps(kwargs), method=urlfetch.POST)
