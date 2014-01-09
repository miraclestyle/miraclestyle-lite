import dis
from decimal import Decimal

def memoize(maxsize):
    """
    Decorator to 'memoize' a function - caching its results with a
    near LRU implementation.

    The cache keeps a list of keys logicaly separated in 4 segment :

    segment 1 | ...        | segment4
    [k,k,k,k,k,k,k, .. ,k,k,k,k,k,k,k]

    For each segment there is a pointer that loops on it.  When a key
    is accessed from the cache it is promoted to the first segment (at
    the pointer place of segment one), the key under the pointer is
    moved to the next segment, the pointer is then incremented and so
    on. A key that is removed from the last segment is removed from
    the cache.

    :param: maxsize the size of the cache (must be greater than or
    equal to 4)
    """
    assert maxsize >= 4, "Memoize cannot work if maxsize is less than 4"

    def wrap(fct):
        cache = {}
        keys = [None for i in xrange(maxsize)]
        seg_size = maxsize // 4

        pointers = [i * seg_size for i in xrange(4)]
        max_pointers = [(i + 1) * seg_size for i in xrange(3)] + [maxsize]

        def wrapper(*args):
            key = repr(args)
            res = cache.get(key)
            if res:
                pos, res = res
                keys[pos] = None
            else:
                res = fct(*args)

            value = res
            for segment, pointer in enumerate(pointers):
                newkey = keys[pointer]
                keys[pointer] = key
                cache[key] = (pointer, value)

                pointers[segment] = pointer + 1
                if pointers[segment] == max_pointers[segment]:
                    pointers[segment] = segment * seg_size

                if newkey is None:
                    break
                segment, value = cache.pop(newkey)
                key = newkey

            return res

        wrapper.__doc__ = fct.__doc__
        wrapper.__name__ = fct.__name__

        return wrapper
    return wrap

_ALLOWED_CODES = set(dis.opmap[x] for x in [
        'POP_TOP', 'ROT_TWO', 'ROT_THREE', 'ROT_FOUR', 'DUP_TOP', 'BUILD_LIST',
        'BUILD_MAP', 'BUILD_TUPLE', 'LOAD_CONST', 'RETURN_VALUE',
        'STORE_SUBSCR', 'UNARY_POSITIVE', 'UNARY_NEGATIVE', 'UNARY_NOT',
        'UNARY_INVERT', 'BINARY_POWER', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
        'BINARY_FLOOR_DIVIDE', 'BINARY_TRUE_DIVIDE', 'BINARY_MODULO',
        'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_LSHIFT', 'BINARY_RSHIFT',
        'BINARY_AND', 'BINARY_XOR', 'BINARY_OR', 'STORE_MAP', 'LOAD_NAME',
        'CALL_FUNCTION', 'COMPARE_OP', 'LOAD_ATTR', 'STORE_NAME', 'GET_ITER',
        'FOR_ITER', 'LIST_APPEND', 'JUMP_ABSOLUTE', 'DELETE_NAME',
        'JUMP_IF_TRUE', 'JUMP_IF_FALSE', 'JUMP_IF_FALSE_OR_POP',
        'JUMP_IF_TRUE_OR_POP', 'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
        'BINARY_SUBSCR', 'JUMP_FORWARD',
        ] if x in dis.opmap)


@memoize(1000)
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