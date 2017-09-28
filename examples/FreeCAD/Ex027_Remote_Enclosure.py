import cadquery as cq

exploded = False        # when true, moves the base away from the top so we see
showTop = True          # When true, the top is rendered.
showCover = True        # When true, the cover is rendered

width = 2.2             # Nominal x dimension of the part
height = 0.5            # Height from bottom top to the top of the top :P
length = 1.5            # Nominal y dimension of the part
trapezoidFudge = 0.7    # ratio of trapezoid bases. set to 1.0 for cube
xHoleOffset = 0.500     # Holes are distributed symetrically about each axis
yHoleOffset = 0.500
zFilletRadius = 0.50    # Fillet radius of corners perp. to Z axis.
yFilletRadius = 0.250   # Fillet readius of the top edge of the case
lipHeight = 0.1         # The height of the lip on the inside of the cover
wallThickness = 0.06    # Wall thickness for the case
coverThickness = 0.2    # Thickness of the cover plate
holeRadius = 0.30       # Button hole radius
counterSyncAngle = 100  # Countersink angle.

xyplane = cq.Workplane("XY")
yzplane = cq.Workplane("YZ")


def trapezoid(b1, b2, h):
    "Defines a symetrical trapezoid in the XY plane."

    y = h / 2
    x1 = b1 / 2
    x2 = b2 / 2
    return (xyplane.moveTo(-x1,  y)
            .polyline([(x1,  y),
                       (x2, -y),
                       (-x2, -y)]).close())


# Defines our base shape: a box with fillets around the vertical edges.
# This has to be a function because we need to create multiple copies of
# the shape.
def base(h):
    return (trapezoid(width, width * trapezoidFudge, length)
            .extrude(h)
            .translate((0, 0, height / 2))
            .edges("Z")
            .fillet(zFilletRadius))

# start with the base shape
top = (base(height)
       # then fillet the top edge
       .edges(">Z")
       .fillet(yFilletRadius)
       # shell the solid from the bottom face, with a .060" wall thickness
       .faces("<Z")
       .shell(-wallThickness)
       # cut five button holes into the top face in a cross pattern.
       .faces(">Z")
       .workplane()
       .pushPoints([(0,            0),
                    (-xHoleOffset, 0),
                    (0,           -yHoleOffset),
                    (xHoleOffset,  0),
                    (0,            yHoleOffset)])
       .cskHole(diameter=holeRadius,
                cskDiameter=holeRadius * 1.5,
                cskAngle=counterSyncAngle))

# the bottom cover begins with the same basic shape as the top
cover = (base(coverThickness)
         # we need to move it upwards into the parent solid slightly.
         .translate((0, 0, -coverThickness + lipHeight))
         # now we subtract the top from the cover. This produces a lip on the
         # solid NOTE: that this does not account for mechanical tolerances.
         # But it looks cool.
         .cut(top)
         # try to fillet the inner edge of the cover lip. Technically this
         # fillets every edge perpendicular to the Z axis.
         .edges("#Z")
         .fillet(.020)
         .translate((0, 0, -0.5 if exploded else 0)))

# Conditionally render the parts
if showTop:
    show_object(top)
if showCover:
    show_object(cover)
