class Engine:
  
  @classmethod
  def final_check(cls, context):
    pass
  
  @classmethod
  def run(cls, context):
    
    calc = {}
    
    for role in roles:
      role.run(context)
    for action, properties in context.entity._rule_action_permissions.items():
      for proerpty, value in properties.items():
        if len(value):
          if (strict) and all(value):
            calc[action][proerpty] = [True]
          elif any(value):
            calc[action][proerpty] = [True]
          else:
            calc[action][proerpty] = [False]