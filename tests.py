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