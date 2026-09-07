import subprocess
import sys


def test_import_cadquery_does_not_load_solver_backends():
    """casadi and nlopt are only needed when constraints are solved. Loading both at
    import time crashes the interpreter at exit on Windows (#1911), so `import
    cadquery` must leave them unloaded. Checked in a fresh process so this test does
    not depend on what the rest of the suite imported first."""
    code = "import sys, cadquery; print('casadi' in sys.modules, 'nlopt' in sys.modules)"
    out = subprocess.check_output([sys.executable, "-c", code], text=True)
    assert out.split() == ["False", "False"]
