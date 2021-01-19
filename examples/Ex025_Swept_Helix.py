import cadquery as cq

r = 0.5  # Radius of the helix
p = 0.4  # Pitch of the helix - vertical distance between loops
h = 2.4  # Height of the helix - total height

# Helix
wire = cq.Wire.makeHelix(pitch=p, height=h, radius=r)
helix = cq.Workplane(obj=wire)

# Final result: A 2D shape swept along a helix.
result = (
    cq.Workplane("XZ")  # helix is moving up the Z axis
    .center(r, 0)  # offset isosceles trapezoid
    .polyline(((-0.15, 0.1), (0.0, 0.05), (0, 0.35), (-0.15, 0.3)))
    .close()  # make edges a wire
    .sweep(helix, isFrenet=True)  # Frenet keeps orientation as expected
)

show_object(result)
