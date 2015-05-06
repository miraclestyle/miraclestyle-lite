def function(message=None):
    def decorator(fn):
        def inner(*args, **kwargs):
            result = fn(*args, **kwargs)
            result.append(message)
            return result
        return inner
    return decorator


@function(message='Yes')
def go(*args, **kwargs):
    return [args, kwargs]

print go(1,2,3,4,5, foo=1)
print go.__name__
nem = '%s what %s'
print nem