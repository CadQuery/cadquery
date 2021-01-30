import pytest

import cadquery as cq
from cadquery import cqgi
from glob import glob


@pytest.mark.parametrize("p", glob("examples/*.py"))
def test_example(p):

    # read the code
    with open(p) as f:
        code = f.read()

    # build
    res = cqgi.parse(code).build()

    assert res.exception is None

    # check if the resulting objects are valid
    for r in res.results:
        if isinstance(r, cq.Workplane):
            for v in r.vals():
                if isinstance(v, cq.Shape):
                    assert v.IsValid()
        elif isinstance(r, cq.Shape):
            assert r.IsValid()
