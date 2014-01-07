# -*- coding: utf-8 -*-
'''
Created on Jan 7, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
"""
safe_eval module - methods intended to provide more restricted alternatives to
                   evaluate simple and/or untrusted code.
"""

# Module partially ripped from/inspired by several different sources:
#  - http://code.activestate.com/recipes/286134/
#  - safe_eval in lp:~xrg/openobject-server/optimize-5.0
#  - safe_eval in tryton http://hg.tryton.org/hgwebdir.cgi/trytond/rev/bbb5f73319ad
#  - python 2.6's ast.literal_eval

from opcode import HAVE_ARGUMENT, opmap, opname
from types import CodeType
import logging

__all__ = ['test_expr', 'run_literal', 'run', 'run_const' ]

# The time module is usually already provided in the safe_eval environment
# but some code, e.g. datetime.datetime.now() (Windows/Python 2.5.2, bug
# lp:703841), does import time.
_ALLOWED_MODULES = ['_strptime', 'time']

_CONST_OPCODES = set(opmap[x] for x in [
    'POP_TOP', 'ROT_TWO', 'ROT_THREE', 'ROT_FOUR', 'DUP_TOP','POP_BLOCK','SETUP_LOOP',
    'BUILD_LIST', 'BUILD_MAP', 'BUILD_TUPLE',
    'LOAD_CONST', 'RETURN_VALUE', 'STORE_SUBSCR'] if x in opmap)

_EXPR_OPCODES = _CONST_OPCODES.union(set(opmap[x] for x in [
    'UNARY_POSITIVE', 'UNARY_NEGATIVE', 'UNARY_NOT',
    'UNARY_INVERT', 'BINARY_POWER', 'BINARY_MULTIPLY',
    'BINARY_DIVIDE', 'BINARY_FLOOR_DIVIDE', 'BINARY_TRUE_DIVIDE',
    'BINARY_MODULO', 'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_SUBSCR',
    'BINARY_LSHIFT', 'BINARY_RSHIFT', 'BINARY_AND', 'BINARY_XOR',
    'BINARY_OR'] if x in opmap))

_SAFE_OPCODES = _EXPR_OPCODES.union(set(opmap[x] for x in [
    'STORE_MAP', 'LOAD_NAME', 'CALL_FUNCTION', 'COMPARE_OP', 'LOAD_ATTR',
    'STORE_NAME', 'GET_ITER', 'FOR_ITER', 'LIST_APPEND', 'DELETE_NAME',
    'JUMP_FORWARD', 'JUMP_IF_TRUE', 'JUMP_IF_FALSE', 'JUMP_ABSOLUTE',
    'MAKE_FUNCTION', 'SLICE+0', 'SLICE+1', 'SLICE+2', 'SLICE+3',
    # New in Python 2.7 - http://bugs.python.org/issue4715 :
    'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP', 'POP_JUMP_IF_FALSE',
    'POP_JUMP_IF_TRUE'
    ] if x in opmap))

_logger = logging.getLogger('safe_eval')

def _get_opcodes(codeobj):
    """_get_opcodes(codeobj) -> [opcodes]

    Extract the actual opcodes as a list from a code object

    >>> c = compile("[1 + 2, (1,2)]", "", "eval")
    >>> _get_opcodes(c)
    [100, 100, 23, 100, 100, 102, 103, 83]
    """
    i = 0
    opcodes = []
    byte_codes = codeobj.co_code
    while i < len(byte_codes):
        code = ord(byte_codes[i])
        opcodes.append(code)
        if code >= HAVE_ARGUMENT:
            i += 3
        else:
            i += 1
    return opcodes

def test_expr(expr, allowed_codes, mode="eval"):
    """test_expr(expression, allowed_codes[, mode]) -> code_object

    Test that the expression contains only the allowed opcodes.
    If the expression is valid and contains only allowed codes,
    return the compiled code object.
    Otherwise raise a ValueError, a Syntax Error or TypeError accordingly.
    """
    try:
        if mode == 'eval':
            # eval() does not like leading/trailing whitespace
            expr = expr.strip()
        code_obj = compile(expr, "", mode)
    except (SyntaxError, TypeError):
        _logger.debug('Invalid eval expression', exc_info=True)
        raise
    except Exception:
        _logger.debug('Disallowed or invalid eval expression', exc_info=True)
        raise ValueError("%s is not a valid expression" % expr)
    for code in _get_opcodes(code_obj):
        if code not in allowed_codes:
            raise ValueError("opcode %s not allowed (%r)" % (opname[code], expr))
    return code_obj


def run_const(expr):
    """run_const(expression) -> value

    Safe Python constant evaluation

    Evaluates a string that contains an expression describing
    a Python constant. Strings that are not valid Python expressions
    or that contain other code besides the constant raise ValueError.

    >>> run_const("10")
    10
    >>> run_const("[1,2, (3,4), {'foo':'bar'}]")
    [1, 2, (3, 4), {'foo': 'bar'}]
    >>> const_eval("1+2")
    Traceback (most recent call last):
    ...
    ValueError: opcode BINARY_ADD not allowed
    """
    c = test_expr(expr, _CONST_OPCODES)
    return eval(c)

def expr_eval(expr):
    """expr_eval(expression) -> value

    Restricted Python expression evaluation

    Evaluates a string that contains an expression that only
    uses Python constants. This can be used to e.g. evaluate
    a numerical expression from an untrusted source.

    >>> expr_eval("1+2")
    3
    >>> expr_eval("[1,2]*2")
    [1, 2, 1, 2]
    >>> expr_eval("__import__('sys').modules")
    Traceback (most recent call last):
    ...
    ValueError: opcode LOAD_NAME not allowed
    """
    c = test_expr(expr, _EXPR_OPCODES)
    return eval(c)


# Port of Python 2.6's ast.literal_eval for use under Python 2.5
SAFE_CONSTANTS = {'None': None, 'True': True, 'False': False}

try:
    # first, try importing directly
    from ast import literal_eval
except ImportError:
    import _ast as ast

    def _convert(node):
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Tuple):
            return tuple(map(_convert, node.elts))
        elif isinstance(node, ast.List):
            return list(map(_convert, node.elts))
        elif isinstance(node, ast.Dict):
            return dict((_convert(k), _convert(v)) for k, v
                        in zip(node.keys, node.values))
        elif isinstance(node, ast.Name):
            if node.id in SAFE_CONSTANTS:
                return SAFE_CONSTANTS[node.id]
        raise ValueError('malformed or disallowed expression')

    def parse(expr, filename='<unknown>', mode='eval'):
        """parse(source[, filename], mode]] -> code object
        Parse an expression into an AST node.
        Equivalent to compile(expr, filename, mode, PyCF_ONLY_AST).
        """
        return compile(expr, filename, mode, ast.PyCF_ONLY_AST)

    def run_literal(node_or_string):
        """literal_eval(expression) -> value
        Safely evaluate an expression node or a string containing a Python
        expression.  The string or node provided may only consist of the
        following Python literal structures: strings, numbers, tuples,
        lists, dicts, booleans, and None.

        >>> run_literal('[1,True,"spam"]')
        [1, True, 'spam']

        >>> run_literal('1+3')
        Traceback (most recent call last):
        ...
        ValueError: malformed or disallowed expression
        """
        if isinstance(node_or_string, basestring):
            node_or_string = parse(node_or_string)
        if isinstance(node_or_string, ast.Expression):
            node_or_string = node_or_string.body
        node_or_string = apply_filters(node_or_string)
        return _convert(node_or_string)

def _import(name, globals={}, locals={}, fromlist=[], level=-1):
    if name in _ALLOWED_MODULES:
        return __import__(name, globals, locals, level)
    raise ImportError(name)

def run(expr, globals_dict=None, locals_dict=None, mode="eval", nocopy=False):
    """run(expression[, globals[, locals[, mode[, nocopy]]]]) -> result

    System-restricted Python expression evaluation

    Evaluates a string that contains an expression that mostly
    uses Python constants, arithmetic expressions and the
    objects directly provided in context.

    This can be used to e.g. evaluate
    an OpenERP domain expression from an untrusted source.

    Throws TypeError, SyntaxError or ValueError (not allowed) accordingly.

    >>> run("__import__('sys').modules")
    Traceback (most recent call last):
    ...
    ValueError: opcode LOAD_NAME not allowed

    """
    if isinstance(expr, CodeType):
        raise ValueError("safe_eval does not allow direct evaluation of code objects.")
      
    expr = apply_filters(expr)

    if '__subclasses__' in expr:
       raise ValueError('expression not allowed (__subclasses__)')

    if globals_dict is None:
        globals_dict = {}

    # prevent altering the globals/locals from within the sandbox
    # by taking a copy.
    if not nocopy:
        # isinstance() does not work below, we want *exactly* the dict class
        if (globals_dict is not None and type(globals_dict) is not dict) \
            or (locals_dict is not None and type(locals_dict) is not dict):
            logging.getLogger('safe_eval').warning('Looks like you are trying to pass a dynamic environment,"\
                              "you should probably pass nocopy=True to safe_eval()')

        globals_dict = dict(globals_dict)
        if locals_dict is not None:
            locals_dict = dict(locals_dict)

    globals_dict.update(
            __builtins__ = {
                '__import__': _import,
                'True': True,
                'False': False,
                'None': None,
                'str': str,
                'globals': locals,
                'locals': locals,
                'bool': bool,
                'dict': dict,
                'list': list,
                'tuple': tuple,
                'map': map,
                'abs': abs,
                'reduce': reduce,
                'filter': filter,
                'round': round,
                'len': len,
                'set' : set
            }
    )
    return eval(test_expr(expr,_SAFE_OPCODES, mode=mode), globals_dict, locals_dict)
      
# implementation of filters

__SYSTEM_FILTERS = []

def apply_filters(expr):
    filters = get_filters()
    
    for _filter in filters:
       expr = _filter(expr)
       
    return expr

def get_filters():
    global __SYSTEM_FILTERS
    
    return __SYSTEM_FILTERS
  
def register_filters(*args):
    global __SYSTEM_FILTERS
    
    __SYSTEM_FILTERS.extend(*args)