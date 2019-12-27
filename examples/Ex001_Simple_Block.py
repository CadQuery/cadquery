import cadquery as cq

# These can be modified rather than hardcoding values for each dimension.
length = 80.0  # Length of the block
height = 60.0  # Height of the block
thickness = 10.0  # Thickness of the block

# Create a 3D block based on the dimension variables above.
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the X and Y origins to define the workplane, meaning that the
# positive Z direction is "up", and the negative Z direction is "down".
result = cq.Workplane("XY").box(length, height, thickness)

# The following method is now outdated, but can still be used to display the
# results of the script if you want
# from Helpers import show
# show(result)  # Render the result of this script

show_object(result)
