# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import unittest
import random

# example of testcase

class Base1(object):
  
  def ove(self):
    print '1'
    super(Base1, self).ove()
  
  def foo(self):
    print 'bar'
    
    
class Base2(object):
  
  def bar(self):
    self.foo()
    
  def ove(self):
    print '2'
    
class Baz(Base1, Base2):
  
  def write(self):
    self.bar()
    self.ove()
    
ff = Baz()
ff.write()

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
            
if __name__ == '__main__':
  unittest.main()