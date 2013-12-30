# -*- coding: utf-8 -*-
'''
Created on Dec 30, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
class Foobar():
  _properties = None
  
  def change(self, what):
      self._properties = what
      
      


a = Foobar()
a.change({'a' : 1})
b = Foobar()
b.change({'b' : 2})

d = {'1' : a, '2' : b}

for k,v in d.items():
    print v._properties
    v._properties['changed'] = 1
    
print a._properties, b._properties