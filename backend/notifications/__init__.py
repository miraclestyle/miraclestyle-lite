# -*- coding: utf-8 -*-
'''
Created on Jan 16, 2015

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)

Jinja2 flavored notification templates

variables available for every template ['account', 'sender', 'entity', 'input', 'action', 'subject', 'body']
+ dynamic and static data
'''

import codecs
import os


def template(path):
  try:
    return codecs.open(os.path.join(os.path.dirname(__file__), 'templates', path), 'r', 'utf-8').read()
  except IOError as e:
    return 'Notification template not created at path %s' % path


ACCOUNT_SUDO_SUBJECT = template('account/sudo_subject.html')
ACCOUNT_SUDO_BODY = template('account/sudo_body.html')

CATALOG_PUBLISH_SUBJECT = template('catalog/publish_subject.html')
CATALOG_PUBLISH_BODY = template('catalog/publish_body.html')

CATALOG_SUDO_SUBJECT = template('catalog/sudo_subject.html')
CATALOG_SUDO_BODY = template('catalog/sudo_body.html')

CATALOG_DISCONTINUE_SUBJECT = template('catalog/discontinue_subject.html')
CATALOG_DISCONTINUE_BODY = template('catalog/discontinue_body.html')

ORDER_LOG_MESSAGE_SUBJECT = template('order/log_message_subject.html')
ORDER_LOG_MESSAGE_BODY = template('order/log_message_body.html')

ORDER_NEW_MESSAGES_SUBJECT = template('order/new_messages_subject.html')
ORDER_NEW_MESSAGES_BODY = template('order/new_messages_body.html')

ORDER_NOTIFY_SUBJECT = template('order/notify_subject.html')
ORDER_NOTIFY_BODY = template('order/notify_body.html')