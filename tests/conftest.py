"""Lets the tests import the package (ereplan) and the experiment scripts (experiments/) from any directory."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (os.path.join(ROOT, "experiments"), ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)


# CostBench has no licence file, so its task routes are not distributed with this repository. Tests that need them
# are skipped until data/processed/costbench_routes.json is built with tools/costbench_routes.py.
COSTBENCH_ROUTES = os.path.join(ROOT, "data", "processed", "costbench_routes.json")
NEEDS_COSTBENCH = ("test_costbench_v5.py", "test_fr11_job_is_reproducible")


def pytest_collection_modifyitems(config, items):
    if os.path.exists(COSTBENCH_ROUTES):
        return
    import pytest
    skip = pytest.mark.skip(reason="needs data/processed/costbench_routes.json (build it with tools/costbench_routes.py)")
    for item in items:
        if any(k in item.nodeid for k in NEEDS_COSTBENCH):
            item.add_marker(skip)
