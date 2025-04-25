"""
Example 028 - VTK Visualization with Materials and Environment Mapping

This example demonstrates how to:
1. Create 3D objects with different materials (simple color, common material, PBR material)
2. Set up a VTK visualization with environment mapping
3. Use HDR textures for realistic lighting and reflections
4. Configure camera and rendering settings

The example creates three objects:
- A red box with a simple color material
- A gold cylinder with common material properties (ambient, diffuse, specular)
- A chrome sphere with PBR (Physically Based Rendering) material properties

The scene is rendered with an HDR environment map that provides realistic lighting
and reflections on the materials.

Note: Emission support will be added in a future version with proper texture support.
"""

from pathlib import Path
from cadquery.occ_impl.assembly import toVTK
from vtkmodules.vtkRenderingCore import (
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkTexture,
)
from vtkmodules.vtkIOImage import vtkHDRReader
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingOpenGL2 import vtkOpenGLSkybox
import cadquery as cq
import os


# Create basic shapes for our example
red_box = cq.Workplane().box(10, 10, 10)  # Create a 10x10x10 box
gold_cylinder = cq.Workplane().cylinder(
    20, 5
)  # Create a cylinder with radius 5 and height 20
chrome_sphere = cq.Workplane().sphere(8)  # Create a sphere with radius 8

# Create a hexagonal prism
glass_hex = (
    cq.Workplane("XY")
    .polygon(6, 15)  # Create a hexagon with radius 15
    .extrude(10)  # Extrude 10 units in Z direction
)

# Create an assembly to hold our objects
assy = cq.Assembly(name="material_test")

# Add a red box with a simple color material
# This demonstrates the most basic material type
assy.add(
    red_box,
    name="red_box",
    loc=cq.Location((-60, 0, 0)),  # Position the box to the left
    material=cq.Material(
        name="Red",
        description="Simple red material",
        density=1000.0,
        color=cq.Color(1, 0, 0, 1),  # Pure red with full opacity
    ),
)

# Add a gold cylinder with common material properties
# This demonstrates traditional material properties (ambient, diffuse, specular)
assy.add(
    gold_cylinder,
    name="gold_cylinder",
    loc=cq.Location((-20, 0, 0)),  # Position the cylinder to the left of center
    material=cq.Material(
        name="Gold",
        description="Metallic gold material",
        density=19320.0,  # Actual density of gold in kg/m³
        simple=cq.SimpleMaterial(
            ambient_color=cq.Color(0.24, 0.2, 0.07),  # Dark gold ambient color
            diffuse_color=cq.Color(0.75, 0.6, 0.22),  # Gold diffuse color
            specular_color=cq.Color(0.63, 0.56, 0.37),  # Light gold specular color
            shininess=0.8,  # High shininess for metallic look
            transparency=0.0,  # Fully opaque
        ),
    ),
)

# Add a chrome sphere with PBR material properties
# This demonstrates modern physically based rendering materials
assy.add(
    chrome_sphere,
    name="chrome_sphere",
    loc=cq.Location((20, 0, 0)),  # Position the sphere to the right of center
    material=cq.Material(
        name="Chrome",
        description="Polished chrome material",
        density=7190.0,  # Density of chrome in kg/m³
        pbr=cq.PbrMaterial(
            base_color=cq.Color(0.8, 0.8, 0.8),  # Light gray base color
            metallic=1.0,  # Fully metallic
            roughness=0.1,  # Very smooth surface
            refraction_index=2.4,  # High refraction index for chrome
        ),
    ),
)

# Add a glass hexagonal prism with PBR material properties
# This demonstrates transparent materials with PBR
assy.add(
    glass_hex,
    name="glass_hex",
    loc=cq.Location((60, 0, 0)),  # Position the hexagon to the right
    material=cq.Material(
        name="Glass",
        description="Clear glass material",
        density=2500.0,  # Density of glass in kg/m³
        pbr=cq.PbrMaterial(
            base_color=cq.Color(0.9, 0.9, 0.9, 0.1),  # Light gray with transparency
            metallic=0,  # Non-metallic
            roughness=0.1,  # Smooth surface
            refraction_index=2,  # Typical glass refraction index
        ),
    ),
)


# Convert the assembly to VTK format for visualization
renderer = toVTK(assy, edges=False)

# Set up the render window
render_window = vtkRenderWindow()
render_window.SetSize(1920, 1080)  # Set to Full HD resolution
render_window.AddRenderer(renderer)

# Load the HDR texture for environment mapping
reader = vtkHDRReader()
reader.SetFileName(Path(__file__).parent / "golden_gate_hills_1k.hdr")
reader.Update()

# Create and configure the texture
texture = vtkTexture()
texture.SetColorModeToDirectScalars()  # Use HDR values directly
texture.SetInputConnection(reader.GetOutputPort())
texture.MipmapOn()  # Enable mipmapping for better quality
texture.InterpolateOn()  # Enable texture interpolation
texture.SetRepeat(False)  # Prevent texture repetition
texture.SetEdgeClamp(True)  # Clamp texture edges

# Create a skybox using the HDR texture
skybox = vtkOpenGLSkybox()
skybox.SetTexture(texture)
skybox.SetProjectionToCube()  # Use cube map projection
renderer.AddActor(skybox)

# Set up PBR environment lighting
renderer.UseImageBasedLightingOn()  # Enable image-based lighting
renderer.SetEnvironmentTexture(texture)  # Use HDR texture for lighting
renderer.UseSphericalHarmonicsOn()  # Use spherical harmonics for better performance

# Set up the interactor for user interaction
interactor = vtkRenderWindowInteractor()
interactor.SetRenderWindow(render_window)

# Configure the renderer and camera
renderer = render_window.GetRenderers().GetFirstRenderer()
renderer.SetBackground(0.2, 0.3, 0.4)  # Set dark blue-gray background
camera = renderer.GetActiveCamera()
camera.SetPosition(0, -10, 200)  # Position camera above the scene
camera.SetFocalPoint(0, 0, 0)  # Look at the center of the scene
camera.SetViewUp(0, 1, 0)  # Set Y axis as up to see horizon
camera.SetViewAngle(30)  # Set field of view

# Set up trackball camera interaction style
interactor_style = vtkInteractorStyleTrackballCamera()
interactor.SetInteractorStyle(interactor_style)

if __name__ == "__main__":
    # Start the visualization
    interactor.Initialize()
    interactor.Start()
