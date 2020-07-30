from ...cq import Workplane
from ..shapes import Compound, Shape


def toCompound(shape: Workplane) -> Compound:

    return Compound.makeCompound(val for val in shape.vals() if isinstance(val, Shape))
