# -*- coding: utf-8 -*-
'''
Created on Sep 5, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

import json
import time
import os
import itertools
 
from app import ndb, memcache
from app.pyson import Eval
from app.core import logger
from app.request import Segments, Angular
from app.kernel.models import (User, UserIdentity, Workflow)


class TestRoot(ndb.BaseModel):
      _KIND = 'TestRoot'
      name = ndb.StringProperty()
 
class TestChild(ndb.BaseModel):
      _KIND = 'TestChild'
      childname = ndb.StringProperty()

class SecondTestRoot(ndb.BaseModel):
       _KIND = 'SecondTestRoot'
       name = ndb.StringProperty(indexed=True)
      
class Test(ndb.BaseModel, Workflow):
    
       _KIND = 'Test'
       
       OBJECT_STATES = {
          'active' : (1, ),
          'not_active' : (2, )              
       }
       
       name = ndb.SuperStringProperty(indexed=True, writable=Eval('state') == 'active')
       state = ndb.SuperStateProperty(default=1)
       
       date = ndb.DateTimeProperty(auto_now_add=True, indexed=True)
       numbers = ndb.DecimalProperty()
      
class TestExpandoIndex(ndb.BaseExpando):
    
      _KIND = 'TestExpandoIndex'
      
      name = ndb.StringProperty()
      
      _default_indexed = False
      
      _VIRUTAL_FIELDS = {
         'west' : ndb.StringProperty(indexed=True)
      }
      
      
class TestCountry(ndb.BaseModel):
      _KIND = 'TestCountry'
      name = ndb.StringProperty()
      
      
class Environ(ndb.BaseModel):
      _KIND = 'Environ'
      name = ndb.StringProperty()
      
class TestNamespace(ndb.BaseModel):
      _KIND = 'TestNamespace'
      name = ndb.StringProperty()
      
class TestRole(ndb.Model):
      name = ndb.StringProperty()
      
class TestRoleUser(ndb.Model):
      name = ndb.StringProperty()
       
class TestSequencer(ndb.Model):
      sequence = ndb.IntegerProperty()
      
class TestStore(ndb.Model):
      name = ndb.StringProperty()
      
class TestObjectLog(ndb.Model):
      name = ndb.StringProperty()
      
class TestUser(ndb.Model):
      name = ndb.StringProperty()
      
class TestOrder(ndb.Model):
      name = ndb.StringProperty()
 
import decimal
        
class Tests(Segments):
    
    
     def segment_test_loops2(self):
        variants = [
            {'name': 'Color', 'count': 3, 'options': ['Red', 'Green', 'Blue'], 'position': 0, 'increment': False, 'reset': False},
            {'name': 'Size', 'count': 3, 'options': ['Small', 'Medium', 'Large'], 'position': 0, 'increment': False, 'reset': False},
            {'name': 'Size2', 'count': 3, 'options': ['XS', 'XL', 'XXL'], 'position': 0, 'increment': False, 'reset': False},
            # {'name': 'Size2', 'count': 3, 'options': ['XS', 'XL', 'XXL'], 'position': 0, 'increment': False, 'reset': False},

            {'name': 'Fabric', 'count': 2, 'options': ['Silk', 'Cotton'], 'position': 0, 'increment': False, 'reset': False},
        ]
        
        variant_signatures = []
        stay = True
        while stay:
            iterator = 0
            for item in variants:
                if (item['increment']):
                    variants[iterator]['position'] += 1
                    variants[iterator]['increment'] = False
                if (item['reset']):
                    variants[iterator]['position'] = 0
                    variants[iterator]['reset'] = False
                iterator += 1
            dic = {}
            iterator = 0
            for item in variants:
                dic[item['name']] = item['options'][item['position']]
                if (iterator == 0):
                    if (item['count'] == item['position'] + 1):
                        variants[iterator]['reset'] = True
                        variants[iterator + 1]['increment'] = True
                    else:
                        variants[iterator]['increment'] = True
                elif not (len(variants) == iterator + 1):
                    if (item['count'] == item['position'] + 1):
                        if (variants[iterator - 1]['reset']):
                            variants[iterator]['reset'] = True
                            variants[iterator + 1]['increment'] = True
                elif (len(variants) == iterator + 1):
                    if (item['count'] == item['position'] + 1):
                        if (variants[iterator - 1]['reset']):
                            variant_signatures.append(dic)
                            stay = False
                            break
                iterator += 1
            variant_signatures.append(dic)
            
        for i in variant_signatures:
            self.response.write('<br />')
            self.response.write(i)
        self.response.write(len(variant_signatures))
    
     def segment_test_loops(self):
         
         self.response.headers['Content-Type'] = 'text/plain;charset=utf8'
         
         product_template_variants = {
            1: {'name': 'Color', 'options': ['Red', 'Green', 'Blue']},
            2: {'name': 'Size', 'options': ['Small', 'Medium', 'Large']},
            2: {'name': 'Size2', 'options': ['Wood', 'Steel', 'Gas']},
            3: {'name': 'Fabric', 'options': ['Silk', 'Cotton']},
         }
         variant_signature = {
            1: {'Color': 'Red', 'Size': 'Small', 'Fabric': 'Silk'},
            2: {'Color': 'Red', 'Size': 'Small', 'Fabric': 'Cotton'},
            3: {'Color': 'Red', 'Size': 'Medium', 'Fabric': 'Silk'},
            4: {'Color': 'Red', 'Size': 'Medium', 'Fabric': 'Cotton'},
            5: {'Color': 'Red', 'Size': 'Large', 'Fabric': 'Silk'},
            6: {'Color': 'Red', 'Size': 'Large', 'Fabric': 'Cotton'},
            7: {'Color': 'Green', 'Size': 'Small', 'Fabric': 'Silk'},
            8: {'Color': 'Green', 'Size': 'Small', 'Fabric': 'Cotton'},
            9: {'Color': 'Green', 'Size': 'Medium', 'Fabric': 'Silk'},
            10: {'Color': 'Green', 'Size': 'Medium', 'Fabric': 'Cotton'},
            11: {'Color': 'Green', 'Size': 'Large', 'Fabric': 'Silk'},
            12: {'Color': 'Green', 'Size': 'Large', 'Fabric': 'Cotton'},
            13: {'Color': 'Blue', 'Size': 'Small', 'Fabric': 'Silk'},
            14: {'Color': 'Blue', 'Size': 'Small', 'Fabric': 'Cotton'},
            15: {'Color': 'Blue', 'Size': 'Medium', 'Fabric': 'Silk'},
            16: {'Color': 'Blue', 'Size': 'Medium', 'Fabric': 'Cotton'},
            17: {'Color': 'Blue', 'Size': 'Large', 'Fabric': 'Silk'},
            18: {'Color': 'Blue', 'Size': 'Large', 'Fabric': 'Cotton'},
        }
         
         variant_signatures = {
            1: {'Color': 'Red', 'Size': 'Small', 'Fabric': 'Silk'},
            2: {'Color': 'Green', 'Size': 'Small', 'Fabric': 'Silk'},
            3: {'Color': 'Blue', 'Size': 'Small', 'Fabric': 'Silk'},
            4: {'Color': 'Red', 'Size': 'Medium', 'Fabric': 'Silk'},
            5: {'Color': 'Green', 'Size': 'Medium', 'Fabric': 'Silk'},
            6: {'Color': 'Blue', 'Size': 'Medium', 'Fabric': 'Silk'},
            7: {'Color': 'Red', 'Size': 'Large', 'Fabric': 'Silk'},
            8: {'Color': 'Green', 'Size': 'Large', 'Fabric': 'Silk'},
            9: {'Color': 'Blue', 'Size': 'Large', 'Fabric': 'Silk'},
            10: {'Color': 'Red', 'Size': 'Small', 'Fabric': 'Cotton'},
            11: {'Color': 'Green', 'Size': 'Small', 'Fabric': 'Cotton'},
            12: {'Color': 'Blue', 'Size': 'Small', 'Fabric': 'Cotton'},
            13: {'Color': 'Red', 'Size': 'Medium', 'Fabric': 'Cotton'},
            14: {'Color': 'Green', 'Size': 'Medium', 'Fabric': 'Cotton'},
            15: {'Color': 'Blue', 'Size': 'Medium', 'Fabric': 'Cotton'},
            16: {'Color': 'Red', 'Size': 'Large', 'Fabric': 'Cotton'},
            17: {'Color': 'Green', 'Size': 'Large', 'Fabric': 'Cotton'},
            18: {'Color': 'Blue', 'Size': 'Large', 'Fabric': 'Cotton'},
         }
         
  
         flist = [{'name': 'Color', 'options': ['Red', 'Green', 'Blue'], 'count' : 3},
              {'name': 'Size', 'options': ['Small', 'Medium', 'Large'], 'count' : 3}, 
               {'name': 'Size Other', 'options': ['XS', 'XL', 'XXL'], 'count' : 3}, 
               
              {'name': 'Fabric', 'options': ['Silk', 'Cotton'], 'count' : 2}
         ]
         
         self.response.write("Compile for \n")
         self.response.write(flist)
         self.response.write("\n")
          
         keys = []
         
         max_iteration = 1000
         
         from itertools import product
         option1 = ['Red', 'Green', 'Blue']
         option2 = ['Small', 'Medium', 'Large']
         option3 = ['Silk', 'Cotton']
     
         it = 1
         for tup in product(option1, option2, option3):
                 ttem = "-".join(tup)
                 print it, ttem
                 it += 1
 
       
         self.response.write("\n")        
         self.response.write(keys)
         self.response.write("\n")
         self.response.write(len(keys))
   
   
    
     def segment_test_get_hook(self):
         k = self.request.get('k')
         soul = ndb.Key(urlsafe=k).get_async().get_result()
         
         if self.request.get('put'):
             soul.state = 2
             soul.name = 'sdsddssdgegeg'
             soul.put()
             self.response.write(soul._original_values)
    
         self.response.write(soul)
  
     def segment_test_namespace_otherwise(self):
         namespace = 'foo'
         if self.request.get('make'):
            pass
            
    
     def segment_test_namespace_parent(self):
         namespace = 'foo'
         
         if self.request.get('f'):
             @ndb.transactional(xg=True)
             def trans():
                 store = TestStore(name='Store 1', namespace=namespace)
                 
                 store.put()
                 
                 obj = TestObjectLog(parent=store.key, name='Log 1')
                 
                 obj.put()
                 
                 self.response.write(obj.key.urlsafe())
                  
             trans()
             
         else:
             self.response.write(ndb.Key(urlsafe=self.request.get('k')).get())
          
     def segment_test_sequencer(self):
         if self.request.get('put'):
            for i in range(1, 5):
                t = TestSequencer(sequence=i, namespace='foo')
                t.put()
         
         self.response.write(TestSequencer.query(namespace='foo').order(TestSequencer.sequence).fetch())
         self.response.write(TestSequencer.query(namespace='foo').order(-TestSequencer.sequence).fetch())
    
     def segment_ndb_key_test(self):
         if self.request.get('put'):
            t = TestRole(name='Role name')
            t.put()
            
            u = TestRoleUser(id=str(t.key.id()), name='TestRoleUser', parent=t.key)
            u.put()
            
            self.response.write(str(t.key.id()))
         else:   
            self.response.write(TestRoleUser.get_by_id(self.request.get('id')))
    
     def segment_namespace_test(self):
         if self.request.get('k'):
            namespace = ndb.Key(urlsafe=self.request.get('k')).get()
         else:
            namespace = Environ(name='Environ #1')
            namespace.put()
        
         namespace = namespace.key.urlsafe()
         
         app = []   
         if self.request.get('put'):
           for i in range(1,2):
               t = TestNamespace(name='Namespace entity #%s' % i, namespace=namespace)
               t.put()
               app.append(t)
         else:
             for i in TestNamespace.query(namespace=namespace):
                 app.append(i)
         
         self.response.write(namespace)
         self.response.write('<br />')      
         self.response.write(app)
            
            
    
     def segment_angular_query(self):
         self.send_json([{'id' : 1, 'name' : 'Name 1'}, {'id' : 2, 'name' : 'Name 2'}])
    
     def segment_angular_index(self):
         self.render('angular/index.html')
    
     def segment_test_find_query(self):
         
         if self.request.get('put'):
            fx = os.path.join(os.path.abspath('.'), 'countries.json')
            logger(fx)
            
            f = open(fx)
            js = f.read()
            
            js = json.loads(js)
            for j in js:
                TestCountry(name=j['short_name']).put()
         
         q = self.request.get('q')
       
         letters = list('abcdefghijklmnopqrstuvwxyz')
         
         logger(letters)
         
         b = letters[letters.index(q[-1].lower()) + 1]
         
         q2 = list(q)
         del q2[-1]
         
         if q[-1].isupper():
            b = b.upper()
          
         q2.append(b)
         
         b = u"".join(q2)
          
         self.response.write('<p>Query: TestCountry.query(TestCountry.name >= %s, TestCountry.name < %s).order(TestCountry.name).fetch()</p>' % (q, b))
         
         res = TestCountry.query(TestCountry.name >= q, TestCountry.name < b).order(TestCountry.name).fetch()
         
         for pr in res:
             self.response.write('<br /> %s' % pr.name)
    
     def segment_test_index(self):
         
         if self.request.get('put'):
             a = TestExpandoIndex(name='foo2', west='east2')
             a.put()
         else:
             a = ndb.Key(urlsafe='agpkZXZ-YnViZWZkch0LEhBUZXN0RXhwYW5kb0luZGV4GICAgICAyPMKDA').get()
             del a.west
             a.put()
    
     def segment_test_ancestor_queries(self):
         """
         Test.query(ancestor='value).order(Test.date)
         Test.query(ancestor='value).order(-Test.date)
         Test.query(Test.name == 'value', ancestor='value')
         Test.query(Test.name == 'value', ancestor='value).order(Test.name)
         Test.query(Test.name == 'value', ancestor='value).order(-Test.name)
         Test.query(Test.name == 'value', ancestor='value).order(Test.date)
         Test.query(Test.name == 'value', ancestor='value).order(-Test.date)
         """
         
         k2e = SecondTestRoot.get_by_id('foo')
         if k2e:
            ke = k2e.key
         
         q = self.request.get('q')
         if not q:
            q = -1
         else:
            q = int(q)
            
         command = self.request.get('command')
         if command == 'make':
            f = SecondTestRoot(id='foo', name='bar') 
            f.put()
            
            ke = f.key
            
            for i in range(0, 10):
                k = Test(name='record', parent=f.key)
                k.put()
            return
            
         self.response.headers['Content-Type'] = 'text/plain;charset=utf8'
         
         if q == 1:
             self.response.write("\n Test.query(ancestor='value).order(Test.name) GOT: \n")
             self.response.write(Test.query(ancestor=ke).order(Test.name).fetch())
             self.response.write("\n \n")
         
         if q == 2:
             self.response.write("\n Test.query(ancestor='value).order(-Test.name) GOT: \n")
             self.response.write(Test.query(ancestor=ke).order(-Test.name).fetch())
             self.response.write("\n \n")
         
         if q == 3:
             self.response.write("\n Test.query(ancestor='value).order(Test.date) GOT: \n")
             self.response.write(Test.query(ancestor=ke).order(Test.date).fetch())
             self.response.write("\n \n")
         
         if q == 4:
             self.response.write("\n Test.query(ancestor='value).order(-Test.date) GOT: \n")
             self.response.write(Test.query(ancestor=ke).order(-Test.date).fetch())
             self.response.write("\n \n")
         
         if q == 5:
             self.response.write("\n Test.query(Test.name == 'value', ancestor='value') GOT: \n")
             self.response.write(Test.query(Test.name == 'record', ancestor=ke).fetch())
             self.response.write("\n \n")
         
         if q == 6:
             self.response.write("\n Test.query(Test.name == 'value', ancestor='value).order(Test.name) GOT: \n")
             self.response.write(Test.query(Test.name == 'record', ancestor=ke).order(Test.name).fetch())
             self.response.write("\n \n")
         
         if q == 7:
             self.response.write("\n Test.query(Test.name == 'value', ancestor='value).order(-Test.name) GOT: \n")
             self.response.write(Test.query(Test.name == 'record', ancestor=ke).order(-Test.name).fetch())
             self.response.write("\n \n")
         
         if q == 8:
             self.response.write("\n Test.query(Test.name == 'value', ancestor='value).order(Test.date) GOT: \n")
             self.response.write(Test.query(Test.name == 'record', ancestor=ke).order(Test.date).fetch())
             self.response.write("\n \n")
         
         if q == 9:
             self.response.write("\n Test.query(Test.name == 'value', ancestor='value).order(-Test.date) GOT: \n")
             self.response.write(Test.query(Test.name == 'record', ancestor=ke).order(-Test.date).fetch())
             self.response.write("\n \n")
             
         if q == 10:
            # Test.query().order(Test.name)
             self.response.write("\n Test.query().order(Test.name) GOT: \n")
             self.response.write(Test.query().order(Test.name).fetch())
             self.response.write("\n \n")
         
         
    
     def segment_test_queries(self):
          
         data = self.request.get_all('d')
         self.data = data
         
         self.response.headers['Content-Type'] = 'text/plain;charset=utf8'
         
         command = self.request.get('command')
         no_put = self.request.get('no_put')
         update = self.request.get('update')
         no_update = self.request.get('no_update')
         
         l1 = TestRoot.query().fetch(keys_only=True)
         
         if l1 and (not no_put and not update):
            ndb.delete_multi(l1)
            memcache.delete('update_factory')
         
         l2 = TestChild.query().fetch(keys_only=True)
         
         if l2 and (not no_put and not update):
            ndb.delete_multi(l2)
            
         update_factory = memcache.get('update_factory')
         
         if not update:
            update_factory = {
               'test1' : [],
               'test2' : [],
               'test3' : [],
               'test4' : [],
            }
            
         if update:
            if not update_factory:
               raise Exception('Run the creation first, memcache is empty')
            else:
               logger(update_factory)
           
         if command == 'test1':
             @ndb.transactional(xg=True)
             def test1():
                 if update:
                    self.data = []
                    for k in update_factory['test1']:
                        ke = ndb.Key(urlsafe=k).get()
                        kx = u'%s updated' % ke.name
                         
                        if not no_update:
                           ke.name = kx 
                           ke.put()
                        else:
                           kx = ke.name
                           
                        self.data.append(kx)  
                 else:
                     logger(self.data)
                     if not no_put:
                         for d in self.data:
                             a = TestRoot(name=d)
                             a.put()
                             update_factory['test1'].append(a.key.urlsafe())
                
                 for d in self.data:
                    self.response.write("Querying for %s inside transaction function, got: \n" % d)
                    self.response.write(TestRoot.query(TestRoot.name==d).order(TestRoot.name).fetch())
                 self.response.write("\n \n")  
                
             test1()
         
         if command == 'test2':
             runs = []
             for d in data:
                 if no_update:
                    d = '%s updated' % d
                 runs.append(TestRoot.query(TestRoot.name==d).order(TestRoot.name).get())     
             @ndb.transactional(xg=True)
             def test2():
                 if update:
                    """ 
                    self.data = []
                    for k in update_factory['test2']:
                        ke = ndb.Key(urlsafe=k).get()
                        kx = u'%s updated' % ke.name
                    """
                    self.data = []
                    for ke in runs:
                        if not ke:
                           continue 
                        kx = u'%s updated' % ke.name
                        if not no_update:
                           ke.name = kx 
                           ke.put()
                        else:
                           kx = ke.name
                           
                        self.data.append(kx)
                 else:
                     if not no_put:
                         for d in self.data:
                             a = TestRoot(name=d)
                             a.put()
                             update_factory['test2'].append(a.key.urlsafe())
             
             test2()   
              
             for d in self.data:
                 self.response.write("\n\n Querying for %s outside (TestRoot.query(TestRoot.name==d).order(TestRoot.name).fetch()) transaction function, got: \n" % d)
                 
                # time.sleep(0.2)
                 
                 for f in TestRoot.query(TestRoot.name==d).order(TestRoot.name).fetch():
                     self.response.write("\t %s \n" % f)
                     
                 self.response.write("\n \n")
                 
         if command == 'test3':
             kg = ndb.Key(TestRoot, 'root_test3')
             @ndb.transactional(xg=True)
             def test3():
                 troot = TestRoot(id='root_test3', name='Root Entity for test3')
                 troot2 = kg.get()
                 if not troot2:
                    troot.put()
                 else:
                    troot = troot2 
                    
                 if update:
                    self.data = []
                    for k in update_factory['test3']:
                        ke = ndb.Key(urlsafe=k).get()
                        kx = u'%s updated' % ke.childname
                         
                        if not no_update:
                           ke.childname = kx 
                           ke.put()
                        else:
                           kx = ke.childname
                           
                        self.data.append(kx)  
                 else:                 
                     if not no_put:   
                         for d in self.data:
                             a = TestChild(childname=d, parent=troot.key)
                             a.put()
                             update_factory['test3'].append(a.key.urlsafe())
       
                 for d in self.data:
                     self.response.write("Querying (TestChild) for %s inside (TestChild.query(TestChild.childname==d, ancestor=%s).order(TestChild.childname).fetch()) transaction function, got: \n" % (d, str(kg)))
                     for f in TestChild.query(TestChild.childname==d, ancestor=kg).order(TestChild.childname).fetch():
                         self.response.write("\t" + str(f) + "\n")    
                     self.response.write("\n \n")
                     
             test3()   
 
         if command == 'test4':
             kg = ndb.Key(TestRoot, 'root_test4')
             @ndb.transactional(xg=True)
             def test4():
                 troot = TestRoot(id='root_test4', name='Root Entity for test4')
                 troot2 = kg.get()
                 if not troot2:
                    troot.put()
                 else:
                    troot = troot2 
                    
                 if update:
                    self.data = []
                    for k in update_factory['test4']:
                        ke = ndb.Key(urlsafe=k).get()
                        kx = u'%s updated' % ke.childname
                         
                        if not no_update:
                           ke.childname = kx 
                           ke.put()
                        else:
                           kx = ke.childname
                           
                        self.data.append(kx)    
                 else:                
                     if not no_put:   
                         for d in self.data:
                             a = TestChild(childname=d, parent=troot.key)
                             a.put()
                             update_factory['test4'].append(a.key.urlsafe())
             
             test4()   
             for d in self.data:
                 self.response.write("Querying (TestChild) for %s outside (TestChild.query(TestChild.childname==d, ancestor=%s).order(TestChild.childname).fetch()) transaction function, got: \n" % (d, str(kg)))
                 
                 for f in TestChild.query(TestChild.childname==d, ancestor=kg).order(TestChild.childname).fetch():
                     self.response.write("\t" + str(f) + "\n")    
                     
                 self.response.write("\n \n")
             
         if not no_put:
             memcache.set('update_factory', update_factory)
             
    
     def segment_testanc(self):
         k = ndb.Key(urlsafe='agpkZXZ-YnViZWZkchULEghUZXN0Um9vdBiAgICAgNC7Cgw')
         TestChild(parent=k, childname='aaa').put()
         b = TestChild.query(ancestor=k).order(-TestChild.childname).fetch()
 
         self.response.write(b)
    
     def segment_wipetests(self):
         keys = TestChild.query().fetch(keys_only=True)
         ndb.delete_multi(keys)
    
     def segment_test6(self):
         self.render('tests/ajax.html')
    
     def segment_test4(self):
  
         if self.request.get('put'):
            u = TestRoot(name='test', sequence=1)
            u.put()
            
            self.response.write(u)
            self.response.write('<br />Factory key: ' + u.key.urlsafe() + '<br /><br />')
            return
         else:
             pass
             
         
         self.ss = 0.0 
         
         @ndb.transactional
         def trans():
             u = ndb.Key(urlsafe=self.request.get('k')).get()
             error = False
             for i in range(0, int(self.request.get('iterations', 5))):
                 t = time.time()
                 b = TestChild(parent=u.key, childname='foobar')
                 #self.response.write('Writing this entity to %s' % u.key.urlsafe())
                 try:
                     b.put()
                     ssa = time.time() - t
                     self.ss += ssa
                 except Exception as e:
                     error = True
                     self.response.clear()
                     #self.handle_exception(e, True)
                     self.response.write('<span style="color:red;font-weight:bold;">%s</span><div>%s</div>' % (e, ''))
                     break
             
             if not error:
                self.response.clear() 
                self.response.write('<span style="color:green;font-weight:bold;">OK</span>') 
             #self.response.write('<br />Wrote it, got id() %s (%s s)<br />' % (b.key.id(), ssa))
         
         trans()
         """
         try:    
             for i in range(0, int(self.request.get('iterations', 5))):
                  trans()
             self.response.write('<span style="color:green;font-weight:bold;">OK</span>')    
         except Exception as e:
             self.response.clear()
             #self.handle_exception(e, True)
             self.response.write('<span style="color:red;font-weight:bold;">%s</span><div>%s</div>' % (e, ''))
         """
     
             
         #self.response.write('<br />Total time taken to complete %s' % self.ss)
    
     def segment_test(self):
         self.response.write(User.current())
    
     def segment_test5(self):
         if self.request.get('k'):
            u = ndb.Key(urlsafe=self.request.get('k')).get()
            u.identities.append(UserIdentity(identity='baaz', email='email2@gmail.com'))
         else:
             u = User(state=1, identities=[UserIdentity(identity='baaz', email='email@gmail.com')])
             u.put()
             
         self.response.write(u.identities)
         self.response.write(u.key.urlsafe())

class AngularTests(Angular):
      
      def get(self):
          time.sleep(5)
          self.data['foo'] = 1


class RunTests(Segments):
    
      def segment_test_pyson(self):
          from app.tests.runs.pyson import main
          main()