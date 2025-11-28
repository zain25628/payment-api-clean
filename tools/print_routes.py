import os
import sys

# ensure repo root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app

for r in app.routes:
    methods = getattr(r, 'methods', None)
    path = getattr(r, 'path', None) or repr(r)
    print(f"{path} {methods}")
