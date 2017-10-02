import sys
import logging

#these items point to the freecad implementation
from .freecad_impl.geom import Plane,BoundBox,Vector,Matrix,sortWiresByBuildOrder
from .freecad_impl.shapes import Shape,Vertex,Edge,Face,Wire,Solid,Shell,Compound
from .freecad_impl import exporters
from .freecad_impl import importers

#these items are the common implementation

#the order of these matter
from .selectors import *
from .cq import *


__all__ = [
    'CQ','Workplane','plugins','selectors','Plane','BoundBox','Matrix','Vector','sortWiresByBuildOrder',
    'Shape','Vertex','Edge','Wire','Face','Solid','Shell','Compound','exporters', 'importers',
    'NearestToPointSelector','ParallelDirSelector','DirectionSelector','PerpendicularDirSelector',
    'TypeSelector','DirectionMinMaxSelector','StringSyntaxSelector','Selector','plugins'
]

__version__ = "1.0.0"

import sys
import logging

# --- Initialize logging
# any script can log to FreeCAD console with:
#
#   >>> import cadquery
#   >>> import logging
#   >>> log = logging.getLogger(__name__)
#   >>> log.debug("detailed info, not normally displayed")
#   >>> log.info("some information")
#   some information
#   >>> log.warning("some warning text")  # orange text
#   some warning text
#   >>> log.error("an error message")  # red text
#   an error message
#
# debug logging can be enabled in your script with:
# 
#   >>> import logging
#   >>> logging.getLogger().setLevel(logging.DEBUG)
#   >>> log = logging.getLogger(__name__)
#   >>> log.debug("debug logs will now be displayed")
#   debug logs will now be displayed
#
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# FreeCAD Logging Handler
class FreeCADConsoleHandler(logging.Handler):
    # Custom flag to identify loggers writing to the FreeCAD.Console
    # why?, This same implementation may be coppied to freecad modules, this helps
    # avoid duplicate logging... futureproofing ftw
    freecad_console = True

    def emit(self, record):
        log_text = self.format(record) + "\n"
        if record.levelno >= logging.ERROR:
            FreeCAD.Console.PrintError(log_text)
        elif record.levelno >= logging.WARNING:
            FreeCAD.Console.PrintWarning(log_text)
        else:
            FreeCAD.Console.PrintMessage(log_text)

try:
    import FreeCAD
    FreeCAD.Console  # will raise exception if not available

    if not any(getattr(h, 'freecad_console', False) for h in root_logger.handlers):
        # avoid duplicate logging
        freecad_handler = FreeCADConsoleHandler()
        freecad_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        freecad_handler.setFormatter(formatter)
        root_logger.addHandler(freecad_handler)

except Exception as e:
    # Fall back to STDOUT output (better than nothing)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)
