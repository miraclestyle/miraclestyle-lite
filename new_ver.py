class ActionPermission(Permission):
  
  
  def __init__(self, kind, action, executable=None, condition=None):
    
    self.kind = kind
    self.action = action
    self.executable = executable
    self.condition = condition
    
  def run(self, role, context):
    
    if (self.kind == context.entity.get_rule_kind()) and (self.action in context.entity._rule_actions) and (eval(self.condition)):
      if (role.overide):
        if (self.executable != None):
          context.entity._rule_action_permissions[self.action] = {'executable': self.executable}
      else:
        if (self.executable != None) and (context.entity._rule_action_permissions[self.action]['executable'] == None):
          context.entity._rule_action_permissions[self.action] = {'executable': self.executable}

class FieldPermission(Permission):
  
  
  def __init__(self, kind, field, writable=None, visible=None, required=None, condition=None):
    
    self.kind = kind
    self.field = field
    self.writable = writable
    self.visible = visible
    self.required = required
    self.condition = condition
    
  def run(self, context):
    
    if (self.kind == context.entity.get_rule_kind()) and (self.field in context.entity._rule_properties) and (eval(self.condition)):
      if (role.overide):
        if (self.writable != None):
          context.entity._rule_field_permissions[self.field] = {'writable': self.writable}
        if (self.visible != None):
          context.entity._rule_field_permissions[self.field] = {'visible': self.visible}
        if (self.required != None):
          context.entity._rule_field_permissions[self.field] = {'required': self.required}
      else:
        if (self.writable != None) and (context.entity._rule_field_permissions[self.field]['writable'] == None):
          context.entity._rule_field_permissions[self.field] = {'writable': self.writable}
        if (self.visible != None) and (context.entity._rule_field_permissions[self.field]['visible'] == None):
          context.entity._rule_field_permissions[self.field] = {'visible': self.visible}
        if (self.required != None) and (context.entity._rule_field_permissions[self.field]['required'] == None):
          context.entity._rule_field_permissions[self.field] = {'required': self.required}