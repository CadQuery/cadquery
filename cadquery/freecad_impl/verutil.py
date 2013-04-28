"""
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

    An exporter should provide functionality to accept a shape, and return
    a string containing the model content.
"""

import re
from importlib import import_module
import os
import sys

MEMO_VERSION = None
SUBMODULES = None
_PATH = None

def _figure_out_version(freecadversion):
    """Break this out for testability."""
    return tuple(
            ((int(re.sub("([0-9]*).*", "\\1", part) or 0))
                for part in freecadversion[:3]))


def _fc_path():
    """Find FreeCAD"""
    global _PATH
    if _PATH:
        return _PATH
    if sys.platform.startswith('linux'):
        #Make some dangerous assumptions...
        for _PATH in [
                os.path.join(os.path.expanduser("~"), "lib/freecad/lib"),
                "/usr/local/lib/freecad/lib",
                "/usr/lib/freecad/lib",
                ]:
            if os.path.exists(_PATH):
                return _PATH

    elif sys.platform.startswith('win'):
        for _PATH in [
                "c:/apps/FreeCAD0.12/bin",
                "c:/apps/FreeCAD0.13/bin",
                ]:
            if os.path.exists(_PATH):
                return _PATH

def freecad_version():
    """Determine the freecad version and return it as a simple
    comparable tuple"""
    #If we cannot find freecad, we append it to the path if possible
    _pthtmp = _fc_path()
    if not _pthtmp in sys.path:
        sys.path.append(_pthtmp)
    import FreeCAD
    global MEMO_VERSION
    if not MEMO_VERSION:
        MEMO_VERSION = _figure_out_version(FreeCAD.Version())
    return MEMO_VERSION

def _find_submodules():
    """Find the list of allowable submodules in fc13"""
    global SUBMODULES
    searchpath = _fc_path()
    if not SUBMODULES:
        SUBMODULES = [
                re.sub("(.*)\\.(py|so)","\\1", filename)
                for filename in os.listdir(searchpath)
                if (
                    filename.endswith(".so") or
                    filename.endswith(".py") or
                    filename.endswith(".dll") )] #Yes, complex. Sorry.
    return SUBMODULES


def fc_import(modulename):
    """Intelligent import of freecad components.
    If we are in 0.12, we can import FreeCAD.Drawing
    If we are in 0.13, we need to set sys.path and import Drawing as toplevel.
    This may or may not be a FreeCAD bug though.
    This is ludicrously complex and feels awful. Kinda like a lot of OCC.
    """
    #Note that this also sets the path as a side effect.

    _fcver = freecad_version()

    if _fcver >= (0, 13):
        if modulename in _find_submodules():
            return import_module(modulename)
        elif re.sub("^FreeCAD\\.", "", modulename) in _find_submodules():
            return import_module(re.sub("^FreeCAD\\.", "", modulename))
        else:
            raise ImportError, "Module %s not found/allowed in %s" % (
                    modulename, _PATH)
    elif _fcver >= (0, 12):
        return import_module(modulename)
    else:
        raise RuntimeError, "Invalid freecad version: %s" % \
                str(".".join(_fcver))

__ALL__ = ['fc_import', 'freecad_version']
