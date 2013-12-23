class ActionPermission(Permission):
  
  
  def __init__(self, kind, action, executable=None, condition=None):
    
    self.kind = kind
    self.action = action
    self.executable = executable
    self.condition = condition
    
  def run(self, role, context):
    
    if (self.kind == context.entity.get_rule_kind()) and (self.action in context.entity._rule_actions) and (eval(self.condition)) and (self.executable != None):
      context.entity._rule_action_permissions[self.action]['executable'].append(self.executable)