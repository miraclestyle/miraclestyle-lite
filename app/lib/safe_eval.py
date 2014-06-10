import dis
from decimal import Decimal
 
_ALLOWED_CODES = set(dis.opmap[x] for x in [
        'POP_TOP', 'ROT_TWO', 'ROT_THREE', 'ROT_FOUR', 'DUP_TOP', 'BUILD_LIST',
        'BUILD_MAP', 'BUILD_TUPLE', 'LOAD_CONST', 'RETURN_VALUE',
        'STORE_SUBSCR', 'UNARY_POSITIVE', 'UNARY_NEGATIVE', 'UNARY_NOT',
        'UNARY_INVERT', 'BINARY_POWER', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
        'BINARY_FLOOR_DIVIDE', 'BINARY_TRUE_DIVIDE', 'BINARY_MODULO',
        'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_LSHIFT', 'BINARY_RSHIFT',
        'BINARY_AND', 'BINARY_XOR', 'BINARY_OR', 'STORE_MAP', 'LOAD_NAME',
        'COMPARE_OP', 'LOAD_ATTR', 'STORE_NAME', 'GET_ITER',
        'FOR_ITER', 'LIST_APPEND', 'JUMP_ABSOLUTE', 'DELETE_NAME',
        'JUMP_IF_TRUE', 'JUMP_IF_FALSE', 'JUMP_IF_FALSE_OR_POP',
        'JUMP_IF_TRUE_OR_POP', 'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
        'BINARY_SUBSCR', 'JUMP_FORWARD',
        ] if x in dis.opmap)

# 'CALL_FUNCTION', removed

def _compile_source(source):
    comp = compile(source, '', 'eval')
    codes = []
    co_code = comp.co_code
    i = 0
    while i < len(co_code):
        code = ord(co_code[i])
        codes.append(code)
        if code >= dis.HAVE_ARGUMENT:
            i += 3
        else:
            i += 1
    for code in codes:
        if code not in _ALLOWED_CODES:
            raise ValueError('opcode %s not allowed' % dis.opname[code])
    return comp


def safe_eval(source, data=None):
    if '__subclasses__' in source:
        raise ValueError('__subclasses__ not allowed')

    comp = _compile_source(source)
    
    try:
      return eval(comp, {'__builtins__': {
          'True': True,
          'False': False,
          'str': str,
          'globals': locals,
          'locals': locals,
          'bool': bool,
          'dict': dict,
          'round': round,
          'Decimal' : Decimal,
          }}, data)
      
    except Exception as e:
        raise Exception('Failed to process code "%s" error: %s' % ((source, data), e))