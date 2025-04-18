from dataclasses import dataclass
from typing import Optional, Tuple, TypeAlias, overload

RGB: TypeAlias = Tuple[float, float, float]
RGBA: TypeAlias = Tuple[float, float, float, float]


@dataclass
class Color:
    """
    Simple color representation with optional alpha channel.
    All values are in range [0.0, 1.0].
    """

    r: float  # red component
    g: float  # green component
    b: float  # blue component
    a: float = 1.0  # alpha component, defaults to opaque

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
    def __init__(self, r: float, g: float, b: float, a: float = 1.0):
        """
        Construct a Color from RGB(A) values.

        :param r: red value, 0-1
        :param g: green value, 0-1
        :param b: blue value, 0-1
        :param a: alpha value, 0-1 (default: 1.0)
        """
        ...

    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            # Handle no-args case (default yellow)
            self.r = 1.0
            self.g = 1.0
            self.b = 0.0
            self.a = 1.0
        elif len(args) == 1 and isinstance(args[0], str):
            from .occ_impl.assembly import color_from_name

            # Handle color name case
            color = color_from_name(args[0])
            self.r = color.r
            self.g = color.g
            self.b = color.b
            self.a = color.a
        elif len(args) == 3:
            # Handle RGB case
            r, g, b = args
            a = kwargs.get("a", 1.0)
            self.r = r
            self.g = g
            self.b = b
            self.a = a
        elif len(args) == 4:
            # Handle RGBA case
            r, g, b, a = args
            self.r = r
            self.g = g
            self.b = b
            self.a = a
        else:
            raise ValueError(f"Unsupported arguments: {args}, {kwargs}")

        # Validate values
        for name, value in [("r", self.r), ("g", self.g), ("b", self.b), ("a", self.a)]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} component must be between 0.0 and 1.0")

    def rgb(self) -> RGB:
        """Get RGB components as tuple."""
        return (self.r, self.g, self.b)

    def rgba(self) -> RGBA:
        """Get RGBA components as tuple."""
        return (self.r, self.g, self.b, self.a)

    def toTuple(self) -> Tuple[float, float, float, float]:
        """
        Convert Color to RGBA tuple.
        """
        return (self.r, self.g, self.b, self.a)

    def __repr__(self) -> str:
        """String representation of the color."""
        return f"Color(r={self.r}, g={self.g}, b={self.b}, a={self.a})"

    def __str__(self) -> str:
        """String representation of the color."""
        return f"({self.r}, {self.g}, {self.b}, {self.a})"

    def __hash__(self) -> int:
        """Make Color hashable."""
        return hash((self.r, self.g, self.b, self.a))

    def __eq__(self, other: object) -> bool:
        """Compare two Color objects."""
        if not isinstance(other, Color):
            return False
        return (self.r, self.g, self.b, self.a) == (other.r, other.g, other.b, other.a)


@dataclass
class CommonMaterial:
    """
    Traditional material model matching OpenCascade's XCAFDoc_VisMaterialCommon.
    """

    ambient_color: Color
    diffuse_color: Color
    specular_color: Color
    emissive_color: Color
    shininess: float
    transparency: float

    def __post_init__(self):
        """Validate the material properties."""
        # Validate ranges
        if not 0.0 <= self.shininess <= 1.0:
            raise ValueError("Shininess must be between 0.0 and 1.0")
        if not 0.0 <= self.transparency <= 1.0:
            raise ValueError("Transparency must be between 0.0 and 1.0")

    def __hash__(self) -> int:
        """Make CommonMaterial hashable."""
        return hash(
            (
                self.ambient_color,
                self.diffuse_color,
                self.specular_color,
                self.emissive_color,
                self.shininess,
                self.transparency,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Compare two CommonMaterial objects."""
        if not isinstance(other, CommonMaterial):
            return False
        return (
            self.ambient_color == other.ambient_color
            and self.diffuse_color == other.diffuse_color
            and self.specular_color == other.specular_color
            and self.emissive_color == other.emissive_color
            and self.shininess == other.shininess
            and self.transparency == other.transparency
        )


@dataclass
class PbrMaterial:
    """
    PBR material definition matching OpenCascade's XCAFDoc_VisMaterialPBR.
    """

    # Base color and texture
    base_color: Color
    metallic: float
    roughness: float
    refraction_index: float

    # Optional properties
    emissive_factor: Color = Color(0.0, 0.0, 0.0)

    def __post_init__(self):
        """Validate the material properties."""
        # Validate ranges
        if not 0.0 <= self.metallic <= 1.0:
            raise ValueError("Metallic must be between 0.0 and 1.0")
        if not 0.0 <= self.roughness <= 1.0:
            raise ValueError("Roughness must be between 0.0 and 1.0")
        if not 1.0 <= self.refraction_index <= 3.0:
            raise ValueError("Refraction index must be between 1.0 and 3.0")

    def __hash__(self) -> int:
        """Make PbrMaterial hashable."""
        return hash(
            (
                self.base_color,
                self.metallic,
                self.roughness,
                self.refraction_index,
                self.emissive_factor,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Compare two PbrMaterial objects."""
        if not isinstance(other, PbrMaterial):
            return False
        return (
            self.base_color == other.base_color
            and self.metallic == other.metallic
            and self.roughness == other.roughness
            and self.refraction_index == other.refraction_index
            and self.emissive_factor == other.emissive_factor
        )


@dataclass
class Material:
    """
    Material class that can store multiple representation types simultaneously.
    Different exporters/viewers can use the most appropriate representation.
    """

    name: str
    description: str
    density: float  # kg/m³

    # Material representations
    color: Optional[Color] = None
    common: Optional[CommonMaterial] = None
    pbr: Optional[PbrMaterial] = None

    def __post_init__(self):
        """Validate that at least one representation is provided."""
        if not any([self.color, self.common, self.pbr]):
            raise ValueError("Material must have at least one representation defined")

    def __hash__(self) -> int:
        """Make Material hashable."""
        return hash(
            (
                self.name,
                self.description,
                self.density,
                self.color,
                self.common,
                self.pbr,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Compare two Material objects."""
        if not isinstance(other, Material):
            return False
        return (
            self.name == other.name
            and self.description == other.description
            and self.density == other.density
            and self.color == other.color
            and self.common == other.common
            and self.pbr == other.pbr
        )
