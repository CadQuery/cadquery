import os

from typing import Union, Literal

UnitLiterals = Literal["MM", "CM", "M", "KM", "INCH", "FT", "MI", "UM", "NM"]
Real = Union[int, float]
PathLike = Union[str, "os.PathLike[str]"]
