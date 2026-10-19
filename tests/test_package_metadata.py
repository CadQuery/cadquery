from contextlib import chdir
from pathlib import Path
from runpy import run_path

import setuptools


def test_pip_install_requires_excludes_crashing_casadi_nlopt_pair(monkeypatch):
    root = Path(__file__).parents[1]
    captured = {}

    def fake_setup(**kwargs):
        captured.update(kwargs)

    monkeypatch.delenv("APPVEYOR", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.delenv("CONDA_PY", raising=False)
    monkeypatch.delenv("READTHEDOCS", raising=False)
    monkeypatch.setattr(setuptools, "setup", fake_setup)

    with chdir(root):
        run_path(str(root / "setup.py"))

    assert "casadi<3.8" in captured["install_requires"]
