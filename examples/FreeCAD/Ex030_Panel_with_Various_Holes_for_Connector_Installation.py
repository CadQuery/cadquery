import cadquery as cq

# The dimensions of the model. These can be modified rather than changing the
# object's code directly.
width = 400
height = 500
thickness = 2

# Create a plate with two polygons cut through it
result = cq.Workplane("front").box(width, height, thickness)

h_sep = 60
for idx in range(4):
    result = result.workplane(offset=1, centerOption='CenterOfBoundBox').center(157,210-idx*h_sep).moveTo(-23.5,0).circle(1.6).moveTo(23.5,0).circle(1.6).moveTo(-17.038896,-5.7).threePointArc((-19.44306,-4.70416),(-20.438896,-2.3)).lineTo(-21.25,2.3).threePointArc((-20.25416,4.70416),(-17.85,5.7)).lineTo(17.85,5.7).threePointArc((20.25416,4.70416),(21.25,2.3)).lineTo(20.438896,-2.3).threePointArc((19.44306,-4.70416),(17.038896,-5.7)).close().cutThruAll()

for idx in range(4):
    result = result.workplane(offset=1, centerOption='CenterOfBoundBox').center(157,-30-idx*h_sep).moveTo(-16.65,0).circle(1.6).moveTo(16.65,0).circle(1.6).moveTo(-10.1889,-5.7).threePointArc((-12.59306,-4.70416),(-13.5889,-2.3)).lineTo(-14.4,2.3).threePointArc((-13.40416,4.70416),(-11,5.7)).lineTo(11,5.7).threePointArc((13.40416,4.70416),(14.4,2.3)).lineTo(13.5889,-2.3).threePointArc((12.59306,-4.70416),(10.1889,-5.7)).close().cutThruAll()

h_sep4DB9 = 30
for idx in range(8):
    result = result.workplane(offset=1, centerOption='CenterOfBoundBox').center(91,225-idx*h_sep4DB9).moveTo(-12.5,0).circle(1.6).moveTo(12.5,0).circle(1.6).moveTo(-6.038896,-5.7).threePointArc((-8.44306,-4.70416),(-9.438896,-2.3)).lineTo(-10.25,2.3).threePointArc((-9.25416,4.70416),(-6.85,5.7)).lineTo(6.85,5.7).threePointArc((9.25416,4.70416),(10.25,2.3)).lineTo(9.438896,-2.3).threePointArc((8.44306,-4.70416),(6.038896,-5.7)).close().cutThruAll()

for idx in range(4):
    result = result.workplane(offset=1, centerOption='CenterOfBoundBox').center(25,210-idx*h_sep).moveTo(-23.5,0).circle(1.6).moveTo(23.5,0).circle(1.6).moveTo(-17.038896,-5.7).threePointArc((-19.44306,-4.70416),(-20.438896,-2.3)).lineTo(-21.25,2.3).threePointArc((-20.25416,4.70416),(-17.85,5.7)).lineTo(17.85,5.7).threePointArc((20.25416,4.70416),(21.25,2.3)).lineTo(20.438896,-2.3).threePointArc((19.44306,-4.70416),(17.038896,-5.7)).close().cutThruAll()

for idx in range(4):
    result = result.workplane(offset=1, centerOption='CenterOfBoundBox').center(25,-30-idx*h_sep).moveTo(-16.65,0).circle(1.6).moveTo(16.65,0).circle(1.6).moveTo(-10.1889,-5.7).threePointArc((-12.59306,-4.70416),(-13.5889,-2.3)).lineTo(-14.4,2.3).threePointArc((-13.40416,4.70416),(-11,5.7)).lineTo(11,5.7).threePointArc((13.40416,4.70416),(14.4,2.3)).lineTo(13.5889,-2.3).threePointArc((12.59306,-4.70416),(10.1889,-5.7)).close().cutThruAll()

for idx in range(8):
    result = result.workplane(offset=1, centerOption='CenterOfBoundBox').center(-41,225-idx*h_sep4DB9).moveTo(-12.5,0).circle(1.6).moveTo(12.5,0).circle(1.6).moveTo(-6.038896,-5.7).threePointArc((-8.44306,-4.70416),(-9.438896,-2.3)).lineTo(-10.25,2.3).threePointArc((-9.25416,4.70416),(-6.85,5.7)).lineTo(6.85,5.7).threePointArc((9.25416,4.70416),(10.25,2.3)).lineTo(9.438896,-2.3).threePointArc((8.44306,-4.70416),(6.038896,-5.7)).close().cutThruAll()

for idx in range(4):
    result = result.workplane(offset=1, centerOption='CenterOfBoundBox').center(-107,210-idx*h_sep).moveTo(-23.5,0).circle(1.6).moveTo(23.5,0).circle(1.6).moveTo(-17.038896,-5.7).threePointArc((-19.44306,-4.70416),(-20.438896,-2.3)).lineTo(-21.25,2.3).threePointArc((-20.25416,4.70416),(-17.85,5.7)).lineTo(17.85,5.7).threePointArc((20.25416,4.70416),(21.25,2.3)).lineTo(20.438896,-2.3).threePointArc((19.44306,-4.70416),(17.038896,-5.7)).close().cutThruAll()

for idx in range(4):
    result = result.workplane(offset=1, centerOption='CenterOfBoundBox').center(-107,-30-idx*h_sep).circle(14).rect(24.7487,24.7487, forConstruction=True).vertices().hole(3.2).cutThruAll()

for idx in range(8):
    result = result.workplane(offset=1, centerOption='CenterOfBoundBox').center(-173,225-idx*h_sep4DB9).moveTo(-12.5,0).circle(1.6).moveTo(12.5,0).circle(1.6).moveTo(-6.038896,-5.7).threePointArc((-8.44306,-4.70416),(-9.438896,-2.3)).lineTo(-10.25,2.3).threePointArc((-9.25416,4.70416),(-6.85,5.7)).lineTo(6.85,5.7).threePointArc((9.25416,4.70416),(10.25,2.3)).lineTo(9.438896,-2.3).threePointArc((8.44306,-4.70416),(6.038896,-5.7)).close().cutThruAll()

for idx in range(4):
    result = result.workplane(offset=1, centerOption='CenterOfBoundBox').center(-173,-30-idx*h_sep).moveTo(-2.9176,-5.3).threePointArc((-6.05,0),(-2.9176,5.3)).lineTo(2.9176,5.3).threePointArc((6.05,0),(2.9176,-5.3)).close().cutThruAll()

# Render the solid
show_object(result)
