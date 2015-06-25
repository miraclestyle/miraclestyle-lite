class foo:

    def bar(zar, **kwargs):
        return zar

    def go(**kwargs):
        return kwargs

    _permissions = [
        go,
        bar
    ]

for perm in foo._permissions:
    print perm(bar=1, zar=2, far=3)