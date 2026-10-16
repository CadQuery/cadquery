import os
import subprocess
import sys

import pytest

import cadquery
from cadquery.occ_impl import exporters
from cadquery.occ_impl.exporters import assembly, dxf, vtk


def test_import_does_not_load_ezdxf_or_vtk():
    # a fresh interpreter: this process has ezdxf and vtk loaded by other tests
    code = (
        "import sys, cadquery as cq;"
        "print({m.split('.')[0] for m in sys.modules} & {'ezdxf', 'vtkmodules'});"
        # the submodules stay reachable through the packages
        "cq.exporters.assembly.ExportModes, cq.exporters.dxf, cq.exporters.vtk;"
        "print('ok')"
    )
    # run next to the package under test; only stdout is checked, since the
    # interpreter may crash on exit on Windows (#1911)
    out = subprocess.run(
        [sys.executable, "-u", "-c", code],
        cwd=os.path.dirname(os.path.dirname(cadquery.__file__)),
        capture_output=True,
        text=True,
    )

    assert out.stdout.split() == ["set()", "ok"], out.stdout + out.stderr


def test_exporters_lazy_names():
    # the submodules are attributes here already, so ask __getattr__ directly
    assert exporters.__getattr__("dxf") is dxf
    assert exporters.__getattr__("vtk") is vtk
    assert exporters.__getattr__("assembly") is assembly

    assert exporters.exportDXF is dxf.exportDXF
    assert exporters.exportDXFProjection is dxf.exportDXFProjection
    assert exporters.DxfDocument is dxf.DxfDocument
    assert exporters.exportVTP is vtk.exportVTP

    with pytest.raises(AttributeError):
        exporters.nonexistent
