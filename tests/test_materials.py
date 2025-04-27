import re
import pytest
from cadquery.materials import Color, SimpleMaterial, PbrMaterial, Material
import cadquery as cq
import os
import json
from tests.test_assembly import read_step, get_doc_nodes
from cadquery.occ_impl.exporters.assembly import exportStepMeta, _vtkRenderWindow
from cadquery.occ_impl.assembly import toJSON, toVTKAssy
from tempfile import TemporaryDirectory
from shutil import make_archive
from vtkmodules.vtkIOExport import vtkJSONSceneExporter


def approx_equal_tuples(tuple1, tuple2, rel=1e-6, abs=1e-12):
    """Compare two tuples of floats for approximate equality.
    
    Args:
        tuple1: First tuple of floats
        tuple2: Second tuple of floats
        rel: Relative tolerance (default: 1e-6)
        abs: Absolute tolerance (default: 1e-12)
    
    Returns:
        bool: True if tuples are approximately equal
    """
    if len(tuple1) != len(tuple2):
        return False
    return all(
        pytest.approx(v1, rel=rel, abs=abs) == v2 for v1, v2 in zip(tuple1, tuple2)
    )


class TestColor:
    def test_default_constructor(self):
        color = Color()
        assert color.red == 1.0
        assert color.green == 1.0
        assert color.blue == 0.0
        assert color.alpha == 1.0

    def test_rgb_constructor(self):
        color = Color(0.1, 0.2, 0.3)
        assert color.red == 0.1
        assert color.green == 0.2
        assert color.blue == 0.3
        assert color.alpha == 1.0

    def test_rgba_constructor(self):
        color = Color(0.1, 0.2, 0.3, 0.4)
        assert color.red == 0.1
        assert color.green == 0.2
        assert color.blue == 0.3
        assert color.alpha == 0.4

    def test_kwargs_constructor(self):
        color = Color(red=0.1, green=0.2, blue=0.3, alpha=0.4)
        assert color.red == 0.1
        assert color.green == 0.2
        assert color.blue == 0.3
        assert color.alpha == 0.4

    def test_invalid_values(self):
        with pytest.raises(ValueError):
            Color(1.5, 0.2, 0.3)  # r > 1.0
        with pytest.raises(ValueError):
            Color(0.1, -0.2, 0.3)  # g < 0.0
        with pytest.raises(ValueError):
            Color(0.1, 0.2, 0.3, 1.5)  # a > 1.0

    def test_rgb_method(self):
        color = Color(0.1, 0.2, 0.3)
        assert color.rgb() == (0.1, 0.2, 0.3)

    def test_rgba_method(self):
        color = Color(0.1, 0.2, 0.3, 0.4)
        assert color.rgba() == (0.1, 0.2, 0.3, 0.4)

    def test_equality(self):
        color1 = Color(0.1, 0.2, 0.3, 0.4)
        color2 = Color(0.1, 0.2, 0.3, 0.4)
        color3 = Color(0.2, 0.2, 0.3, 0.4)
        assert color1 == color2
        assert color1 != color3
        assert color1 != "not a color"

    def test_hash(self):
        color1 = Color(0.1, 0.2, 0.3, 0.4)
        color2 = Color(0.1, 0.2, 0.3, 0.4)
        color3 = Color(0.2, 0.2, 0.3, 0.4)
        assert hash(color1) == hash(color2)
        assert hash(color1) != hash(color3)

    def test_repr(self):
        color = Color(0.1, 0.2, 0.3, 0.4)
        assert repr(color) == "Color(r=0.1, g=0.2, b=0.3, a=0.4)"

    def test_str(self):
        color = Color(0.1, 0.2, 0.3, 0.4)
        assert str(color) == "(0.1, 0.2, 0.3, 0.4)"

    def test_occt_conversion(self):
        c1 = cq.Color("red")
        occt_c1 = c1.to_occ_rgba()
        assert occt_c1.GetRGB().Red() == 1
        assert occt_c1.Alpha() == 1

        c2 = cq.Color(1, 0, 0)
        occt_c2 = c2.to_occ_rgba()
        assert occt_c2.GetRGB().Red() == 1
        assert occt_c2.Alpha() == 1

        c3 = cq.Color(1, 0, 0, 0.5)
        occt_c3 = c3.to_occ_rgba()
        assert occt_c3.GetRGB().Red() == 1
        assert occt_c3.Alpha() == 0.5

        c4 = cq.Color()

        with pytest.raises(ValueError):
            cq.Color("?????")

        with pytest.raises(ValueError):
            cq.Color(1, 2, 3, 4, 5)

    def test_invalid_kwargs(self):
        with pytest.raises(TypeError):
            Color(red=0.1, green=0.2, blue=0.3, alpha=0.4, unknown_kwarg=1)

    def test_too_many_args(self):
        with pytest.raises(ValueError):
            Color(0.1, 0.2, 0.3, 0.4, 0.5)


class TestCommonMaterial:
    @pytest.fixture
    def default_colors(self):
        return {
            "ambient": Color(0.1, 0.1, 0.1),
            "diffuse": Color(0.2, 0.2, 0.2),
            "specular": Color(0.3, 0.3, 0.3),
        }

    def test_valid_construction(self, default_colors):
        material = SimpleMaterial(
            ambient_color=default_colors["ambient"],
            diffuse_color=default_colors["diffuse"],
            specular_color=default_colors["specular"],
            shininess=0.5,
            transparency=0.2,
        )
        assert material.shininess == 0.5
        assert material.transparency == 0.2

    def test_invalid_shininess(self, default_colors):
        with pytest.raises(ValueError):
            SimpleMaterial(
                ambient_color=default_colors["ambient"],
                diffuse_color=default_colors["diffuse"],
                specular_color=default_colors["specular"],
                shininess=1.5,  # Invalid: > 1.0
                transparency=0.2,
            )

    def test_invalid_transparency(self, default_colors):
        with pytest.raises(ValueError):
            SimpleMaterial(
                ambient_color=default_colors["ambient"],
                diffuse_color=default_colors["diffuse"],
                specular_color=default_colors["specular"],
                shininess=0.5,
                transparency=-0.1,  # Invalid: < 0.0
            )

    def test_equality(self, default_colors):
        mat1 = SimpleMaterial(
            ambient_color=default_colors["ambient"],
            diffuse_color=default_colors["diffuse"],
            specular_color=default_colors["specular"],
            shininess=0.5,
            transparency=0.2,
        )
        mat2 = SimpleMaterial(
            ambient_color=default_colors["ambient"],
            diffuse_color=default_colors["diffuse"],
            specular_color=default_colors["specular"],
            shininess=0.5,
            transparency=0.2,
        )
        assert mat1 == mat2
        assert mat1 != "not a material"

    def test_hash(self, default_colors):
        mat1 = SimpleMaterial(
            ambient_color=default_colors["ambient"],
            diffuse_color=default_colors["diffuse"],
            specular_color=default_colors["specular"],
            shininess=0.5,
            transparency=0.2,
        )
        mat2 = SimpleMaterial(
            ambient_color=default_colors["ambient"],
            diffuse_color=default_colors["diffuse"],
            specular_color=default_colors["specular"],
            shininess=0.5,
            transparency=0.2,
        )
        mat3 = SimpleMaterial(
            ambient_color=default_colors["ambient"],
            diffuse_color=default_colors["diffuse"],
            specular_color=default_colors["specular"],
            shininess=0.6,  # Different shininess
            transparency=0.2,
        )
        assert hash(mat1) == hash(mat2)
        assert hash(mat1) != hash(mat3)


class TestPbrMaterial:
    def test_valid_construction(self):
        material = PbrMaterial(
            base_color=Color(0.1, 0.2, 0.3),
            metallic=0.5,
            roughness=0.6,
            refraction_index=1.5,
        )
        assert material.metallic == 0.5
        assert material.roughness == 0.6
        assert material.refraction_index == 1.5

    def test_invalid_metallic(self):
        with pytest.raises(ValueError):
            PbrMaterial(
                base_color=Color(0.1, 0.2, 0.3),
                metallic=1.5,  # Invalid: > 1.0
                roughness=0.6,
                refraction_index=1.5,
            )

    def test_invalid_roughness(self):
        with pytest.raises(ValueError):
            PbrMaterial(
                base_color=Color(0.1, 0.2, 0.3),
                metallic=0.5,
                roughness=-0.1,  # Invalid: < 0.0
                refraction_index=1.5,
            )

    def test_invalid_refraction_index(self):
        with pytest.raises(ValueError):
            PbrMaterial(
                base_color=Color(0.1, 0.2, 0.3),
                metallic=0.5,
                roughness=0.6,
                refraction_index=3.5,  # Invalid: > 3.0
            )

    def test_equality(self):
        mat1 = PbrMaterial(
            base_color=Color(0.1, 0.2, 0.3),
            metallic=0.5,
            roughness=0.6,
            refraction_index=1.5,
        )
        mat2 = PbrMaterial(
            base_color=Color(0.1, 0.2, 0.3),
            metallic=0.5,
            roughness=0.6,
            refraction_index=1.5,
        )
        assert mat1 == mat2
        assert mat1 != "not a material"

    def test_hash(self):
        mat1 = PbrMaterial(
            base_color=Color(0.1, 0.2, 0.3),
            metallic=0.5,
            roughness=0.6,
            refraction_index=1.5,
        )
        mat2 = PbrMaterial(
            base_color=Color(0.1, 0.2, 0.3),
            metallic=0.5,
            roughness=0.6,
            refraction_index=1.5,
        )
        mat3 = PbrMaterial(
            base_color=Color(0.1, 0.2, 0.3),
            metallic=0.5,
            roughness=0.7,  # Different roughness
            refraction_index=1.5,
        )
        assert hash(mat1) == hash(mat2)
        assert hash(mat1) != hash(mat3)


class TestMaterial:
    def test_color_only(self):
        material = Material(
            name="test",
            description="test material",
            density=1000.0,
            color=Color(0.1, 0.2, 0.3),
        )
        assert material.name == "test"
        assert material.description == "test material"
        assert material.density == 1000.0
        assert material.color is not None
        assert material.simple is None
        assert material.pbr is None

    def test_common_only(self):
        material = Material(
            name="test",
            description="test material",
            density=1000.0,
            simple=SimpleMaterial(
                ambient_color=Color(0.1, 0.1, 0.1),
                diffuse_color=Color(0.2, 0.2, 0.2),
                specular_color=Color(0.3, 0.3, 0.3),
                shininess=0.5,
                transparency=0.2,
            ),
        )
        assert material.color is None
        assert material.simple is not None
        assert material.pbr is None

    def test_pbr_only(self):
        material = Material(
            name="test",
            description="test material",
            density=1000.0,
            pbr=PbrMaterial(
                base_color=Color(0.1, 0.2, 0.3),
                metallic=0.5,
                roughness=0.6,
                refraction_index=1.5,
            ),
        )
        assert material.color is None
        assert material.simple is None
        assert material.pbr is not None

    def test_no_representation(self):
        with pytest.raises(ValueError):
            Material(
                name="test", description="test material", density=1000.0,
            )

    def test_equality(self):
        mat1 = Material(
            name="test",
            description="test material",
            density=1000.0,
            color=Color(0.1, 0.2, 0.3),
        )
        mat2 = Material(
            name="test",
            description="test material",
            density=1000.0,
            color=Color(0.1, 0.2, 0.3),
        )
        assert mat1 == mat2
        assert mat1 != "not a material"

    def test_hash(self):
        mat1 = Material(
            name="test",
            description="test material",
            density=1000.0,
            color=Color(0.1, 0.2, 0.3),
        )
        mat2 = Material(
            name="test",
            description="test material",
            density=1000.0,
            color=Color(0.1, 0.2, 0.3),
        )
        mat3 = Material(
            name="test",
            description="test material",
            density=1000.0,
            color=Color(0.2, 0.2, 0.3),  # Different color
        )
        assert hash(mat1) == hash(mat2)
        assert hash(mat1) != hash(mat3)

        # Test hash with different material types
        mat4 = Material(
            name="test",
            description="test material",
            density=1000.0,
            simple=SimpleMaterial(
                ambient_color=Color(0.1, 0.1, 0.1),
                diffuse_color=Color(0.2, 0.2, 0.2),
                specular_color=Color(0.3, 0.3, 0.3),
                shininess=0.5,
                transparency=0.2,
            ),
        )
        mat5 = Material(
            name="test",
            description="test material",
            density=1000.0,
            pbr=PbrMaterial(
                base_color=Color(0.1, 0.2, 0.3),
                metallic=0.5,
                roughness=0.6,
                refraction_index=1.5,
            ),
        )
        assert hash(mat1) != hash(mat4)
        assert hash(mat4) != hash(mat5)


@pytest.fixture
def material_assy(tmp_path_factory):
    """Create an assembly with various materials for testing exports."""

    # Create a box with a simple color
    red_box = cq.Workplane().box(10, 10, 10)

    # Create a cylinder with common material
    gold_cylinder = cq.Workplane().cylinder(5, 20)

    # Create a sphere with PBR material
    chrome_sphere = cq.Workplane().sphere(8)

    # Create the assembly
    assy = cq.Assembly(name="material_test")

    # Add red box with simple color - using simple color representation
    assy.add(
        red_box,
        name="red_box",
        material=Material(
            name="Red",
            description="Simple red material",
            density=1000.0,
            color=Color(1, 0, 0, 1),  # Pure red
        ),
    )

    # Add gold cylinder with common material
    assy.add(
        gold_cylinder,
        name="gold_cylinder",
        loc=cq.Location((40, 0, 0)),
        material=Material(
            name="Gold",
            description="Metallic gold material",
            density=19320.0,  # Actual density of gold in kg/m³
            simple=SimpleMaterial(
                ambient_color=Color(0.24, 0.2, 0.07),
                diffuse_color=Color(0.75, 0.6, 0.22),
                specular_color=Color(0.63, 0.56, 0.37),
                shininess=0.8,
                transparency=0.0,
            ),
        ),
    )

    # Add chrome sphere with PBR material
    assy.add(
        chrome_sphere,
        name="chrome_sphere",
        loc=cq.Location((80, 0, 0)),
        material=Material(
            name="Chrome",
            description="Polished chrome material",
            density=7190.0,  # Density of chrome in kg/m³
            pbr=PbrMaterial(
                base_color=Color(0.8, 0.8, 0.8),
                metallic=1.0,
                roughness=0.1,
                refraction_index=2.4,
            ),
        ),
    )

    return assy


def test_material_gltf_export(material_assy):
    """Test that materials are correctly exported to glTF."""

    # Export to glTF in current directory
    gltf_path = "material_test.gltf"

    # Export to glTF
    material_assy.export(gltf_path)

    # Verify file exists
    assert os.path.exists(gltf_path)

    # Read and verify the glTF content
    with open(gltf_path, "r") as f:
        content = f.read()
        # Check for material properties
        assert '"baseColorFactor":[1.0,0.0,0.0,1.0]' in content  # Red color
        assert '"metallicFactor":1.0' in content  # Chrome metallic
        assert '"roughnessFactor":0.1' in content  # Chrome roughness

        # Current glTF exporter does not support material names
        # assert '"name":"Chrome"' in content  # Material name
        # assert '"name":"Red"' in content  # Material name


def test_material_step_export(material_assy):
    """Test that materials are correctly exported to STEP."""

    # Export to STEP in current directory
    step_path = "material_test.step"

    # Export to STEP
    material_assy.export(step_path)

    # Verify file exists
    assert os.path.exists(step_path)

    # Read the STEP file and verify colors
    doc = read_step(step_path)
    nodes = get_doc_nodes(doc, True)

    # Find and verify the red box
    red_box = [n for n in nodes if "red_box" in n["name"]][0]
    assert approx_equal_tuples(red_box["color"], (1.0, 0.0, 0.0, 1.0))

    # Find and verify the gold cylinder - should use diffuse color from common material
    gold_cylinder = [n for n in nodes if "gold_cylinder" in n["name"]][0]
    assert approx_equal_tuples(gold_cylinder["color"], (0.75, 0.6, 0.22, 1.0))

    # Find and verify the chrome sphere - should use base color from PBR
    chrome_sphere = [n for n in nodes if "chrome_sphere" in n["name"]][0]
    assert approx_equal_tuples(chrome_sphere["color"], (0.8, 0.8, 0.8, 1.0))


def test_material_step_meta_export(material_assy):
    """Test that materials are correctly exported to STEP with metadata."""

    # Export to STEP in current directory
    step_path = "material_test_meta.step"

    # Export to STEP with metadata
    exportStepMeta(material_assy, step_path)

    # Verify file exists
    assert os.path.exists(step_path)

    # Read the contents to verify material metadata was written
    with open(step_path, "r") as f:
        content = f.read()
        # Check for material definitions
        assert "material name" in content
        assert "COLOUR_RGB" in content
        # Check for specific material names
        assert "Red" in content
        assert "Gold" in content
        assert "Chrome" in content
        # Check for material properties
        assert re.search(r"1\.932[eE]\+04", content)  # Gold density
        assert re.search(r"7\.19[eE]\+03", content)  # Chrome density


def test_material_json_export(material_assy):
    """Test that materials are correctly exported to JSON."""

    # Get JSON data
    json_data = toJSON(material_assy)

    # Verify we have the expected number of objects (3 parts)
    assert len(json_data) == 3

    # Save to file for examination
    with open("material_test.json", "w") as f:
        json.dump(json_data, f)


def test_material_vtkjs_export(material_assy):
    """Test that materials are correctly exported to VTKJS using export()."""

    # Export to VTKJS in current directory
    vtk_path = "material_test.vtkjs"

    # Export using regular export
    material_assy.export(vtk_path)
    assert os.path.exists(vtk_path + ".zip")

    # TODO: Add verification of VTK content once we have a parser
    # This would require implementing a VTK file parser or using external tools
    # For now we just verify the export succeeds


def test_material_vtkjs_assy_export(material_assy):
    """Test that materials are correctly exported to VTKJS using toVTKAssy()."""

    # Export to VTKJS in current directory
    vtk_path = "material_test_assy.vtkjs"

    # Create render window from assembly
    renderWindow = _vtkRenderWindow(material_assy)

    # Export using temporary directory like in assembly.py
    with TemporaryDirectory() as tmpdir:
        exporter = vtkJSONSceneExporter()
        exporter.SetFileName(tmpdir)
        exporter.SetRenderWindow(renderWindow)
        exporter.Write()
        make_archive(vtk_path, "zip", tmpdir)

    # Verify zip file exists
    assert os.path.exists(vtk_path + ".zip")

    # Also verify using toVTKAssy
    vtk_assy = toVTKAssy(material_assy)
    assert vtk_assy is not None

    # TODO: Add verification of VTK content once we have a parser
    # This would require implementing a VTK file parser or using external tools
    # For now we just verify the export succeeds


def test_material_vrml_export(material_assy):
    """Test that materials are correctly exported to VRML."""

    # Export to VRML in current directory
    vrml_path = "material_test.vrml"

    # Export to VRML
    material_assy.export(vrml_path)

    # Verify file exists
    assert os.path.exists(vrml_path)

    # Read and verify the VRML content
    with open(vrml_path, "r") as f:
        content = f.read()

        # VRML should contain material definitions
        assert "material Material {" in content

        # VRML uses ambient, diffuse, specular, emissive, shininess and transparency
        # Each shape should have a material definition
        material_blocks = content.count("material Material {")
        # We expect multiple material blocks since each shape has one for faces, lines and points
        assert material_blocks >= 3  # At least one set per shape (we have 3 shapes)

        # Check for material properties
        assert "ambientIntensity" in content
        assert "diffuseColor" in content
        assert "specularColor" in content
        assert "shininess" in content
        assert "transparency" in content
