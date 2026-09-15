import os
import subprocess
import sys

import cadquery


def test_import_does_not_load_ezdxf():
    # a fresh interpreter: this process has ezdxf loaded by other tests
    code = (
        "import sys, cadquery;"
        "print({m.split('.')[0] for m in sys.modules} & {'ezdxf'})"
    )
    # run next to the package under test; only stdout is checked, since the
    # interpreter may crash on exit on Windows (#1911)
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=os.path.dirname(os.path.dirname(cadquery.__file__)),
        capture_output=True,
        text=True,
    )

    assert out.stdout.strip().endswith("set()"), out.stdout + out.stderr
