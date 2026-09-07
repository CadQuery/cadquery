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


def test_process_exits_cleanly_with_both_solver_backends_loaded():
    """casadi and nlopt are SWIG modules that share SWIG's runtime capsule; on Windows
    their wheels use different C runtimes and the capsule's exit-time destructor
    corrupts the heap (#1911). cadquery.occ_impl.swig_runtime disarms it at exit, so
    a process that solved an assembly and loaded nlopt must still exit 0."""
    code = (
        "import cadquery as cq, nlopt, sys\n"
        "a = cq.Assembly()\n"
        "a.add(cq.Workplane().box(10, 10, 10), name='b1')\n"
        "a.add(cq.Workplane().box(5, 5, 5), name='b2')\n"
        "a.constrain('b1@faces@>Z', 'b2@faces@<Z', 'Plane')\n"
        "a.solve()\n"
        "print('casadi' in sys.modules and 'nlopt' in sys.modules)\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.stdout.split() == ["True"], proc.stderr
    assert proc.returncode == 0, f"exit {proc.returncode}: {proc.stderr}"
