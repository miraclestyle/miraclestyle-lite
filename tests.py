# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import inspect

class Foo(object):
     @classmethod
     def bar(cls):
         pass
     def baz(self):
         pass
       
print Foo.bar.__self__ is Foo
print Foo.baz.__self__ is None

print inspect.isclass(Foo)
print inspect.isclass(Foo())