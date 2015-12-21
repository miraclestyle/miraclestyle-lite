import codecs
import os
import sys

root = os.path.dirname(os.path.abspath(__file__))

files = map(lambda x: os.path.join(root, x), ['backend/app.yaml', 'frontend/app.yaml', 'dispatch.yaml'])

state = ''
try:
    arg = sys.argv[1]
    if arg == 'testing':
        state = '-testing-site'
except IndexError as e:
    pass

for f in files:
    contents = codecs.open(f, 'r').read()
    lines = contents.splitlines()
    lines[0] = 'application: themiraclestyle%s' % state
    codecs.open(f, 'w').writelines(lines)