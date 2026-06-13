from cadquery.func import *

dx = 5
dy = 3
dz = 1.5

hist = History()

# make a hollow base
base_face = plane(dx, dy)
base = extrude(base_face, (0, 0, dz))
res = fillet(base, base.edges("|Z"), 0.5)
ftop = res.face(">Z")
resh = hollow(res, ftop, -0.2, history=hist, name="hollow")

# add mounting points
mid = resh.face(">Z[-2]")
f = (
    face(circle(0.1), circle(0.05))
    .moved(offset2D(base_face.wire(), -0.5).vertices())
    .moved(mid)
    .moved(z=0)
)
res = prism(resh, mid, f, base.face(">Z"), history=hist, name="mounts")

# add fillet
res = fillet(
    res,
    hist["hollow"].generated().edges("<Z") | hist["mounts"].generated().edges("<Z"),
    0.04,
)

# add a lip
top = res.face(">Z")
top_ow = top.outerWire()

res = prism(
    res,
    top,
    face(top_ow, offset2D(top_ow, -0.1)),
    0.2,
    additive=False,
    history=hist,
    name="lip",
)

# apply chamfers
res = chamfer(res, hist["lip"].modified().face(">Z").outerWire(), 0.05)
result = chamfer(
    res, compound([f.face().outerWire() for f in hist["mounts"].last()]), 0.02
)
