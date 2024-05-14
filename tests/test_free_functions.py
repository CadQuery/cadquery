from cadquery.occ_impl.shapes import (
    vertex,
    segment,
    polyline,
    polygon,
    rect,
    circle,
    ellipse,
    plane,
    box,
    cylinder,
    sphere,
    torus,
    cone,
    spline,
    text,
    clean,
    fill,
    cap,
    extrude,
    fillet,
    chamfer,
    revolve,
    offset,
    loft,
    sweep,
    cut,
    fuse,
    intersect,
    wire,
    face,
    shell,
    solid,
    compound,
    Location,
    Shape,
    _get_one_wire,
    _get_wires,
    _get,
    _get_one,
    _get_edges,
)

from pytest import approx, raises
from math import pi

#%% test utils


def assert_all_valid(*objs: Shape):

    for o in objs:
        assert o.isValid()


def vector_equal(v1, v2):

    return v1.toTuple() == approx(v2.toTuple())


#%% utils


def test_utils():

    r1 = _get_one_wire(rect(1, 1))

    assert r1.ShapeType() == "Wire"

    r2 = list(_get_wires(compound(r1, r1.moved(Location(0, 0, 1)))))

    assert len(r2) == 2
    assert all(el.ShapeType() == "Wire" for el in r2)

    with raises(ValueError):
        list(_get_wires(box(1, 1, 1)))

    r3 = list(_get(box(1, 1, 1).moved(Location(), Location(2, 0, 0)), "Solid"))

    assert (len(r3)) == 2
    assert all(el.ShapeType() == "Solid" for el in r3)

    with raises(ValueError):
        list(_get(box(1, 1, 1), "Shell"))

    r4 = _get_one(compound(box(1, 1, 1), box(2, 2, 2)), "Solid")

    assert r4.ShapeType() == "Solid"

    with raises(ValueError):
        _get_one(rect(1, 1), ("Solid", "Shell"))

    with raises(ValueError):
        list(_get_edges(fill(circle(1))))


#%% constructors


def test_constructors():

    # wire
    e1 = segment((0, 0), (0, 1))
    e2 = segment((0, 1), (1, 1))
    e3 = segment((1, 1), (1, 0))
    e4 = segment((1, 0), (0, 0))

    w1 = wire(e1, e2, e3, e4)
    w2 = wire((e1, e2, e3, e4))

    assert w1.Length() == approx(4)
    assert w2.Length() == approx(4)

    # face
    f1 = face(w1, circle(0.1).moved(Location(0.5, 0.5, 0)))
    f2 = face((w1,))

    assert f1.Area() < 1
    assert len(f1.Wires()) == 2
    assert f2.Area() == approx(1)
    assert len(f2.Wires()) == 1

    with raises(ValueError):
        face(e1)

    # shell
    b = box(1, 1, 1)

    sh1 = shell(b.Faces())
    sh2 = shell(*b.Faces())

    assert sh1.Area() == approx(6)
    assert sh2.Area() == approx(6)

    # solid
    s1 = solid(b.Faces())
    s2 = solid(*b.Faces())

    assert s1.Volume() == approx(1)
    assert s2.Volume() == approx(1)

    # compound
    c1 = compound(b.Faces())
    c2 = compound(*b.Faces())

    assert len(list(c1)) == 6
    assert len(list(c2)) == 6

    for f in list(c1) + list(c2):
        assert f.ShapeType() == "Face"


#%% primitives


def test_vertex():

    v = vertex((1, 2,))

    assert v.isValid()
    assert v.Center().toTuple() == approx((1, 2, 0))

    v = vertex(1, 2, 3)

    assert v.isValid()
    assert v.Center().toTuple() == approx((1, 2, 3))


def test_segment():

    s = segment((0, 0, 0), (0, 0, 1))

    assert s.isValid()
    assert s.Length() == approx(1)


def test_polyline():

    s = polyline((0, 0), (0, 1), (1, 1))

    assert s.isValid()
    assert s.Length() == approx(2)


def test_polygon():

    s = polygon((0, 0), (0, 1), (1, 1), (1, 0))

    assert s.isValid()
    assert s.IsClosed()
    assert s.Length() == approx(4)


def test_rect():

    s = rect(2, 1)

    assert s.isValid()
    assert s.IsClosed()
    assert s.Length() == approx(6)


def test_circle():

    s = circle(1)

    assert s.isValid()
    assert s.IsClosed()
    assert s.Length() == approx(2 * pi)


def test_ellipse():

    s = ellipse(3, 2)

    assert s.isValid()
    assert s.IsClosed()
    assert face(s).Area() == approx(6 * pi)


def test_plane():

    s = plane(1, 2)

    assert s.isValid()
    assert s.Area() == approx(2)


def test_box():

    s = box(1, 1, 1)

    assert s.isValid()
    assert s.Volume() == approx(1)


def test_cylinder():

    s = cylinder(2, 1)

    assert s.isValid()
    assert s.Volume() == approx(pi)


def test_sphere():

    s = sphere(2)

    assert s.isValid()
    assert s.Volume() == approx(4 / 3 * pi)


def test_torus():

    s = torus(10, 2)

    assert s.isValid()
    assert s.Volume() == approx(2 * pi ** 2 * 5)


def test_cone():

    s = cone(2, 1)

    assert s.isValid()
    assert s.Volume() == approx(1 / 3 * pi)

    s = cone(2, 1, 1)

    assert s.isValid()
    assert s.Volume() == approx(1 / 3 * pi * (1 + 0.25 + 0.5))


def test_spline():

    s1 = spline((0, 0), (0, 1))
    s2 = spline([(0, 0), (0, 1)])
    s3 = spline([(0, 0), (0, 1)], [(1, 0), (-1, 0)])

    assert s1.Length() == approx(1)
    assert s2.Length() == approx(1)
    assert s3.Length() > 0
    assert s3.tangentAt(0).toTuple() == approx((1, 0, 0))
    assert s3.tangentAt(1).toTuple() == approx((-1, 0, 0))


def test_text():

    r1 = text("CQ", 10)

    assert len(r1.Faces()) == 2
    assert len(r1.Wires()) == 3
    assert r1.Area() > 0.0

    # test alignemnt
    r2 = text("CQ", 10, halign="left")
    r3 = text("CQ", 10, halign="right")
    r4 = text("CQ", 10, valign="bottom")
    r5 = text("CQ", 10, valign="top")

    assert r2.faces("<X").Center().x > r1.faces("<X").Center().x
    assert r1.faces("<X").Center().x > r3.faces("<X").Center().x
    assert r4.faces("<X").Center().y > r1.faces("<X").Center().y
    assert r1.faces("<X").Center().y > r5.faces("<X").Center().x


#%% bool ops
def test_operators():

    b1 = box(1, 1, 1).moved(Location(-0.5, -0.5, -0.5))  # small box
    b2 = box(2, 2, 2).moved(Location(-1, -1, -1))  # large box
    b3 = b1.moved(Location(0, 0, 1e-4))  # almost b1
    f = plane(3, 3)  # face
    e = segment((-2, 0), (2, 0))  # edge

    assert (b2 - b1).Volume() == approx(8 - 1)

    assert (b2 * b1).Volume() == approx(1)
    assert (b1 * f).Area() == approx(1)
    assert (b1 * e).Length() == approx(1)
    assert (f * e).Length() == approx(3)

    assert (b2 + b1).Volume() == approx(8)

    assert len((b1 / f).Solids()) == 2

    # test fuzzy ops
    assert len((b1 + b3).Faces()) == 14
    assert (b1 - b3).Volume() > 0
    assert (b1 * b3).Volume() < 1

    assert len(fuse(b1, b3, 1e-3).Faces()) == 6
    assert len(cut(b1, b3, 1e-3).Faces()) == 0
    assert len(intersect(b1, b3, 1e-3).Faces()) == 6


#%% moved
def test_moved():

    b = box(1, 1, 1)
    l1 = Location((-1, 0, 0))
    l2 = Location((1, 0, 0))
    l3 = Location((0, 1, 0), (45, 0, 0))
    l4 = Location((0, -1, 0), (-45, 0, 0))

    bs1 = b.moved(l1, l2)
    bs2 = b.moved((l1, l2))

    assert bs1.Volume() == approx(2)
    assert len(bs1.Solids()) == 2

    assert bs2.Volume() == approx(2)
    assert len(bs2.Solids()) == 2

    # nested move
    bs3 = bs1.moved(l3, l4)

    assert bs3.Volume() == approx(4)
    assert len(bs3.Solids()) == 4

    # move with VectorLike
    bs4 = b.moved((0, 0, 1), (0, 0, -1))
    bs5 = bs4.moved((1, 0, 0)).move((-1, 0, 0))

    assert bs4.Volume() == approx(2)
    assert vector_equal(bs5.Center(), bs4.Center())

    # move with direct params
    bs6 = b.moved((0, 0, 1)).moved(0, 0, -1)
    bs7 = b.moved((0, 0, 1)).moved(z=-1)
    bs8 = b.moved(Location((0, 0, 0), (-45, 0, 0))).moved(rx=45)
    bs9 = b.moved().move(Location((0, 0, 0), (-45, 0, 0))).move(rx=45)

    assert vector_equal(bs6.Center(), b.Center())
    assert vector_equal(bs7.Center(), b.Center())
    assert vector_equal(bs8.edges(">Z").Center(), b.edges(">Z").Center())
    assert vector_equal(bs9.edges(">Z").Center(), b.edges(">Z").Center())


#%% ops
def test_clean():

    b1 = box(1, 1, 1)
    b2 = b1.moved(Location(1, 0, 0))

    len((b1 + b2).Faces()) == 10
    len(clean(b1 + b2).Faces()) == 6


def test_fill():

    w1 = rect(1, 1)
    w2 = rect(0.5, 0.5).moved(Location(0, 0, 1))

    f1 = fill(w1)
    f2 = fill(w1, [(0, 0, 1)])
    f3 = fill(w1, [w2])

    assert f1.isValid()
    assert f1.Area() == approx(1)

    assert f2.isValid()
    assert f2.Area() > 1

    assert f3.isValid()
    assert f3.Area() > 1
    assert len(f3.Edges()) == 4
    assert len(f3.Wires()) == 1


def test_cap():

    s = extrude(circle(1), (0, 0, 1))

    f1 = cap(s.edges(">Z"), s, [(0, 0, 1.5)])
    f2 = cap(s.edges(">Z"), s, [circle(0.5).moved(Location(0, 0, 2))])

    assert_all_valid(f1, f2)
    assert f1.Area() > pi
    assert f2.Area() > pi


def test_fillet():

    b = box(1, 1, 1)

    r = fillet(b, b.edges(">Z"), 0.1)

    assert r.isValid()
    assert len(r.Edges()) == 20
    assert r.faces(">Z").Area() < 1


def test_chamfer():

    b = box(1, 1, 1)

    r = chamfer(b, b.edges(">Z"), 0.1)

    assert r.isValid()
    assert len(r.Edges()) == 20
    assert r.faces(">Z").Area() < 1


def test_extrude():

    v = vertex(0, 0, 0)
    e = segment((0, 0), (0, 1))
    w = rect(1, 1)
    f = fill(w)

    d = (0, 0, 1)

    r1 = extrude(v, d)
    r2 = extrude(e, d)
    r3 = extrude(w, d)
    r4 = extrude(f, d)

    assert r1.Length() == approx(1)
    assert r2.Area() == approx(1)
    assert r3.Area() == approx(4)
    assert r4.Volume() == approx(1)


def test_revolve():

    w = rect(1, 1)

    r = revolve(w, (0.5, 0, 0), (0, 1, 0))

    assert r.Volume() == approx(4 * pi)


def test_offset():

    f = plane(1, 1)
    s = box(1, 1, 1).shells()

    r1 = offset(f, 1)
    r2 = offset(s, -0.25)

    assert r1.Volume() == approx(1)
    assert r2.Volume() == approx(1 - 0.5 ** 3)


def test_sweep():

    w1 = rect(1, 1)
    w2 = w1.moved(Location(0, 0, 1))

    p1 = segment((0, 0, 0), (0, 0, 1))
    p2 = spline((w1.Center(), w2.Center()), ((-0.5, 0, 1), (0.5, 0, 1)))

    r1 = sweep(w1, p1)
    r2 = sweep((w1, w2), p1)
    r3 = sweep(w1, p1, cap=True)
    r4 = sweep((w1, w2), p1, cap=True)
    r5 = sweep((w1, w2), p2, cap=True)

    assert_all_valid(r1, r2, r3, r4, r5)

    assert r1.Area() == approx(4)
    assert r2.Area() == approx(4)
    assert r3.Volume() == approx(1)
    assert r4.Volume() == approx(1)
    assert r5.Volume() > 0
    assert len(r5.Faces()) == 6


def test_loft():

    w1 = circle(1)
    w2 = ellipse(1.5, 1).move(0, y=1)
    w3 = circle(1).moved(z=4, rx=15)

    w4 = segment((0, 0), (1, 0))
    w5 = w4.moved(0, 0, 1)

    r1 = loft(w1, w2, w3)  # loft
    r2 = loft(w1, w2, w3, ruled=True)  # ruled loft
    r3 = loft([w1, w2, w3])  # overload
    r4 = loft(w1, w2, w3, cap=True)  # capped loft
    r5 = loft(w4, w5)  # loft with open edges

    assert_all_valid(r1, r2, r3, r4, r5)

    assert len(r1.Faces()) == 1
    assert len(r2.Faces()) == 2
    assert len((r1 - r3).Faces()) == 0
    assert r4.Volume() > 0
    assert r5.Area() == approx(1)
