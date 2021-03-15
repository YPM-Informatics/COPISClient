import os, sys

path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'copis')
sys.path.insert(0, path)

exec(open(os.path.join(path, 'client.py')).read())
