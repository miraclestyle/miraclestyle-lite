# -*- coding: utf-8 -*-
'''
Created on Apr 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, util


class DomainUserError(Exception):
  
  def __init__(self, message):
    self.message = {'domain_user': message}


class DomainRoleSet(ndb.BaseModel):
  
  def run(self, context):
    ActionPermission = context._models['79']
    FieldPermission = context._models['80']
    input_permissions = context._input.get('permissions')
    permissions = []
    for permission in input_permissions:
      if str(permission.get('kind')) == '80':
        permissions.append(FieldPermission(permission.get('model'),
                                           permission.get('fields'),
                                           permission.get('writable'),
                                           permission.get('visible'),
                                           permission.get('condition')))
      elif str(permission.get('kind')) == '79':
        permissions.append(ActionPermission(permission.get('model'),
                                            [ndb.Key(urlsafe=action_key) for action_key in permission.get('actions')],
                                            permission.get('executable'),
                                            permission.get('condition')))

    context.entities['60'].name = context._input.get('name')
    context.entities['60'].active = context._input.get('active')
    context.entities['60'].permissions = permissions


class DomainUserInvite(ndb.BaseModel):
  
  def run(self, context):
    User = context._models['0']
    email = context._input.get('email')
    user = User.query(User.emails == email).get()
    if not user:
      raise DomainUserError('not_found')
    if user.state != 'active':
      raise DomainUserError('not_active')
    already_invited = context._model.build_key(user.key_id_str, namespace=context._namespace).get()
    if already_invited:
      raise DomainUserError('already_invited')
    context.entities['8'] = context._model(id=user.key_id_str, namespace=context._namespace)
    input_roles = ndb.get_multi(context._input.get('roles'))
    roles = []
    for role in input_roles:
      if role.key.namespace() == context._namespace:
        roles.append(role.key)
    context.entities['8'].populate(name=context._input.get('name'), state='invited', roles=roles)
    user._use_rule_engine = False
    user.domains.append(context._domain.key)
    context.entities['0'] = user


class DomainUserRead(ndb.BaseModel):
  
  def run(self, context):
    user = ndb.Key('0', long(context.entities['8'].key.id())).get()
    context.entities['8']._primary_email = user._primary_email
    context.entities['0'] = user


class DomainUserUpdate(ndb.BaseModel):
  
  def run(self, context):
    input_roles = ndb.get_multi(context._input.get('roles'))
    roles = []
    # Avoid rogue roles.
    for role in input_roles:
      if role.key.namespace() == context.entities['8'].key_namespace:
        roles.append(role.key)
    context.entities['8'].name = context._input.get('name')
    context.entities['8'].roles = roles


class DomainUserRemove(ndb.BaseModel):
  
  def run(self, context):
    context.entities['0']._use_rule_engine = False
    context.entities['0'].domains.remove(ndb.Key(urlsafe=context.entities['8'].key_namespace))


class DomainUserCleanRoles(ndb.BaseModel):
  
  def run(self, context):
    roles = ndb.get_multi(context.entities['8'].roles)
    for role in roles:
      if role is None:
        context.entities['8'].roles.remove(role)
