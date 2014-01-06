"""
context.event.name
context.event.args
context.event.response

context.transaction.group
context.transaction.nodes
context.transaction.callbacks

context.log.nodes

context.rule.nodes


context.auth.user
context.authentication.user
context.event.response
"""

class Context:
  
  def __init__(self, **kwargs):
    
    self.event = None
    self.auth = None
    self.rule = None
    self.log = None
    self.transaction = None
      
    for k,v in kwargs.items():
      setattr(k, v)
      
class Action(ndb.BaseExpando):
  
  KIND_ID = 49
  
  # root (namespace Domain)
  # key.id() = code.code
  
  name = ndb.SuperStringProperty('1', required=True)
  code = ndb.SuperStringProperty('2', repeated=True)
  company = ndb.SuperKeyProperty('3', kind='app.domain.business.Company', required=True)
  sequence = ndb.SuperIntegerProperty('4', required=True)
  active = ndb.SuperBooleanProperty('5', default=True)
  subscriptions = ndb.SuperStringProperty('6', repeated=True) # verovatno ce ovo biti KeyProperty, repeated, i imace reference na akcije
  
  entry_fields = ndb.SuperPickleProperty('7', required=True, compressed=False)
  line_fields = ndb.SuperPickleProperty('8', required=True, compressed=False)
  plugin_categories = ndb.SuperStringProperty('9', repeated=True)
  
  
  def run(self, args):
    context = Context()
    context.event.name = self.key.urlsafe()
    for arg in self.args:
      context.event.args[arg] = args.get(arg)
      
      
    return transaction.Engine.run(context)
      
   
  
class Engine:
  
  def run(cls, action_key, args):
    
    action = get_system_action(action_key)
    if not action:
      action = Action.get_action(action_key)
    
    if action:
      context = action.run(args)
      
    if context:
      context.event.response
    
  
  
      
