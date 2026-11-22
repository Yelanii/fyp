"""Lets the tests import the package (ereplan) and the experiment scripts (experiments/) from any directory."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (os.path.join(ROOT, "experiments"), ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)
