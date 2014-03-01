

class Entity():
   ".... nesto = ndb.StringProperty()"
    
   _actions = {}
    
   _additional_values = {}
   
   _properties = {}
   
   _virtual_properies = None
   
   def __init__(self, *args, **kwargs):
     
      self.add_field('_actions', self._actions)
      self.remove_field('_actions')
 
      
   def add_field(self, name, value):
       self._additional_values[name] = value
       
   def remove_field(self, name):
       pass
   
   def __todict__(self):
      dict = {}
      
      dict.update(self._additional_values)
      
      return dict
      
      
   def create(self):
      entity = {}
      entity.include_propery('primary_contact_email', '...whatever')
      
      
      {'key' : '..'}
      
      
entity = Entity()
entity.name = 1