from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Tuple, TypeAlias, overload

if TYPE_CHECKING:
    from OCP.Quantity import Quantity_Color, Quantity_ColorRGBA
    from OCP.XCAFDoc import XCAFDoc_Material, XCAFDoc_VisMaterial
    from vtkmodules.vtkRenderingCore import vtkActor


RGB: TypeAlias = Tuple[float, float, float]
RGBA: TypeAlias = Tuple[float, float, float, float]


@dataclass(frozen=True)
class Color:
    """
    Simple color representation with optional alpha channel.
    All values are in range [0.0, 1.0].
    """

    red: float
    green: float
    blue: float
    alpha: float = 1.0

    @overload
    def __init__(self):
        """
        Construct a Color with default value (white).
        """
        ...

    @overload
    def __init__(self, name: str):
        """
        Construct a Color from a name.

        :param name: name of the color, e.g. green
        """
        ...

    @overload
    def __init__(self, red: float, green: float, blue: float, alpha: float = 1.0):
        """
        Construct a Color from RGB(A) values.

        :param red: red value, 0-1
        :param green: green value, 0-1
        :param blue: blue value, 0-1
        :param alpha: alpha value, 0-1 (default: 1.0)
        """
        ...

    def __init__(self, *args, **kwargs):
        # Check for unknown kwargs
        valid_kwargs = {"red", "green", "blue", "alpha", "name"}
        unknown_kwargs = set(kwargs.keys()) - valid_kwargs
        if unknown_kwargs:
            raise TypeError(f"Got unexpected keyword arguments: {unknown_kwargs}")

        number_of_args = len(args) + len(kwargs)
        if number_of_args == 0:
            # Handle no-args case (default yellow)
            r, g, b, a = 1.0, 1.0, 0.0, 1.0
        elif (number_of_args == 1 and isinstance(args[0], str)) or "name" in kwargs:
            from OCP.Quantity import Quantity_ColorRGBA
            from vtkmodules.vtkCommonColor import vtkNamedColors

            color_name = args[0] if number_of_args == 1 else kwargs["name"]

            # Try to get color from OCCT first, fall back to VTK if not found
            try:
                # Get color from OCCT
                occ_rgba = Quantity_ColorRGBA()
                exists = Quantity_ColorRGBA.ColorFromName_s(color_name, occ_rgba)
                if not exists:
                    raise ValueError(f"Unknown color name: {color_name}")
                occ_rgb = occ_rgba.GetRGB()
                r, g, b, a = (
                    occ_rgb.Red(),
                    occ_rgb.Green(),
                    occ_rgb.Blue(),
                    occ_rgba.Alpha(),
                )
            except ValueError:
                # Check if color exists in VTK
                vtk_colors = vtkNamedColors()
                if not vtk_colors.ColorExists(color_name):
                    raise ValueError(f"Unsupported color name: {color_name}")

                # Get color from VTK
                vtk_rgba = vtk_colors.GetColor4d(color_name)
                r = vtk_rgba.GetRed()
                g = vtk_rgba.GetGreen()
                b = vtk_rgba.GetBlue()
                a = vtk_rgba.GetAlpha()

        elif number_of_args <= 4:
            r, g, b, a = args + (4 - len(args)) * (1.0,)

            if "red" in kwargs:
                r = kwargs["red"]
            if "green" in kwargs:
                g = kwargs["green"]
            if "blue" in kwargs:
                b = kwargs["blue"]
            if "alpha" in kwargs:
                a = kwargs["alpha"]

        elif number_of_args > 4:
            raise ValueError("Too many arguments")

        # Validate values
        for name, value in [("red", r), ("green", g), ("blue", b), ("alpha", a)]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} component must be between 0.0 and 1.0")

        # Set all attributes at once
        object.__setattr__(self, "red", r)
        object.__setattr__(self, "green", g)
        object.__setattr__(self, "blue", b)
        object.__setattr__(self, "alpha", a)

    def rgb(self) -> RGB:
        """Get RGB components as tuple."""
        return (self.red, self.green, self.blue)

    def rgba(self) -> RGBA:
        """Get RGBA components as tuple."""
        return (self.red, self.green, self.blue, self.alpha)

    def to_occ_rgb(self) -> "Quantity_Color":
        """Convert Color to an OCCT RGB color object."""
        from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB

        return Quantity_Color(self.red, self.green, self.blue, Quantity_TOC_RGB)

    def to_occ_rgba(self) -> "Quantity_ColorRGBA":
        """Convert Color to an OCCT RGBA color object."""
        from OCP.Quantity import Quantity_ColorRGBA

        return Quantity_ColorRGBA(self.red, self.green, self.blue, self.alpha)

    def __repr__(self) -> str:
        """String representation of the color."""
        return f"Color(r={self.red}, g={self.green}, b={self.blue}, a={self.alpha})"

    def __str__(self) -> str:
        """String representation of the color."""
        return f"({self.red}, {self.green}, {self.blue}, {self.alpha})"


@dataclass(unsafe_hash=True)
class SimpleMaterial:
    """
    Traditional material model matching OpenCascade's XCAFDoc_VisMaterialCommon.
    """

    ambient_color: Color
    diffuse_color: Color
    specular_color: Color
    shininess: float
    transparency: float

    def __post_init__(self):
        """Validate the material properties."""
        # Validate ranges
        if not 0.0 <= self.shininess <= 1.0:
            raise ValueError("Shininess must be between 0.0 and 1.0")
        if not 0.0 <= self.transparency <= 1.0:
            raise ValueError("Transparency must be between 0.0 and 1.0")

    def apply_to_vtk_actor(self, actor: "vtkActor") -> None:
        """Apply common material properties to a VTK actor."""
        prop = actor.GetProperty()
        prop.SetInterpolationToPhong()
        prop.SetAmbientColor(*self.ambient_color.rgb())
        prop.SetDiffuseColor(*self.diffuse_color.rgb())
        prop.SetSpecularColor(*self.specular_color.rgb())
        prop.SetSpecular(self.shininess)
        prop.SetOpacity(1.0 - self.transparency)


@dataclass(unsafe_hash=True)
class PbrMaterial:
    """
    PBR material definition matching OpenCascade's XCAFDoc_VisMaterialPBR.
    
    Note: Emission support will be added in a future version with proper texture support.
    """

    # Base color and texture
    base_color: Color
    metallic: float
    roughness: float
    refraction_index: float

    def __post_init__(self):
        """Validate the material properties."""
        # Validate ranges
        if not 0.0 <= self.metallic <= 1.0:
            raise ValueError("Metallic must be between 0.0 and 1.0")
        if not 0.0 <= self.roughness <= 1.0:
            raise ValueError("Roughness must be between 0.0 and 1.0")
        if not 1.0 <= self.refraction_index <= 3.0:
            raise ValueError("Refraction index must be between 1.0 and 3.0")

    def apply_to_vtk_actor(self, actor: "vtkActor") -> None:
        """Apply PBR material properties to a VTK actor."""
        prop = actor.GetProperty()
        prop.SetInterpolationToPBR()
        prop.SetColor(*self.base_color.rgb())
        prop.SetOpacity(self.base_color.alpha)
        prop.SetMetallic(self.metallic)
        prop.SetRoughness(self.roughness)
        prop.SetBaseIOR(self.refraction_index)


@dataclass(unsafe_hash=True)
class Material:
    """
    Material class that can store multiple representation types simultaneously.
    Different exporters/viewers can use the most appropriate representation.
    """

    name: str
    description: str
    density: float
    density_unit: str = "kg/m³"

    # Material representations
    color: Optional[Color] = None
    simple: Optional[SimpleMaterial] = None
    pbr: Optional[PbrMaterial] = None

    def __post_init__(self):
        """Validate that at least one representation is provided."""
        if not any([self.color, self.simple, self.pbr]):
            raise ValueError("Material must have at least one representation defined")

    def apply_to_vtk_actor(self, actor: "vtkActor") -> None:
        """Apply material properties to a VTK actor."""
        prop = actor.GetProperty()
        prop.SetMaterialName(self.name)

        if self.pbr:
            self.pbr.apply_to_vtk_actor(actor)
        elif self.simple:
            self.simple.apply_to_vtk_actor(actor)
        elif self.color:
            r, g, b, a = self.color.rgba()
            prop.SetColor(r, g, b)
            prop.SetOpacity(a)

    def to_occ_material(self) -> "XCAFDoc_Material":
        """Convert to OCCT material object."""
        from OCP.XCAFDoc import XCAFDoc_Material
        from OCP.TCollection import TCollection_HAsciiString

        occt_material = XCAFDoc_Material()
        occt_material.Set(
            TCollection_HAsciiString(self.name),
            TCollection_HAsciiString(self.description),
            self.density,
            TCollection_HAsciiString(self.density_unit),
            TCollection_HAsciiString("DENSITY"),
        )
        return occt_material

    def to_occ_vis_material(self) -> "XCAFDoc_VisMaterial":
        """Convert to OCCT visualization material object."""
        from OCP.XCAFDoc import (
            XCAFDoc_VisMaterial,
            XCAFDoc_VisMaterialPBR,
            XCAFDoc_VisMaterialCommon,
        )

        vis_mat = XCAFDoc_VisMaterial()

        # Set up PBR material if provided
        if self.pbr:
            pbr_mat = XCAFDoc_VisMaterialPBR()
            pbr_mat.BaseColor = self.pbr.base_color.to_occ_rgba()
            pbr_mat.Metallic = self.pbr.metallic
            pbr_mat.Roughness = self.pbr.roughness
            pbr_mat.RefractionIndex = self.pbr.refraction_index
            vis_mat.SetPbrMaterial(pbr_mat)

        # Set up common material if provided
        if self.simple:
            common_mat = XCAFDoc_VisMaterialCommon()
            common_mat.AmbientColor = self.simple.ambient_color.to_occ_rgb()
            common_mat.DiffuseColor = self.simple.diffuse_color.to_occ_rgb()
            common_mat.SpecularColor = self.simple.specular_color.to_occ_rgb()
            common_mat.Shininess = self.simple.shininess
            common_mat.Transparency = self.simple.transparency
            vis_mat.SetCommonMaterial(common_mat)

        return vis_mat
