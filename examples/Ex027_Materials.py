import cadquery as cq
from cadquery.occ_impl.exporters.assembly import exportStepMeta

# Create a simple cube
cube = cq.Workplane().box(10, 10, 10)

# Define different materials
# 1. Simple color material
red_material = cq.Material(
    name="Red Plastic",
    description="A simple red plastic material",
    density=1200,  # kg/m³
    color=cq.Color(1.0, 0.0, 0.0, 1.0),  # Red with full opacity
)

# 2. Common (legacy) material with traditional properties
metal_material = cq.Material(
    name="Polished Steel",
    description="A shiny metallic material",
    density=7850,  # kg/m³
    common=cq.CommonMaterial(
        ambient_color=cq.Color(0.2, 0.2, 0.2, 1.0),
        diffuse_color=cq.Color(0.5, 0.5, 0.5, 1.0),
        specular_color=cq.Color(0.8, 0.8, 0.8, 1.0),
        emissive_color=cq.Color(0.0, 0.0, 0.0, 1.0),
        shininess=0.8,  # High shininess for metallic look
        transparency=0.0,
    ),
)

# 3. PBR material with modern properties
glass_material = cq.Material(
    name="Clear Glass",
    description="A transparent glass material",
    density=2500,  # kg/m³
    pbr=cq.PbrMaterial(
        base_color=cq.Color(0.9, 0.9, 0.9, 0.3),  # Light gray with transparency
        metallic=0.0,  # Non-metallic
        roughness=0.1,  # Very smooth
        refraction_index=1.5,  # Typical glass refractive index
    ),
)

# 4. Combined material with both common and PBR properties
gold_material = cq.Material(
    name="Gold",
    description="A golden material with both traditional and PBR properties",
    density=19300,  # kg/m³
    common=cq.CommonMaterial(
        ambient_color=cq.Color(0.2, 0.2, 0.0, 1.0),
        diffuse_color=cq.Color(0.8, 0.8, 0.0, 1.0),
        specular_color=cq.Color(1.0, 1.0, 0.0, 1.0),
        emissive_color=cq.Color(0.0, 0.0, 0.0, 1.0),
        shininess=0.9,
        transparency=0.0,
    ),
    pbr=cq.PbrMaterial(
        base_color=cq.Color(1.0, 0.8, 0.0, 1.0),  # Gold color
        metallic=1.0,  # Fully metallic
        roughness=0.2,  # Slightly rough
        refraction_index=1.0,  # Minimum valid refractive index for metals
    ),
)

# Create an assembly with different materials
assy = cq.Assembly()
assy.add(cube, name="red_cube", material=red_material)
assy.add(cube.translate((15, 0, 0)), name="metal_cube", material=metal_material)
assy.add(cube.translate((30, 0, 0)), name="glass_cube", material=glass_material)
assy.add(cube.translate((45, 0, 0)), name="gold_cube", material=gold_material)

# Export as OBJ and GLTF to showcase materials
assy.export("materials.step")  # STEP format
exportStepMeta(assy, "materials_meta.step")  # STEP format with metadata
assy.export("materials.glb")  # GLTF format (binary) with PBR materials

# Show the assembly in the UI
show_object(assy)
