class Engine:
  
  @classmethod
  def final_check(cls, context):
    pass
  
  @classmethod
  def run(cls, context):
    
    # prvo se radi procesing local_role
    # pa se onda apply strict
    # i onda se procesira global_role
    # pase apply overide
    
    entity = context.entity
    if hasattr(entity, '_global_role') and isinstance(entity._global_role, Role):
       entity._global_role.run(context)
    
    cls.final_check(context) # ova funkcija proverava sva polja koja imaju vrednosti None i pretvara ih u False




class ActionPermission(Permission):
  
  
  def __init__(self, kind, action, executable=None, condition=None):
    
    self.kind = kind
    self.action = action
    self.executable = executable
    self.condition = condition
    
  def run(self, role, context):
    
    if (self.kind == context.entity.get_rule_kind()) and (self.action in context.entity._rule_actions) and (eval(self.condition)) and (self.executable != None):
      if (role.overide):
        if (self.executable != None):
          context.entity._rule_action_permissions[self.action]['executable'] = [self.executable]
      else:
        if (self.executable != None):
          context.entity._rule_action_permissions[self.action]['executable'].append(self.executable)