"""
    Copyright (C) 2011-2015  Parametric Products Intellectual Holdings, LLC

    This file is part of CadQuery.

    CadQuery is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    CadQuery is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; If not, see <http://www.gnu.org/licenses/>
"""
import os
import sys


def _fc_path():
    """Find FreeCAD"""
    # Look for FREECAD_LIB env variable
    _PATH = os.environ.get('FREECAD_LIB', '')
    if _PATH and os.path.exists(_PATH):
        return _PATH

    if sys.platform.startswith('linux'):
        # Make some dangerous assumptions...
        for _PATH in [
                os.path.join(os.path.expanduser("~"), "lib/freecad/lib"),
                "/usr/local/lib/freecad/lib",
                "/usr/lib/freecad/lib",
                "/opt/freecad/lib/",
                "/usr/bin/freecad/lib",
                "/usr/lib/freecad",
                "/usr/lib64/freecad/lib",
                ]:
            if os.path.exists(_PATH):
                return _PATH

    elif sys.platform.startswith('win'):
        # Try all the usual suspects
        for _PATH in [
                "c:/Program Files/FreeCAD0.12/bin",
                "c:/Program Files/FreeCAD0.13/bin",
                "c:/Program Files/FreeCAD0.14/bin",
                "c:/Program Files/FreeCAD0.15/bin",
                "c:/Program Files/FreeCAD0.16/bin",
                "c:/Program Files/FreeCAD0.17/bin",
                "c:/Program Files (x86)/FreeCAD0.12/bin",
                "c:/Program Files (x86)/FreeCAD0.13/bin",
                "c:/Program Files (x86)/FreeCAD0.14/bin",
                "c:/Program Files (x86)/FreeCAD0.15/bin",
                "c:/Program Files (x86)/FreeCAD0.16/bin",
                "c:/Program Files (x86)/FreeCAD0.17/bin",
                "c:/apps/FreeCAD0.12/bin",
                "c:/apps/FreeCAD0.13/bin",
                "c:/apps/FreeCAD0.14/bin",
                "c:/apps/FreeCAD0.15/bin",
                "c:/apps/FreeCAD0.16/bin",
                "c:/apps/FreeCAD0.17/bin",
                "c:/Program Files/FreeCAD 0.12/bin",
                "c:/Program Files/FreeCAD 0.13/bin",
                "c:/Program Files/FreeCAD 0.14/bin",
                "c:/Program Files/FreeCAD 0.15/bin",
                "c:/Program Files/FreeCAD 0.16/bin",
                "c:/Program Files/FreeCAD 0.17/bin",
                "c:/Program Files (x86)/FreeCAD 0.12/bin",
                "c:/Program Files (x86)/FreeCAD 0.13/bin",
                "c:/Program Files (x86)/FreeCAD 0.14/bin",
                "c:/Program Files (x86)/FreeCAD 0.15/bin",
                "c:/Program Files (x86)/FreeCAD 0.16/bin",
                "c:/Program Files (x86)/FreeCAD 0.17/bin",
                "c:/apps/FreeCAD 0.12/bin",
                "c:/apps/FreeCAD 0.13/bin",
                "c:/apps/FreeCAD 0.14/bin",
                "c:/apps/FreeCAD 0.15/bin",
                "c:/apps/FreeCAD 0.16/bin",
                "c:/apps/FreeCAD 0.17/bin",
                ]:
            if os.path.exists(_PATH):
                return _PATH

    elif sys.platform.startswith('darwin'):
        # Assume we're dealing with a Mac
        for _PATH in [
                "/Applications/FreeCAD.app/Contents/lib",
                os.path.join(os.path.expanduser("~"),
                             "Library/Application Support/FreeCAD/lib"),
                ]:
            if os.path.exists(_PATH):
                return _PATH

    raise ImportError('cadquery was unable to determine freecad library path')


# Make sure that the correct FreeCAD path shows up in Python's system path
try:
    import FreeCAD
except ImportError:
    path = _fc_path()
    sys.path.insert(0, path)
    import FreeCAD
