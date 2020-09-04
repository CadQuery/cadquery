import pytest
import os

import cadquery as cq
from cadquery.occ_impl.exporters.assembly import exportAssembly, exportCAF


@pytest.fixture
def simple_assy():

    b1 = cq.Solid.makeBox(1,1,1)
    b2 = cq.Workplane().box(1, 1, 2)
    b3 = cq.Workplane().pushPoints([(0, 0), (-2, -5)]).box(1, 1, 3)

    assy = cq.Assembly(b1, loc=cq.Location(cq.Vector(2, -5, 0)))
    assy.add(b2, loc=cq.Location(cq.Vector(1, 1, 0)))
    assy.add(b3, loc=cq.Location(cq.Vector(2, 3, 0)))

    return assy


@pytest.fixture
def nested_assy():

    b1 = cq.Workplane().box(1, 1, 1)
    b2 = cq.Workplane().box(1, 1, 1)
    b3 = cq.Workplane().pushPoints([(-2, 0), (2, 0)]).box(1, 1, .5)

    assy = cq.Assembly(b1, loc=cq.Location(cq.Vector(0, 0, 0)), name="TOP")
    assy2 = cq.Assembly(b2, loc=cq.Location(cq.Vector(0, 4, 0)), name="SECOND")
    assy2.add(b3, loc=cq.Location(cq.Vector(0, 4, 0)), name="BOTTOM")

    assy.add(assy2)

    return assy


def test_assembly(simple_assy, nested_assy):

    # basic checks
    assert len(simple_assy.objects) == 3
    assert len(simple_assy.children) == 2
    assert len(simple_assy.shapes) == 1

    assert len(nested_assy.objects) == 3
    assert len(nested_assy.children) == 1

    # bottm-up traversal
    kvs = list(nested_assy.traverse())

    assert kvs[0][0] == "BOTTOM"
    assert len(kvs[0][1].shapes[0].Solids()) == 2
    assert kvs[-1][0] == "TOP"


def test_step_export(nested_assy):

    exportAssembly(nested_assy, "nested.step")

    w = cq.importers.importStep("nested.step")
    assert w.solids().size() == 4

    # check that locations were applied correctly
    c = cq.Compound.makeCompound(w.solids().vals()).Center()
    c.toTuple()
    assert pytest.approx(c.toTuple()) == (0, 4, 0)


def test_native_export(simple_assy):

    exportCAF(simple_assy, "assy.xml")

    # only sanity check for now
    assert os.path.exists("assy.xml")
