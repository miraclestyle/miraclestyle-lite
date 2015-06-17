z = lambda entity, **kwargs: entity['bar']


ent = {'bar': 1}

print z(ent, lool=1)