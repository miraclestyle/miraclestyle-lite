# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import unittest
import random

def yielder(a):
  yield a

def foo(aa):
   yield map(yielder, aa)

z = [1,2,3,4]    
t = foo(z)
print t
  
  
class Tests():

  def __nonzero__(self):
    print '__nonzero__'
    return False
  
  def __bool__(self):
    print '__bool__'
    return False
  
d = Tests()
'''

if d:
  print 'yes d'
  
if not d:
  print 'not d'
  
'''
  
class Ba():
  
  def __repr__(self):
    s = []
    for k,v in self.__dict__.items():
      s.append('%s=%s' % (k, v))
    s = ", ".join(s)
    return self.__class__.__name__ + '('+s+')'
  
class Image(Ba):
  
  def __init__(self, a):
    self._other = ['1_%s' % a, '2_%s' % a, '3_%s' % a]
    self._id = a
  
class Product(Ba):
  
  def __init__(self, b, c):
    self._images = [Image('%s_%s' % (b, c+1)),Image('%s_%s' % (b, c+2)),Image('%s_%s' % (b, c+3))]
    self._id = b
  
class Catalog(Ba):
  
  def __init__(self):
    self._products = [Product(10, 20), Product(50, 100)]
  
do_entity = Catalog()
  
target_field_paths = ['_products._images._other']
root_entity = do_entity
entities = []
if target_field_paths:
  for full_target in target_field_paths:
    targets = full_target.split('.')
    last_i = len(targets)-1
    def start(entity, target, last_i, i, targets, entities):
      if isinstance(entity, list):
        out = []
        for ent in entity:
          out.append(start(ent, target, last_i, i, targets, entities))
        return out
      else:
        entity = getattr(entity, target)
        if last_i == i:
          if isinstance(entity, list):
            entities.extend(entity)
          else:
            entities.append(entity)
        else:
          return entity
    for i,target in enumerate(targets):
      do_entity = start(do_entity, target, last_i, i, targets, entities)
 
  
print entities

exit()
'''
class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.seq = range(10)

    def test_shuffle(self):
        # make sure the shuffled sequence does not lose any elements
        random.shuffle(self.seq)
        self.seq.sort()
        self.assertEqual(self.seq, range(10))

        # should raise an exception for an immutable sequence
        self.assertRaises(TypeError, random.shuffle, (1,2,3))

    def test_choice(self):
        element = random.choice(self.seq)
        self.assertTrue(element in self.seq)

    def test_sample(self):
        with self.assertRaises(ValueError):
            random.sample(self.seq, 20)
        for element in random.sample(self.seq, 5):
            self.assertTrue(element in self.seq)
'''           
if __name__ == '__main__':
  unittest.main()