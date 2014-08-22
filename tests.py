# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import unittest
import random
import math

def tests(a, b, z):
  return a, b, z

a = 1
b = 2  
print map(lambda x: tests(a, b, x), [1,2,3,4])

def chunks2(l, n):
    if n < 1:
        n = 1
    return [l[i:i + n] for i in range(0, len(l), n)]

def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

dd = [1]
print 'working with', dd        
print list(chunks(dd, 5))
print list(chunks2(dd, 5))

exit()

def prepare_multi_transactions(entities):
  per_entity_group = 5
  total = len(entities)
  loops = int(math.ceil(float(total) / float(per_entity_group)))
  total_offset = 0
  for i in xrange(0, loops):
    off = i*per_entity_group
    entities[i*per_entity_group:total_offset+per_entity_group]
    total_offset += per_entity_group
    
dd = range(1, 43)
print 'working with', dd
prepare_multi_transactions(dd)
    
exit()

class Base(object):
  
  @classmethod
  def out(cls):
    print cls
    
class Sub(Base):
  
  def out(self):
    super(Sub, self.__class__).out()

d = Sub()
d.out()

exit()

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
 

if d:
  print 'yes d'
  
if not d:
  print 'not d'
  
if d is d:
  print 'yes'
  
exit()
 
  
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