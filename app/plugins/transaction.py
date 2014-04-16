# -*- coding: utf-8 -*-
'''
Created on Apr 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, settings
from app.srv import event, log, callback

class Write(event.Plugin):
  
  @ndb.transactional(xg=True)  # @todo Study material. Perhaps 'context.transaction.group' can be context.entity, and 'context.transaction.entities' could be context.entity._entries ??
  def run(self, context):
    group = context.transaction.group
    if not group:
      group = Group(namespace=context.auth.domain.key.urlsafe())  # ??
      group.put()
      group_key = group.key  # Put main key.
      for key, entry in context.transaction.entities.items():
        entry.set_key(parent=group_key)  # parent key for entry
        entry_key = entry.put()
        lines = []
        for i, line in enumerate(entry._lines):
          line.set_key(parent=entry_key, id=i)  # @todo Parent key for line, and if posible, sequence value should be key.id?
          lines.append(line)
          ndb.put_multi(lines)