class FieldPermission(Permission):
  
  
  def __init__(self, kind, field, writable=None, visible=None, required=None, condition=None):
    
    self.kind = kind
    self.field = field
    self.writable = writable
    self.visible = visible
    self.required = required
    self.condition = condition
    
  def run(self, context):
    
    if (self.kind == context.entity._get_kind()) and (self.field in context.entity._properties) and (eval(self.condition)):
      if (context.overide):
        if (self.writable != None):
          context.entity._field_permissions[self.field] = {'writable': self.writable}
        if (self.visible != None):
          context.entity._field_permissions[self.field] = {'visible': self.visible}
        if (self.required != None):
          context.entity._field_permissions[self.field] = {'required': self.required}
      else:
        if (context.entity._field_permissions[self.field]['writable'] == None) and (self.writable != None):
          context.entity._field_permissions[self.field] = {'writable': self.writable}
        if (context.entity._field_permissions[self.field]['visible'] == None) and (self.visible != None):
          context.entity._field_permissions[self.field] = {'visible': self.visible}
        if (context.entity._field_permissions[self.field]['required'] == None) and (self.required != None):
          context.entity._field_permissions[self.field] = {'required': self.required}