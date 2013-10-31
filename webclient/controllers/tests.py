# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular

from app import ndb

class TestRoot(ndb.Model):
      name = ndb.StringProperty()

class TestA(ndb.Model):
      name = ndb.StringProperty()
      
class TestB(ndb.Model):
      name = ndb.StringProperty()
 
class Tests(Angular):
    
      def respond(self):
          
          if self.request.get('del'):
             ndb.delete_multi(TestRoot.query().fetch(keys_only=True) + TestA.query().fetch(keys_only=True) + TestB.query().fetch(keys_only=True))
          
          if self.request.get('make'):
             puts = [] 
             parent = TestRoot(name='Root Thing', id='root_thing').put()
             for i in range(1, 50):
                 puts.append(TestA(parent=parent, id='testa_%s' % i, name='Test %s' % i))
                 
             lists = ndb.put_multi(puts)
             self.response.write('wrote %s' % lists)
             
          parent = ndb.Key(TestRoot, 'root_thing')
          
          if self.request.get('put'):
              @ndb.transactional(xg=True)
              def trans(indx):
                  puts = []
                  for i in range(1, 50):
                      puts.append(TestA(key=ndb.Key(TestA, 'testa_%s' % i, parent=parent), name='Testa %s' % i))
                      
                  lists = ndb.put_multi(puts)
                  puts = []
                  for l in lists:
                      for i in range(1, 2):
                          puts.append(TestB(parent=l, name='Child of TestB %s, #%s' % (l, i)))
                          
                  self.response.write('Wrote %s <br />' % ndb.put_multi(puts))
                  
              trans(1)
       
register(('/tests', Tests))