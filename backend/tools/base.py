# -*- coding: utf-8 -*-
'''
Created on Jun 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import re
import json
import os
import urllib
import urlparse
import webapp2
import datetime
import json

from google.appengine.ext import blobstore
from google.appengine.api import taskqueue, mail, urlfetch, channel
from jinja2 import Environment, evalcontextfilter, Markup, escape, FileSystemLoader
from webapp2_extras import securecookie

import orm
import settings
from .util import normalize
from .debug import log

__all__ = ['rule_prepare', 'rule_exec', 'callback_exec', 'blob_create_upload_url', 'render_template', 'render_subject_and_body_templates',
           'channel_create', 'json_dumps', 'json_loads', 'mail_send', 'http_send', 'channel_send', 'secure_cookie']


class JSONEncoder(json.JSONEncoder):

  '''An encoder that produces JSON safe to embed in HTML.
  To embed JSON content in, say, a script tag on a web page, the
  characters &, < and > should be escaped. They cannot be escaped
  with the usual entities (e.g. &amp;) because they are not expanded
  within <script> tags.
  Also its `default` function will properly format data that is usually not serialized by json standard.
  '''

  def default(self, obj):
    if isinstance(obj, datetime.datetime):
      return obj.strftime(settings.DATETIME_FORMAT)
    if isinstance(obj, orm.Key):
      return obj.urlsafe()
    if hasattr(obj, 'get_output'):
      try:
        return obj.get_output()
      except TypeError as e:
        pass
    if hasattr(obj, 'get_meta'):
      try:
        return obj.get_meta()
      except TypeError as e:
        pass
    try:
      return str(obj)
    except TypeError as e:
      pass
    return json.JSONEncoder.default(self, obj)


def json_dumps(s, **kwargs):
  defaults = {'check_circular': False, 'cls': JSONEncoder}
  defaults.update(kwargs)
  return json.dumps(s, **defaults)

json_loads = json.loads


def _to_utf8(value):
  """Encodes a unicode value to UTF-8 if not yet encoded."""
  if isinstance(value, str):
    return value

  return value.encode('utf-8')


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

JINJA_ENV = Environment(loader=FileSystemLoader([os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notifications', 'templates')]))


def absolute_url(path):
  return '%s/%s' % (settings.get_host_url(webapp2.get_request().host), path)


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@evalcontextfilter
def nl2br(eval_ctx, value):
  result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br />\n'))
                        for p in _paragraph_re.split(escape(value)))
  if eval_ctx.autoescape:
    result = Markup(result)
  return result


@evalcontextfilter
def format_date(eval_ctx, value):
  if not value:
    return value
  return value.strftime('%-d %b %Y, %H:%M')

JINJA_ENV.filters['nl2br'] = nl2br
JINJA_ENV.globals['absolute_url'] = absolute_url
JINJA_ENV.globals['datetime_now'] = lambda: datetime.datetime.now()
JINJA_ENV.filters['format_date'] = format_date
JINJA_ENV.globals['is_list'] = lambda x: isinstance(x, (list, tuple))
JINJA_ENV.globals['is_str'] = lambda x: isinstance(x, basestring)


def render_template(string_template, values={}):
  template = JINJA_ENV.from_string(string_template)
  return template.render(values)


def channel_create(token):
  return channel.create_channel(token)


def render_subject_and_body_templates(data):
  data['body'] = render_template(data['body'], data).strip()
  data['subject'] = render_template(data['subject'], data).strip()
  return data

# @note We have to consider http://sendgrid.com/partner/google
def mail_send(data, render=True):
  message_sender = data.get('sender', None)
  if not message_sender:
    raise ValueError('`sender` not found in data')
  if render:
    render_subject_and_body_templates(data)
  if settings.DEBUG:
    log.debug([data['subject'], data['body']])
  message = mail.EmailMessage()
  message.sender = message_sender
  message.bcc = data['recipient']
  message.subject = data['subject']
  message.html = data['body']
  message.body = message.html
  message.check_initialized()
  message.send()


def http_send(data):
  render_subject_and_body_templates(data)
  urlfetch.fetch(data['recipient'], json.dumps(data), deadline=60, method=urlfetch.POST)


def channel_send(data):
  body = ''
  if 'body' in data:
    body = data['body']
  extra = {'action_id': data['action'].key_id_str, 'body': render_template(body, data).strip()}
  output = data.copy()
  for k in ('account', 'action', 'input', 'entity'):
    del output[k]
  output.update(extra)
  return channel.send_message(data['recipient'], json.dumps(output))

secure_cookie = securecookie.SecureCookieSerializer(settings.COOKIE_SECRET)
