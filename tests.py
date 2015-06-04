import json

def override_dict(a, b):
    current_a = a
    current_b = b
    next_args = []
    while True:
        if current_b is None:
            try:
                current_a, current_b = next_args.pop()
                continue
            except IndexError as e:
                break
        for key in current_b:
            if key in current_a:
                if isinstance(current_a[key], dict) and isinstance(current_b[key], dict):
                    next_args.append((current_a[key], current_b[key]))
                elif current_a[key] == current_b[key]:
                    pass
                else:
                    # in this segment we encounter that a[key] is not equal to
                    # b[key] which we do not want, roll it back
                    current_a[key] = current_b[key]
            else:
                current_a[key] = current_b[key]
        current_b = None
        current_a = None
    return a

def merge_dicts(a, b):
    '''
     Merges dict b into a maintaining values of a intact.
      >>> stuff = {'1' : 'yes'}
      >>> stuff2 = {'1' : 'no', 'other' : 1}
      >>> merge_dicts(stuff, stuff2)
      >>> {'1': 'yes', 'other': 1}
    '''
    current_a = a
    current_b = b
    next_args = []
    while True:
        if current_b is None:
            try:
                current_a, current_b = next_args.pop()
                continue
            except IndexError as e:
                break
        for key in current_b:
            if key in current_a:
                if isinstance(current_a[key], dict) and isinstance(current_b[key], dict):
                    next_args.append((current_a[key], current_b[key]))
                elif current_a[key] == current_b[key]:
                    pass
                else:
                    # in this segment we encounter that a[key] is not equal to
                    # b[key] which we do not want
                    pass
            else:
                current_a[key] = current_b[key]
        current_b = None
        current_a = None
    return a

'''
stuff = {'1' : 'yes', '3': {'bar' : 1, 'far': {'zar': 1}}}
stuff2 = {'1' : 'no', '3': {'far': {'zar': 4}}, 'other' : 1}
print merge_dicts(stuff, stuff2)
print 'now override dict'

stuff = {'1' : 'yes', '3': {'bar' : 1, 'far': {'zar': 1}}}
stuff2 = {'1' : 'no', '3': {'far': {'zar': 4}}, 'other' : 1}
print override_dict(stuff, stuff2)
print 'ok', "\n" * 5
'''

def merge_dicts2(a, b):
    '''
     Merges dict b into a maintaining values of a intact.
      >>> stuff = {'1' : 'yes'}
      >>> stuff2 = {'1' : 'no', 'other' : 1}
      >>> merge_dicts(stuff, stuff2)
      >>> {'1': 'yes', 'other': 1}
    '''
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts2(a[key], b[key])
            elif a[key] == b[key]:
                pass
            else:
                # in this segment we encounter that a[key] is not equal to
                # b[key] which we do not want
                pass
        else:
            a[key] = b[key]
    return a


def override_dict2(a, b):
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                override_dict2(a[key], b[key])
            elif a[key] == b[key]:
                pass
            else:
                # in this segment we encounter that a[key] is not equal to
                # b[key] which we do not want, roll it back
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a



import time
import cStringIO
import cProfile
import pstats

def compute(start):
    return round((time.time() - start) * 1000, 3)

class Profile():

    def __init__(self):
        self.start = time.time()

    @property
    def miliseconds(self):
        return compute(self.start)


def profile(message=None):
    def decorator(fn):
        def inner(*args, **kwargs):
            start = time.time()
            result = fn(*args, **kwargs)
            initial_message = None
            if message is None:
                initial_message = '%s executed in %s'
            else:
                initial_message = message
            return result
        return inner
    return decorator


def make_dict(dic, s=1, e=100):
  hoard = []
  for x in xrange(s, e):
    h = {}
    dic[x] = h
    hoard.append(h)
  return hoard


def make_final_dict():
  dic = {}
  hoard = make_dict(dic)
  for h in hoard:
    ho = make_dict(h)
    for b in ho:
      make_dict(b)
  return dic

d1 = make_final_dict()
d2 = make_final_dict()

d3 = make_final_dict()
d4 = make_final_dict()



d = Profile()
override_dict2(d3, d4)
print 'override_dict2', d.miliseconds

d = Profile()
override_dict(d1, d2)
print 'override_dict', d.miliseconds


exit()

'''import functools
import sys
import types
def copy_func(f, name=None):
    return types.FunctionType(f.func_code, f.func_globals, name or f.func_name,
        f.func_defaults, f.func_closure)

sys.setrecursionlimit(1000)
def fb(i=0):
  if i == 2000:
    return i
  return fb2(i + 1)

def fb2(i=0):
  if i == 2000:
    return i
  return fb(i + 1)

print fb()
exit()'''

import ast
import os
import codecs

class FindRecursiveFunctions(ast.NodeVisitor):
    def __init__(self):
        self._current_func = None
        self.recursive_funcs = set()

    def generic_visit(self, node):
        if node.__class__ is ast.FunctionDef:
            self._current_func = node.name
        try:
            if node.__class__ is ast.Call and node.func.id == self._current_func:
                lineno = None
                if hasattr(node, 'lineno'):
                    lineno = node.lineno
                    # (self._current_func, lineno)
                self.recursive_funcs.add(self._current_func)
        except AttributeError as e:
            pass
        super(FindRecursiveFunctions, self).generic_visit(node)

files_with_recursion = {}
ignore = ['project-documentation.py', 'documentation/code/misc.py', 'temp.py', 'tests.py']
for dirname, dirnames, filenames in os.walk('.'):
    for f in filenames:
      if f.startswith('.') or not f.endswith('.py'):
        continue
      cont = False
      for ig in ignore:
        if f.endswith(ig):
            cont = True
            break
      if cont:
        continue
      abs_path = os.path.join(dirname, f)
      rf = codecs.open(abs_path, 'r', 'utf-8')
      code = rf.read()
      try:
          firstline = code.splitlines()[0]
          code = code[len(firstline):]
      except IndexError as e:
        pass
      print abs_path
      tree = ast.parse(code)
      finder = FindRecursiveFunctions()
      finder.visit(tree)
      if finder.recursive_funcs:
        files_with_recursion[abs_path] = finder.recursive_funcs

print 'Source code has:'
for f, items in files_with_recursion.iteritems():
    print 'File %s has %s recursive functions:' % (f, len(items))
    for item in items:
        print ' %s' % (item)