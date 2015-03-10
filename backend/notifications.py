# -*- coding: utf-8 -*-
'''
Created on Jan 16, 2015

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)

Jinja2 flavored notification templates

variables available for every template ['account', 'sender', 'entity', 'input', 'action', 'subject', 'body']
+ dynamic and static data
'''

ACCOUNT_SUDO_SUBJECT = '''
{% if admin %}
    Account {{entity._primary_email}} has been {% if entity.state == "suspended" %}suspended{% else %}activated{% endif %} by {{account._primary_email}}
{% else %}
    {% if entity.state == "suspended" %}
    Your account {{entity._primary_email}} has been suspended.
    {% else %}
    Your account {{entity._primary_email}} has been activated.
    {% endif %}
{% endif %}
'''

ACCOUNT_SUDO_BODY = '''
{% if admin %}
    Note: <br />
    {{input.note|safe|nl2br}}
{% else %}
    {% if entity.state == "suspended" %}
    Your account {{entity._primary_email}} has been suspended.<br />
    Message from admin:<br />
    {{input.message|safe|nl2br}}
    {% else %}
    Your account {{entity._primary_email}} has been activated.<br />
    Message from admin:<br />
    {{input.message|safe|nl2br}}
    {% endif %}
{% endif %}
'''

CATALOG_PUBLISH_SUBJECT = 'text'
CATALOG_PUBLISH_BODY = 'text'

CATALOG_SUDO_SUBJECT = 'text'
CATALOG_SUDO_BODY = 'text'

CATALOG_CATALOG_PROCESS_DUPLICATE_SUBJECT = 'Catalog sucessfully duplicated.'
CATALOG_CATALOG_PROCESS_DUPLICATE_BODY = 'Your catalog has been sucessfully duplicated.'

CATALOG_PRICETAG_PROCESS_DUPLICATE_SUBJECT = 'Pricetag successfully duplicated.'
CATALOG_PRICETAG_PROCESS_DUPLICATE_BODY = 'Your pricetag has been successfully duplicated.'

CATALOG_DISCONTINUE_SUBJECT = 'text'
CATALOG_DISCONTINUE_BODY = 'text'

ORDER_COMPLETE_SUBJECT = 'text'
ORDER_COMPLETE_BODY = 'text'

ORDER_REVIEW_FEEDBACK_SUBJECT = 'text'
ORDER_REVIEW_FEEDBACK_BODY = 'text'

ORDER_REPORT_FEEDBACK_SUBJECT = 'text'
ORDER_REPORT_FEEDBACK_BODY = 'text'

ORDER_SUDO_FEEDBACK_SUBJECT = 'text'
ORDER_SUDO_FEEDBACK_BODY = 'text'

ORDER_LOG_MESSAGE_SUBJECT = 'text'
ORDER_LOG_MESSAGE_BODY = 'text'