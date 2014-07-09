# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, util


class BuildMenu(ndb.BaseModel):
  
  def run(self, context):
    model = context._model
    domain_user_key = ndb.Key('8', context._user.key_id_str, namespace=context._namespace)
    domain_user = domain_user_key.get()
    if domain_user:
      widgets = model.query(model.active == True,
                            model.role.IN(domain_user.roles),
                            namespace=context._namespace).order(model.sequence).fetch()
      context.tmp['widgets'] = widgets
