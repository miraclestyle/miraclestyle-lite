# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm
from app.util import *


class WidgetBuildMenu(orm.BaseModel):
  
  def run(self, context):
    domain_user_key = orm.Key('8', context.user.key_id_str, namespace=context.namespace)
    domain_user = domain_user_key.get()
    if domain_user:
      context._widgets = context.model.query(context.model.active == True,
                                             context.model.role.IN(domain_user.roles),
                                             namespace=context.namespace).order(context.model.sequence).fetch()
