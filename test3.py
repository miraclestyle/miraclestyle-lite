class Prop():
  
  def __set__(self, a, b=None):
     self.b = 1
  
  def __get__(self, a, b=None):
      print 'prop.__get__'
      
      return self.b
      
      
class Ah():
  
  pro = Prop()
  
  
  #def __getattr__(self, name):
     
  #   return super(Ah, self).__getattr__(name)
   
   
   
dd = Ah()

print getattr(dd, 'pro')